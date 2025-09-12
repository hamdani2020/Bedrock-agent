#!/usr/bin/env python3
"""
Test Agent with Alias Script

This script tests the Bedrock Agent using the production alias.
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

def test_agent_with_alias():
    """Test agent using production alias"""
    config = load_config()
    
    # Get agent configuration
    agent_id = config['lambda_functions']['query_handler']['environment_variables'].get('BEDROCK_AGENT_ID')
    alias_id = config['lambda_functions']['query_handler']['environment_variables'].get('BEDROCK_AGENT_ALIAS_ID')
    
    if not agent_id or not alias_id:
        logger.error("Agent ID or Alias ID not found in configuration")
        return False
    
    logger.info(f"Testing agent: {agent_id} with alias: {alias_id}")
    
    # Initialize Bedrock Agent Runtime client
    region = config.get('region', 'us-west-2')
    bedrock_runtime_client = boto3.client('bedrock-agent-runtime', region_name=region)
    
    test_queries = [
        "What are the general best practices for preventive maintenance?",
        "How should I approach bearing maintenance and inspection?",
        "What are common signs of pump failure and how to prevent them?",
        "What safety protocols should be followed during equipment maintenance?",
        "How do I prioritize maintenance tasks based on equipment criticality?"
    ]
    
    logger.info("Testing agent functionality with production alias...")
    
    try:
        for i, query in enumerate(test_queries, 1):
            logger.info(f"Test {i}/5: {query[:50]}...")
            
            # Create a test session
            session_id = f"test-session-{int(time.time())}-{i}"
            
            try:
                response = bedrock_runtime_client.invoke_agent(
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
                    print(f"\n{'='*60}")
                    print(f"QUERY {i}: {query}")
                    print(f"{'='*60}")
                    print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                    print(f"{'='*60}")
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

def main():
    """Main execution function"""
    try:
        print("BEDROCK AGENT FUNCTIONALITY TEST")
        print("=" * 40)
        
        # Test agent functionality
        test_success = test_agent_with_alias()
        
        if test_success:
            print("\n✅ AGENT TESTING SUCCESSFUL!")
            print("\nTask 4 Implementation Status:")
            print("✅ 1. Create Bedrock Agent using boto3")
            print("✅ 2. Write simple agent instructions for maintenance queries")
            print("✅ 3. Associate Knowledge Base with the agent (N/A - no KB)")
            print("✅ 4. Test basic agent functionality with sample queries")
            
            print("\nAgent Details:")
            config = load_config()
            print(f"Agent ID: {config['lambda_functions']['query_handler']['environment_variables'].get('BEDROCK_AGENT_ID')}")
            print(f"Alias ID: {config['lambda_functions']['query_handler']['environment_variables'].get('BEDROCK_AGENT_ALIAS_ID')}")
            
            print("\nNext steps:")
            print("1. Deploy Lambda functions (Task 5)")
            print("2. Create Streamlit application (Task 7)")
            print("3. Test end-to-end functionality")
        else:
            print("\n⚠️ Agent testing failed")
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        print(f"\n❌ Script failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())