#!/usr/bin/env python3
"""
Debug Lambda function's agent invocation to see exactly what's happening.
"""
import boto3
import json
import uuid
import time
from datetime import datetime

def test_direct_agent_invocation():
    """Test invoking the agent directly (same way Lambda should)."""
    
    print("Testing Direct Agent Invocation (Same as Lambda)")
    print("=" * 60)
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    # Test the exact same query that returns generic response in Lambda
    test_queries = [
        "What faults have been detected in the equipment?",
        "Show me data for conveyor_motor_001",
        "What are the sensor readings for conveyor_motor_001 from September 11, 2025?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing Query: {query}")
        print("-" * 40)
        
        session_id = str(uuid.uuid4())
        
        try:
            start_time = time.time()
            
            response = bedrock_runtime.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=ALIAS_ID,
                sessionId=session_id,
                inputText=query
            )
            
            # Process streaming response exactly like Lambda does
            full_response = ""
            chunk_count = 0
            
            for event in response['completion']:
                chunk_count += 1
                
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        chunk_text = chunk['bytes'].decode('utf-8')
                        full_response += chunk_text
                        print(f"   Chunk {chunk_count}: {chunk_text[:100]}...")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"\nFull Response ({len(full_response)} chars, {response_time:.2f}s):")
            print(f"{full_response}")
            
            # Analyze response characteristics
            generic_indicators = [
                "without access to", "general", "typically", "usually", 
                "I don't have access", "I cannot find", "No data available"
            ]
            
            specific_indicators = [
                "conveyor_motor_001", "September 11", "ball bearing fault", 
                "belt slippage", "RPM", "temperature", "vibration"
            ]
            
            is_generic = any(indicator.lower() in full_response.lower() for indicator in generic_indicators)
            has_specific = any(indicator.lower() in full_response.lower() for indicator in specific_indicators)
            
            print(f"\nAnalysis:")
            print(f"  Generic Response: {'Yes' if is_generic else 'No'}")
            print(f"  Contains Specific Data: {'Yes' if has_specific else 'No'}")
            print(f"  Response Time: {response_time:.2f}s")
            print(f"  Chunks Received: {chunk_count}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

def test_lambda_function_locally():
    """Test the Lambda function code locally to see what it's doing."""
    
    print("\n" + "=" * 60)
    print("Testing Lambda Function Code Locally")
    print("=" * 60)
    
    # Import the Lambda function
    import sys
    import os
    sys.path.append('lambda_functions/query_handler')
    
    try:
        from lambda_function import invoke_bedrock_agent, lambda_handler
        
        # Test the invoke_bedrock_agent function directly
        print("\n1. Testing invoke_bedrock_agent function directly:")
        print("-" * 50)
        
        query = "What faults have been detected in the equipment?"
        session_id = str(uuid.uuid4())
        
        print(f"Query: {query}")
        print(f"Session ID: {session_id}")
        
        # Set environment variables like Lambda would have
        os.environ['BEDROCK_AGENT_ID'] = 'GMJGK6RO4S'
        os.environ['BEDROCK_AGENT_ALIAS_ID'] = 'RUWFC5DRPQ'
        
        try:
            response_text = invoke_bedrock_agent(query, session_id)
            print(f"\nResponse from invoke_bedrock_agent:")
            print(f"Length: {len(response_text)} characters")
            print(f"Content: {response_text}")
            
            # Check if this matches what we expect
            if "without access to" in response_text.lower():
                print("\n⚠️  Function is returning generic response!")
            elif "conveyor_motor_001" in response_text.lower():
                print("\n✓ Function is accessing knowledge base data!")
            else:
                print("\n? Response type unclear")
                
        except Exception as e:
            print(f"Error in invoke_bedrock_agent: {e}")
            import traceback
            traceback.print_exc()
        
        # Test the full Lambda handler
        print("\n\n2. Testing full lambda_handler:")
        print("-" * 50)
        
        # Create a mock Lambda event
        mock_event = {
            'httpMethod': 'POST',
            'headers': {
                'content-type': 'application/json',
                'origin': 'https://localhost:8501'
            },
            'body': json.dumps({
                'query': query,
                'sessionId': session_id
            })
        }
        
        # Mock context
        class MockContext:
            def __init__(self):
                self.aws_request_id = str(uuid.uuid4())
                
            def get_remaining_time_in_millis(self):
                return 30000  # 30 seconds
        
        mock_context = MockContext()
        
        try:
            result = lambda_handler(mock_event, mock_context)
            
            print(f"Status Code: {result['statusCode']}")
            print(f"Headers: {result.get('headers', {})}")
            
            if result['statusCode'] == 200:
                body = json.loads(result['body'])
                response_text = body.get('response', '')
                
                print(f"\nLambda Response:")
                print(f"Length: {len(response_text)} characters")
                print(f"Content: {response_text}")
                
                # Compare with direct invocation
                print(f"\nSession ID returned: {body.get('sessionId', 'None')}")
                
            else:
                print(f"Error response: {result['body']}")
                
        except Exception as e:
            print(f"Error in lambda_handler: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"Could not import Lambda function: {e}")
        print("This might indicate an issue with the Lambda deployment")

def compare_environments():
    """Compare environment variables and configurations."""
    
    print("\n" + "=" * 60)
    print("Comparing Environments")
    print("=" * 60)
    
    # Check current environment
    print("Current Environment Variables:")
    bedrock_vars = {k: v for k, v in os.environ.items() if 'BEDROCK' in k or 'AWS' in k}
    for key, value in bedrock_vars.items():
        print(f"  {key}: {value}")
    
    # Check config file
    print("\nConfig File Values:")
    try:
        with open('config/aws_config.json', 'r') as f:
            config = json.load(f)
        
        lambda_config = config['lambda_functions']['query_handler']['environment_variables']
        print(f"  BEDROCK_AGENT_ID: {lambda_config.get('BEDROCK_AGENT_ID')}")
        print(f"  BEDROCK_AGENT_ALIAS_ID: {lambda_config.get('BEDROCK_AGENT_ALIAS_ID')}")
        print(f"  NEW_KNOWLEDGE_BASE_ID: {lambda_config.get('NEW_KNOWLEDGE_BASE_ID')}")
        
    except Exception as e:
        print(f"Error reading config: {e}")
    
    # Check AWS credentials and region
    print(f"\nAWS Configuration:")
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        print(f"  Region: {session.region_name}")
        print(f"  Access Key: {credentials.access_key[:10]}..." if credentials.access_key else "None")
        print(f"  Has Secret Key: {'Yes' if credentials.secret_key else 'No'}")
        print(f"  Has Session Token: {'Yes' if credentials.token else 'No'}")
        
    except Exception as e:
        print(f"Error checking AWS config: {e}")

if __name__ == "__main__":
    test_direct_agent_invocation()
    test_lambda_function_locally()
    compare_environments()