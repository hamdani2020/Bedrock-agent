#!/usr/bin/env python3
"""
Diagnostic script to test Bedrock Agent invocation exactly as the Lambda function does.
This will help identify differences between console and Lambda function behavior.
"""
import json
import boto3
import logging
import uuid
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agent_invocation():
    """Test agent invocation with the same parameters as Lambda function."""
    
    # Use the same configuration as Lambda
    BEDROCK_AGENT_ID = "GMJGK6RO4S"
    BEDROCK_AGENT_ALIAS_ID = "RUWFC5DRPQ"
    
    # Initialize client
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    # Test query similar to what you mentioned
    test_query = "Show me the latest device reports for conveyor systems with timestamps."
    session_id = str(uuid.uuid4())
    
    print(f"Testing Bedrock Agent invocation:")
    print(f"Agent ID: {BEDROCK_AGENT_ID}")
    print(f"Alias ID: {BEDROCK_AGENT_ALIAS_ID}")
    print(f"Query: {test_query}")
    print(f"Session ID: {session_id}")
    print("-" * 80)
    
    try:
        # First, let's check if the agent and alias exist
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
        
        print("Checking agent status...")
        try:
            agent_response = bedrock_agent.get_agent(agentId=BEDROCK_AGENT_ID)
            print(f"✓ Agent found: {agent_response['agent']['agentName']}")
            print(f"  Status: {agent_response['agent']['agentStatus']}")
            print(f"  Foundation Model: {agent_response['agent']['foundationModel']}")
        except Exception as e:
            print(f"✗ Error getting agent: {e}")
            return
        
        print("\nChecking agent alias...")
        try:
            alias_response = bedrock_agent.get_agent_alias(
                agentId=BEDROCK_AGENT_ID,
                agentAliasId=BEDROCK_AGENT_ALIAS_ID
            )
            print(f"✓ Alias found: {alias_response['agentAlias']['agentAliasName']}")
            print(f"  Status: {alias_response['agentAlias']['agentAliasStatus']}")
            print(f"  Agent Version: {alias_response['agentAlias']['agentVersion']}")
        except Exception as e:
            print(f"✗ Error getting alias: {e}")
            return
        
        print("\nInvoking agent...")
        response = bedrock_agent_runtime.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=test_query
        )
        
        print("✓ Agent invocation successful")
        print("\nProcessing response stream...")
        
        full_response = ""
        chunk_count = 0
        
        for event in response['completion']:
            chunk_count += 1
            print(f"Chunk {chunk_count}: {event.keys()}")
            
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    full_response += chunk_text
                    print(f"  Text: {chunk_text[:100]}...")
            elif 'trace' in event:
                trace = event['trace']
                print(f"  Trace: {trace.get('trace', {}).keys()}")
                
                # Check for knowledge base queries
                if 'orchestrationTrace' in trace.get('trace', {}):
                    orch_trace = trace['trace']['orchestrationTrace']
                    if 'invocationInput' in orch_trace:
                        print(f"    Invocation Input: {orch_trace['invocationInput']}")
                    if 'observation' in orch_trace:
                        obs = orch_trace['observation']
                        if 'knowledgeBaseLookupOutput' in obs:
                            kb_output = obs['knowledgeBaseLookupOutput']
                            print(f"    Knowledge Base Results: {len(kb_output.get('retrievedReferences', []))} references")
                            for ref in kb_output.get('retrievedReferences', [])[:2]:  # Show first 2
                                print(f"      - {ref.get('content', {}).get('text', '')[:100]}...")
        
        print(f"\nFinal Response ({len(full_response)} characters):")
        print("-" * 40)
        print(full_response)
        print("-" * 40)
        
        if not full_response.strip():
            print("⚠️  WARNING: Empty response received!")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"✗ AWS ClientError: {error_code} - {error_message}")
        
        if error_code == 'ValidationException':
            print("  This usually means invalid agent ID or alias ID")
        elif error_code == 'AccessDeniedException':
            print("  This means insufficient permissions")
        elif error_code == 'ResourceNotFoundException':
            print("  This means the agent or alias doesn't exist")
            
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_lambda_simulation():
    """Simulate the exact Lambda function call."""
    print("\n" + "="*80)
    print("SIMULATING LAMBDA FUNCTION CALL")
    print("="*80)
    
    # Simulate the Lambda event
    lambda_event = {
        'body': json.dumps({
            'query': 'Show me the latest device reports for conveyor systems with timestamps.',
            'sessionId': str(uuid.uuid4())
        }),
        'headers': {
            'content-type': 'application/json'
        },
        'httpMethod': 'POST'
    }
    
    # Import and call the Lambda function
    import sys
    import os
    sys.path.append('lambda_functions/query_handler')
    
    # Set environment variables
    os.environ['BEDROCK_AGENT_ID'] = 'GMJGK6RO4S'
    os.environ['BEDROCK_AGENT_ALIAS_ID'] = 'RUWFC5DRPQ'
    
    try:
        from lambda_function import lambda_handler
        
        # Mock context
        class MockContext:
            aws_request_id = str(uuid.uuid4())
            def get_remaining_time_in_millis(self):
                return 30000
        
        context = MockContext()
        
        print("Calling Lambda handler...")
        result = lambda_handler(lambda_event, context)
        
        print(f"Status Code: {result['statusCode']}")
        print(f"Headers: {result['headers']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"Response: {body.get('response', 'No response')}")
        else:
            print(f"Error Body: {result['body']}")
            
    except Exception as e:
        print(f"Error simulating Lambda: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Bedrock Agent Lambda Diagnostic Tool")
    print("="*50)
    
    # Test 1: Direct agent invocation
    test_agent_invocation()
    
    # Test 2: Lambda simulation
    test_lambda_simulation()