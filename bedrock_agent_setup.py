#!/usr/bin/env python3
"""
Bedrock Agent Setup Script

This script creates and configures a Bedrock Agent for maintenance expert functionality.
It handles:
1. Creating the Bedrock Agent with maintenance-specific instructions
2. Associating the Knowledge Base with the agent
3. Creating and managing agent aliases
4. Testing basic agent functionality

Requirements satisfied: 2.1, 2.2, 2.3, 6.1
"""

import json
import boto3
import time
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError, BotoCoreError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BedrockAgentSetup:
    """Handles Bedrock Agent creation and configuration"""
    
    def __init__(self, config_file: str = "config/aws_config.json"):
        """Initialize with configuration"""
        self.config = self._load_config(config_file)
        self.config_file = config_file
        
        # Initialize AWS clients
        self.region = self.config.get('region', 'us-west-2')
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=self.region)
        self.bedrock_runtime_client = boto3.client('bedrock-agent-runtime', region_name=self.region)
        self.iam_client = boto3.client('iam', region_name=self.region)
        
        # Agent configuration
        self.agent_config = self.config['bedrock']['agent']
        self.kb_config = self.config['bedrock']['knowledge_base']
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def _save_config(self):
        """Save updated configuration back to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def create_agent_service_role(self) -> str:
        """Create IAM service role for Bedrock Agent"""
        role_name = self.config['iam']['bedrock_agent_role']
        
        # Trust policy for Bedrock Agent service
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceAccount": boto3.client('sts').get_caller_identity()['Account']
                        }
                    }
                }
            ]
        }
        
        # Permissions policy for agent operations
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:{self.region}::foundation-model/{self.agent_config['foundation_model']}"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve",
                        "bedrock:RetrieveAndGenerate"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:{self.region}:*:log-group:/aws/bedrock/agents/*"
                }
            ]
        }
        
        try:
            # Check if role already exists
            try:
                role = self.iam_client.get_role(RoleName=role_name)
                logger.info(f"IAM role {role_name} already exists")
                return role['Role']['Arn']
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise
            
            # Create the role
            logger.info(f"Creating IAM role: {role_name}")
            role_response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Service role for Bedrock Agent maintenance expert"
            )
            
            # Attach permissions policy
            policy_name = f"{role_name}-permissions"
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permissions_policy)
            )
            
            # Wait for role to be available
            time.sleep(10)
            
            logger.info(f"IAM role created successfully: {role_response['Role']['Arn']}")
            return role_response['Role']['Arn']
            
        except ClientError as e:
            logger.error(f"Failed to create IAM role: {e}")
            raise
    
    def get_knowledge_base_id(self) -> Optional[str]:
        """Get Knowledge Base ID from existing resources or config"""
        # First check if it's in the config
        kb_id = self.config['lambda_functions']['data_sync']['environment_variables'].get('KNOWLEDGE_BASE_ID')
        if kb_id:
            logger.info(f"Found Knowledge Base ID in config: {kb_id}")
            return kb_id
        
        # Try to find by name
        try:
            kb_name = self.kb_config['name']
            response = self.bedrock_agent_client.list_knowledge_bases()
            
            for kb in response.get('knowledgeBaseSummaries', []):
                if kb['name'] == kb_name:
                    kb_id = kb['knowledgeBaseId']
                    logger.info(f"Found Knowledge Base by name: {kb_id}")
                    
                    # Update config
                    self.config['lambda_functions']['data_sync']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
                    self.config['lambda_functions']['health_check']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
                    self._save_config()
                    
                    return kb_id
            
            logger.warning(f"Knowledge Base '{kb_name}' not found. Please run create_knowledge_base.py first.")
            return None
            
        except ClientError as e:
            logger.error(f"Failed to list Knowledge Bases: {e}")
            return None
    
    def create_agent(self) -> str:
        """Create the Bedrock Agent"""
        agent_name = self.agent_config['name']
        
        # Get service role ARN
        service_role_arn = self.create_agent_service_role()
        
        # Get Knowledge Base ID
        knowledge_base_id = self.get_knowledge_base_id()
        if not knowledge_base_id:
            raise ValueError("Knowledge Base ID not found. Please create Knowledge Base first.")
        
        # Enhanced agent instructions for maintenance expert
        agent_instruction = """You are an expert maintenance engineer with deep knowledge of industrial equipment fault analysis and predictive maintenance. Your role is to:

