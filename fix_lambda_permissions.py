#!/usr/bin/env python3
"""
Fix Lambda execution role permissions for Bedrock Agent access.
"""
import boto3
import json
from botocore.exceptions import ClientError

def get_lambda_execution_role(function_name):
    """Get the execution role ARN for a Lambda function."""
    try:
        lambda_client = boto3.client('lambda')
        response = lambda_client.get_function(FunctionName=function_name)
        role_arn = response['Configuration']['Role']
        role_name = role_arn.split('/')[-1]
        return role_name, role_arn
    except Exception as e:
        print(f"❌ Error getting Lambda role: {str(e)}")
        return None, None

def add_bedrock_permissions(role_name):
    """Add Bedrock permissions to Lambda execution role."""
    try:
        iam = boto3.client('iam')
        
        # Policy for Bedrock Agent access
        policy_document = {
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
        }
        
        policy_name = "BedrockAgentAccess"
        
        # Create or update the policy
        try:
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            print(f"✅ Added Bedrock permissions to role: {role_name}")
            return True
        except ClientError as e:
            print(f"❌ Error adding policy: {e.response['Error']['Message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Fix Lambda permissions for Bedrock Agent access."""
    function_name = "bedrock-agent-query-handler"
    
    print("🔧 Fixing Lambda Bedrock Agent Permissions")
    print("=" * 45)
    
    # Get Lambda execution role
    print(f"\n1. Getting execution role for {function_name}...")
    role_name, role_arn = get_lambda_execution_role(function_name)
    
    if not role_name:
        print("❌ Could not find Lambda function or role")
        return
    
    print(f"✅ Found role: {role_name}")
    print(f"   ARN: {role_arn}")
    
    # Add Bedrock permissions
    print(f"\n2. Adding Bedrock permissions to {role_name}...")
    success = add_bedrock_permissions(role_name)
    
    if success:
        print("\n✅ Permissions updated successfully!")
        print("\n📋 Next steps:")
        print("1. Wait 1-2 minutes for permissions to propagate")
        print("2. Test your Lambda function again")
        print("3. The agent should now work properly")
    else:
        print("\n❌ Failed to update permissions")
        print("\n🔧 Manual steps:")
        print("1. Go to AWS IAM Console")
        print(f"2. Find role: {role_name}")
        print("3. Add inline policy with Bedrock permissions")

if __name__ == "__main__":
    main()