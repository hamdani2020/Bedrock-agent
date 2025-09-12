#!/usr/bin/env python3
"""
Update Bedrock Agent with S3 Data Function

This script updates the existing Bedrock Agent to include the S3 data retrieval function
as an action group, allowing it to access maintenance data directly from S3.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

def update_agent_with_s3_function():
    """Update the Bedrock Agent to include S3 data retrieval capability"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Initialize clients
    bedrock_agent_client = boto3.client('bedrock-agent', region_name=region)
    sts_client = boto3.client('sts', region_name=region)
    
    account_id = sts_client.get_caller_identity()['Account']
    
    # Get agent ID from config
    agent_id = config['lambda_functions']['query_handler']['environment_variables'].get('BEDROCK_AGENT_ID')
    
    if not agent_id:
        print("❌ No agent ID found in configuration")
        return False
    
    try:
        print(f"🔄 Updating Bedrock Agent: {agent_id}")
        
        # Define the action group for S3 data retrieval
        action_group_name = "MaintenanceDataRetrieval"
        lambda_function_arn = f"arn:aws:lambda:{region}:{account_id}:function:s3-maintenance-data-retrieval"
        
        # API schema for the action group
        api_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "Maintenance Data Retrieval API",
                "version": "1.0.0",
                "description": "API for retrieving maintenance data from S3"
            },
            "paths": {
                "/retrieve-maintenance-data": {
                    "post": {
                        "summary": "Retrieve maintenance data from S3",
                        "description": "Retrieves relevant maintenance data based on query parameters",
                        "operationId": "retrieveMaintenanceData",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "Search query for maintenance data (e.g., 'bearing fault', 'pump failure')"
                                            },
                                            "date_range": {
                                                "type": "integer",
                                                "description": "Number of days to look back for data (default: 7)",
                                                "default": 7
                                            }
                                        },
                                        "required": ["query"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "query": {"type": "string"},
                                                "results_count": {"type": "integer"},
                                                "data": {"type": "array"},
                                                "summary": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Create action group
        try:
            response = bedrock_agent_client.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName=action_group_name,
                description="Retrieve maintenance data from S3 bucket",
                actionGroupExecutor={
                    'lambda': lambda_function_arn
                },
                apiSchema={
                    'payload': json.dumps(api_schema)
                },
                actionGroupState='ENABLED'
            )
            
            action_group_id = response['agentActionGroup']['actionGroupId']
            print(f"✅ Created action group: {action_group_id}")
            
        except ClientError as e:
            if 'ConflictException' in str(e):
                # Action group might already exist, try to update it
                print("⚠️  Action group might already exist, trying to update...")
                
                # List existing action groups
                action_groups = bedrock_agent_client.list_agent_action_groups(
                    agentId=agent_id,
                    agentVersion='DRAFT'
                )
                
                existing_group = None
                for group in action_groups.get('actionGroupSummaries', []):
                    if group['actionGroupName'] == action_group_name:
                        existing_group = group
                        break
                
                if existing_group:
                    # Update existing action group
                    response = bedrock_agent_client.update_agent_action_group(
                        agentId=agent_id,
                        agentVersion='DRAFT',
                        actionGroupId=existing_group['actionGroupId'],
                        actionGroupName=action_group_name,
                        description="Retrieve maintenance data from S3 bucket",
                        actionGroupExecutor={
                            'lambda': lambda_function_arn
                        },
                        apiSchema={
                            'payload': json.dumps(api_schema)
                        },
                        actionGroupState='ENABLED'
                    )
                    print(f"✅ Updated action group: {existing_group['actionGroupId']}")
                else:
                    raise
            else:
                raise
        
        # Update agent instructions to include data retrieval capability
        enhanced_instructions = """You are an expert maintenance engineer with deep knowledge of industrial equipment fault analysis and predictive maintenance. Your role is to:

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

5. **Data Retrieval and Analysis**: You have access to historical maintenance data through the retrieveMaintenanceData function:
   - Use this function to search for specific fault types, equipment issues, or maintenance patterns
   - Analyze retrieved data to provide data-driven recommendations
   - Reference specific data points and timestamps in your responses
   - Combine historical data with general maintenance expertise

6. **Communication Guidelines**:
   - Always cite specific data sources and timestamps when using retrieved data
   - Explain your reasoning and methodology
   - Use appropriate industrial maintenance terminology
   - Provide confidence levels for predictions when possible
   - Highlight safety considerations prominently

When responding to queries:
- First, try to retrieve relevant historical data using the retrieveMaintenanceData function
- Analyze the retrieved data for patterns and insights
- Combine data-driven analysis with general maintenance best practices
- Be specific and actionable in your recommendations
- Reference both historical data and maintenance principles
- Consider equipment criticality and operational impact
- Emphasize safety when dealing with high-risk scenarios
- Provide both immediate and long-term maintenance strategies

Example usage:
- For bearing issues: retrieveMaintenanceData with query "bearing fault" or "bearing vibration"
- For pump problems: retrieveMaintenanceData with query "pump failure" or "pump pressure"
- For temperature issues: retrieveMaintenanceData with query "temperature" or "overheating"
"""
        
        # Update agent with enhanced instructions
        bedrock_agent_client.update_agent(
            agentId=agent_id,
            agentName=config['bedrock']['agent']['name'],
            description=config['bedrock']['agent']['description'],
            instruction=enhanced_instructions,
            foundationModel=config['bedrock']['agent']['foundation_model']
        )
        
        print("✅ Updated agent instructions")
        
        # Prepare the agent
        print("🔄 Preparing agent with new action group...")
        bedrock_agent_client.prepare_agent(agentId=agent_id)
        
        # Wait for preparation
        max_wait = 300  # 5 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                agent_status = bedrock_agent_client.get_agent(agentId=agent_id)
                status = agent_status['agent']['agentStatus']
                
                if status == 'PREPARED':
                    print("✅ Agent preparation completed")
                    break
                elif status == 'FAILED':
                    print("❌ Agent preparation failed")
                    return False
                
                print(f"⏳ Agent status: {status}, waiting...")
                time.sleep(10)
                wait_time += 10
                
            except ClientError as e:
                if 'ValidationException' in str(e):
                    print("⏳ Agent still preparing...")
                    time.sleep(10)
                    wait_time += 10
                else:
                    raise
        
        if wait_time >= max_wait:
            print("⚠️  Agent preparation timed out, but continuing...")
        
        print("🎉 Agent updated successfully with S3 data retrieval capability!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update agent: {e}")
        return False

def main():
    """Main execution function"""
    try:
        success = update_agent_with_s3_function()
        
        if success:
            print(f"\n✅ AGENT UPDATE COMPLETED!")
            print(f"\nThe Bedrock Agent now has access to maintenance data from S3:")
            print(f"- Can retrieve historical fault data")
            print(f"- Can search for specific equipment issues")
            print(f"- Can provide data-driven maintenance recommendations")
            print(f"\nTask 3 Alternative Implementation:")
            print(f"✅ Direct S3 data access (bypassing Knowledge Base)")
            print(f"✅ Lambda function for data retrieval")
            print(f"✅ Agent action group integration")
            print(f"✅ Enhanced agent instructions")
            return 0
        else:
            print(f"\n❌ Agent update failed")
            return 1
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())