1. **Analyze Equipment Faults**: Examine sensor data, fault predictions, and historical patterns to identify root causes and failure modes.

2. **Provide Maintenance Recommendations**: Suggest specific, actionable maintenance procedures based on fault analysis, including:
   - Immediate actions for critical faults
   - Preventive maintenance schedules
   - Component replacement recommendations
   - Safety protocols and shutdown procedures

3. **Pattern Recognition**: Identify trends and correlations in equipment behavior, including:
   - Seasonal patterns and operational correlations
   - Early warning indicators
   - Systemic issues affecting multiple components
   - Maintenance effectiveness analysis

4. **Risk Assessment**: Evaluate fault severity and provide risk-based prioritization:
   - Classify faults by criticality and safety impact
   - Estimate time-to-failure based on historical data
   - Recommend inspection intervals and monitoring strategies

5. **Communication Guidelines**:
   - Always cite specific data sources and timestamps
   - Explain your reasoning and methodology
   - Use appropriate industrial maintenance terminology
   - Provide confidence levels for predictions when possible
   - Highlight safety considerations prominently

6. **Data Context**: You have access to historical fault prediction data including:
   - Sensor readings (temperature, vibration, pressure, flow rates)
   - Fault predictions with probability scores
   - Maintenance history and schedules
   - Equipment metadata and criticality levels

