#!/usr/bin/env python3
"""
Create Agent Alias Script

This script creates an alias for an existing Bedrock Agent.
"""

import json
import boto3
import time
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_file: str = "config/aws_config.json"):
    """Load configuration from JSON file"""
    with open(config_file, 'r') as f:
        return json.load(f)

def save_config(config, config_file: str = "config/aws_config.json"):
    """Save configuration to JSON file"""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def create_agent_alias():
    """Create an alias for the existing agent"""
    config = load_config()
    
    # Get agent ID from config
    agent_id = config['lambda_functions']['query_handler']['environment_variables'].get('BEDROCK_AGENT_ID')
    if not agent_id:
        logger.error("No agent ID found in configuration")
        return None
    
    logger.info(f"Creating alias for agent: {agent_id}")
    
    # Initialize Bedrock Agent client
    region = config.get('region', 'us-west-2')
    bedrock_agent_client = boto3.client('bedrock-agent', region_name=region)
    
    try:
        # Check agent status first
        agent_status = bedrock_agent_client.get_agent(agentId=agent_id)
        status = agent_status['agent']['agentStatus']
        logger.info(f"Agent status: {status}")
        
        if status == 'CREATING':
            logger.info("Agent is still creating, waiting...")
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(10)
                wait_time += 10
                
                agent_status = bedrock_agent_client.get_agent(agentId=agent_id)
                status = agent_status['agent']['agentStatus']
                logger.info(f"Agent status: {status}")
                
                if status == 'NOT_PREPARED':
                    break
                elif status == 'FAILED':
                    logger.error("Agent creation failed")
                    return None
        
        # Prepare the agent
        logger.info("Preparing agent...")
        bedrock_agent_client.prepare_agent(agentId=agent_id)
        
        # Wait for preparation to complete
        max_wait = 300  # 5 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(10)
            wait_time += 10
            
            try:
                agent_status = bedrock_agent_client.get_agent(agentId=agent_id)
                status = agent_status['agent']['agentStatus']
                logger.info(f"Agent preparation status: {status}")
                
                if status == 'PREPARED':
                    logger.info("Agent preparation completed")
                    break
                elif status == 'FAILED':
                    logger.error("Agent preparation failed")
                    return None
                    
            except ClientError as e:
                if 'ValidationException' in str(e):
                    logger.info("Agent still preparing...")
                else:
                    raise
        
        if wait_time >= max_wait:
            logger.error("Agent preparation timed out")
            return None
        
        # Create alias
        logger.info("Creating agent alias...")
        alias_response = bedrock_agent_client.create_agent_alias(
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
        config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID'] = alias_id
        save_config(config)
        
        return alias_id
        
    except ClientError as e:
        logger.error(f"Failed to create agent alias: {e}")
        return None

def main():
    """Main execution function"""
    try:
        alias_id = create_agent_alias()
        
        if alias_id:
            print(f"\n✅ Agent alias created successfully: {alias_id}")
            print("Configuration updated.")
        else:
            print("\n❌ Failed to create agent alias")
            return 1
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        print(f"\n❌ Script failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())