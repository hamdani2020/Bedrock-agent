#!/usr/bin/env python3
"""
Debug script to identify why Lambda is returning generic responses instead of agent responses.
"""
import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_permissions():
    """Test if current credentials can invoke the Bedrock Agent."""
    try:
        # Use the same IDs as your Lambda
        BEDROCK_AGENT_ID = 'GMJGK6RO4S'
        BEDROCK_AGENT_ALIAS_ID = 'RUWFC5DRPQ'
        
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        
        # Test agent invocation
        response = bedrock_agent_runtime.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId='debug-test-session',
            inputText='What is the status of the industrial conveyor?'
        )
        
        # Process response
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    full_response += chunk_text
        
        print("✅ Agent invocation successful!")
        print(f"Response: {full_response[:200]}...")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"❌ Agent invocation failed: {error_code}")
        print(f"Error message: {error_message}")
        
        if error_code == 'AccessDeniedException':
            print("\n🔧 Fix: Add bedrock:InvokeAgent permission to Lambda execution role")
        elif error_code == 'ResourceNotFoundException':
            print("\n🔧 Fix: Check agent ID and alias ID are correct")
        elif error_code == 'ValidationException':
            print("\n🔧 Fix: Check agent is in PREPARED state")
            
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def check_lambda_role_permissions():
    """Check Lambda execution role permissions."""
    try:
        iam = boto3.client('iam')
        sts = boto3.client('sts')
        
        # Get current identity
        identity = sts.get_caller_identity()
        print(f"Current identity: {identity.get('Arn', 'Unknown')}")
        
        # Check if we can list roles (indicates IAM permissions)
        try:
            roles = iam.list_roles(MaxItems=1)
            print("✅ IAM access available")
        except:
            print("⚠️ Limited IAM access - cannot check role permissions directly")
            
    except Exception as e:
        print(f"❌ Error checking permissions: {str(e)}")

def main():
    """Main diagnostic function."""
    print("🔍 Diagnosing Lambda Agent Integration Issue")
    print("=" * 50)
    
    print("\n1. Testing current AWS credentials...")
    check_lambda_role_permissions()
    
    print("\n2. Testing Bedrock Agent invocation...")
    agent_works = test_agent_permissions()
    
    if not agent_works:
        print("\n📋 Required IAM Policy for Lambda Execution Role:")
        print(json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent"
                    ],
                    "Resource": "arn:aws:bedrock:us-west-2:*:agent/GMJGK6RO4S"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve"
                    ],
                    "Resource": "arn:aws:bedrock:us-west-2:*:knowledge-base/*"
                }
            ]
        }, indent=2))
        
        print("\n🔧 Steps to fix:")
        print("1. Go to AWS IAM Console")
        print("2. Find your Lambda execution role")
        print("3. Add the above policy")
        print("4. Redeploy your Lambda function")
    else:
        print("\n✅ Agent works with current credentials!")
        print("The issue might be in Lambda execution role permissions.")

if __name__ == "__main__":
    main()