When responding to queries:
- Be specific and actionable in your recommendations
- Reference relevant historical data and patterns
- Consider equipment criticality and operational impact
- Emphasize safety when dealing with high-risk scenarios
- Provide both immediate and long-term maintenance strategies"""

        try:
            # Check if agent already exists
            try:
                agents = self.bedrock_agent_client.list_agents()
                for agent in agents.get('agentSummaries', []):
                    if agent['agentName'] == agent_name:
                        logger.info(f"Agent {agent_name} already exists with ID: {agent['agentId']}")
                        return agent['agentId']
            except ClientError:
                pass  # Continue with creation
            
            logger.info(f"Creating Bedrock Agent: {agent_name}")
            
            # Create the agent
            response = self.bedrock_agent_client.create_agent(
                agentName=agent_name,
                description=self.agent_config['description'],
                foundationModel=self.agent_config['foundation_model'],
                instruction=agent_instruction,
                agentResourceRoleArn=service_role_arn,
                idleSessionTTLInSeconds=1800,  # 30 minutes
                tags={
                    'Project': self.config['project_name'],
                    'Purpose': 'MaintenanceExpert',
                    'Environment': 'Development'
                }
            )
            
            agent_id = response['agent']['agentId']
            logger.info(f"Agent created successfully with ID: {agent_id}")
            
            # Associate Knowledge Base with the agent
            logger.info("Associating Knowledge Base with agent...")
            self.bedrock_agent_client.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion='DRAFT',
                knowledgeBaseId=knowledge_base_id,
                description="Historical equipment fault prediction data for maintenance analysis",
                knowledgeBaseState='ENABLED'
            )
            
            logger.info("Knowledge Base associated successfully")
            
            # Update configuration
            self.config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID'] = agent_id
            self.config['lambda_functions']['health_check']['environment_variables']['BEDROCK_AGENT_ID'] = agent_id
            self._save_config()
            
            return agent_id
            
        except ClientError as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    def create_agent_alias(self, agent_id: str) -> str:
        """Create an alias for the agent"""
        try:
            logger.info("Preparing agent for alias creation...")
            
            # First, prepare the agent (this validates the configuration)
            self.bedrock_agent_client.prepare_agent(agentId=agent_id)
            
            # Wait for preparation to complete
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    agent_status = self.bedrock_agent_client.get_agent(agentId=agent_id)
                    status = agent_status['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        logger.info("Agent preparation completed")
                        break
                    elif status in ['FAILED', 'NOT_PREPARED']:
                        logger.error(f"Agent preparation failed with status: {status}")
                        raise RuntimeError(f"Agent preparation failed: {status}")
                    
                    logger.info(f"Agent status: {status}, waiting...")
                    time.sleep(10)
                    wait_time += 10
                    
                except ClientError as e:
                    if 'ValidationException' in str(e):
                        logger.info("Agent still preparing...")
                        time.sleep(10)
                        wait_time += 10
                    else:
                        raise
            
            if wait_time >= max_wait:
                raise TimeoutError("Agent preparation timed out")
            
            # Create alias
            logger.info("Creating agent alias...")
            alias_response = self.bedrock_agent_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName='production',
                description='Production alias for maintenance expert agent',
                tags={
                    'Environment': 'Production',
                    'Purpose': 'MaintenanceExpert'
                }
            )
            
            alias_id = alias_response['agentAlias']['agentAliasId']
            logger.info(f"Agent alias created successfully: {alias_id}")
            
            # Update configuration
            self.config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID'] = alias_id
            self._save_config()
            
            return alias_id
            
        except ClientError as e:
            logger.error(f"Failed to create agent alias: {e}")
            raise
    
    def test_agent_functionality(self, agent_id: str, alias_id: str) -> bool:
        """Test basic agent functionality with sample queries"""
        test_queries = [
            "What types of equipment faults are most common in our historical data?",
            "Can you analyze bearing wear patterns and recommend maintenance intervals?",
            "What sensor readings typically indicate impending pump failures?",
            "Show me fault patterns for high-temperature equipment failures.",
            "What preventive maintenance should be performed on equipment showing vibration anomalies?"
        ]
        
        logger.info("Testing agent functionality with sample queries...")
        
        try:
            for i, query in enumerate(test_queries, 1):
                logger.info(f"Test {i}/5: {query[:50]}...")
                
                # Create a test session
                session_id = f"test-session-{int(time.time())}-{i}"
                
                try:
                    response = self.bedrock_runtime_client.invoke_agent(
                        agentId=agent_id,
                        agentAliasId=alias_id,
                        sessionId=session_id,
                        inputText=query
                    )
                    
                    # Process streaming response
                    response_text = ""
                    for event in response['completion']:
                        if 'chunk' in event:
                            chunk = event['chunk']
                            if 'bytes' in chunk:
                                response_text += chunk['bytes'].decode('utf-8')
                    
                    if response_text.strip():
                        logger.info(f"✅ Test {i} passed - Response received ({len(response_text)} chars)")
                    else:
                        logger.warning(f"⚠️  Test {i} - Empty response")
                        
                except ClientError as e:
                    logger.error(f"❌ Test {i} failed: {e}")
                    return False
                
                # Small delay between tests
                time.sleep(2)
            
            logger.info("🎉 All agent functionality tests completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Agent testing failed: {e}")
            return False
    
    def setup_complete_agent(self) -> Dict[str, str]:
        """Complete agent setup process"""
        logger.info("Starting Bedrock Agent setup...")
        
        try:
            # Step 1: Create the agent
            agent_id = self.create_agent()
            
            # Step 2: Create agent alias
            alias_id = self.create_agent_alias(agent_id)
            
            # Step 3: Test agent functionality
            test_success = self.test_agent_functionality(agent_id, alias_id)
            
            result = {
                'agent_id': agent_id,
                'alias_id': alias_id,
                'test_success': test_success,
                'status': 'success' if test_success else 'partial_success'
            }
            
            logger.info("🎉 Bedrock Agent setup completed successfully!")
            logger.info(f"Agent ID: {agent_id}")
            logger.info(f"Alias ID: {alias_id}")
            logger.info(f"Test Status: {'✅ Passed' if test_success else '⚠️ Partial'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Agent setup failed: {e}")
            raise

def main():
    """Main execution function"""
    try:
        # Initialize setup
        setup = BedrockAgentSetup()
        
        # Run complete setup
        result = setup.setup_complete_agent()
        
        print("\n" + "="*60)
        print("BEDROCK AGENT SETUP SUMMARY")
        print("="*60)
        print(f"Status: {result['status'].upper()}")
        print(f"Agent ID: {result['agent_id']}")
        print(f"Alias ID: {result['alias_id']}")
        print(f"Functionality Tests: {'✅ PASSED' if result['test_success'] else '⚠️ PARTIAL'}")
        print("="*60)
        
        if result['status'] == 'success':
            print("\n✅ Agent is ready for integration with Lambda functions!")
            print("\nNext steps:")
            print("1. Deploy Lambda functions (Task 5)")
            print("2. Create Streamlit application (Task 7)")
            print("3. Test end-to-end functionality")
        else:
            print("\n⚠️ Agent created but some tests failed.")
            print("Please check the logs and test manually if needed.")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())