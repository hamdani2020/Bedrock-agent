#!/usr/bin/env python3
"""
Deploy the query handler Lambda function with Function URL
"""

import boto3
import json
import zipfile
import os
import time
from botocore.exceptions import ClientError

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def create_lambda_package():
    """Create deployment package for Lambda function"""
    print("📦 Creating Lambda deployment package...")
    
    # Create zip file
    zip_path = 'query_handler_deployment.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the Lambda function code
        zip_file.write('lambda_functions/query_handler/lambda_function.py', 'lambda_function.py')
        
        # Add requirements if they exist
        requirements_path = 'lambda_functions/query_handler/requirements.txt'
        if os.path.exists(requirements_path):
            zip_file.write(requirements_path, 'requirements.txt')
    
    print(f"✅ Created deployment package: {zip_path}")
    return zip_path

def create_lambda_execution_role():
    """Create IAM role for Lambda execution"""
    config = load_config()
    if not config:
        return None
    
    try:
        iam = boto3.client('iam')
        
        role_name = config['iam']['lambda_execution_role']
        
        # Check if role already exists
        try:
            response = iam.get_role(RoleName=role_name)
            print(f"✅ IAM role already exists: {role_name}")
            return response['Role']['Arn']
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchEntity':
                raise
        
        print(f"🔧 Creating IAM role: {role_name}")
        
        # Trust policy for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Execution role for Bedrock Agent query handler Lambda'
        )
        
        role_arn = response['Role']['Arn']
        
        # Attach basic Lambda execution policy
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Create and attach Bedrock policy
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent",
                        "bedrock:InvokeModel"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        policy_name = f"{role_name}-bedrock-policy"
        
        try:
            iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(bedrock_policy),
                Description='Policy for Bedrock Agent access'
            )
            
            # Get account ID for policy ARN
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'EntityAlreadyExists':
                print(f"⚠️  Policy creation error: {e}")
        
        print(f"✅ Created IAM role: {role_arn}")
        
        # Wait for role to be available
        time.sleep(10)
        
        return role_arn
        
    except ClientError as e:
        print(f"❌ Error creating IAM role: {e}")
        return None

def deploy_lambda_function(zip_path, role_arn):
    """Deploy Lambda function"""
    config = load_config()
    if not config:
        return None
    
    try:
        lambda_client = boto3.client('lambda', region_name=config['region'])
        
        function_config = config['lambda_functions']['query_handler']
        function_name = function_config['function_name']
        
        # Read the zip file
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        # Check if function already exists
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            print(f"🔄 Updating existing Lambda function: {function_name}")
            
            # Update function code
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            # Update function configuration
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Runtime=function_config['runtime'],
                Handler='lambda_function.lambda_handler',
                Role=role_arn,
                Timeout=function_config['timeout'],
                MemorySize=function_config['memory_size'],
                Environment={
                    'Variables': function_config['environment_variables']
                }
            )
            
            function_arn = response['Configuration']['FunctionArn']
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
            
            print(f"🚀 Creating new Lambda function: {function_name}")
            
            # Create new function
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime=function_config['runtime'],
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='Bedrock Agent query handler',
                Timeout=function_config['timeout'],
                MemorySize=function_config['memory_size'],
                Environment={
                    'Variables': function_config['environment_variables']
                }
            )
            
            function_arn = response['FunctionArn']
        
        print(f"✅ Lambda function deployed: {function_arn}")
        
        # Wait for function to be ready
        print("⏳ Waiting for function to be ready...")
        waiter = lambda_client.get_waiter('function_active')
        waiter.wait(FunctionName=function_name)
        
        return function_arn
        
    except ClientError as e:
        print(f"❌ Error deploying Lambda function: {e}")
        return None

def create_function_url(function_name):
    """Create Function URL for the Lambda function"""
    config = load_config()
    if not config:
        return None
    
    try:
        lambda_client = boto3.client('lambda', region_name=config['region'])
        
        function_config = config['lambda_functions']['query_handler']
        
        # Check if Function URL already exists
        try:
            response = lambda_client.get_function_url_config(FunctionName=function_name)
            function_url = response['FunctionUrl']
            print(f"✅ Function URL already exists: {function_url}")
            return function_url
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
        print(f"🔗 Creating Function URL for: {function_name}")
        
        # Create Function URL
        response = lambda_client.create_function_url_config(
            FunctionName=function_name,
            AuthType=function_config['function_url']['auth_type'],
            Cors=function_config['function_url']['cors']
        )
        
        function_url = response['FunctionUrl']
        print(f"✅ Function URL created: {function_url}")
        
        return function_url
        
    except ClientError as e:
        print(f"❌ Error creating Function URL: {e}")
        return None

def test_lambda_function(function_url):
    """Test the deployed Lambda function"""
    print(f"\n🧪 Testing Lambda function...")
    
    import requests
    
    test_payload = {
        'query': 'What is the current status of the industrial conveyor?',
        'sessionId': 'test-session-123'
    }
    
    try:
        response = requests.post(
            function_url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test successful!")
            print(f"   Response: {result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Test failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Deploying Query Handler Lambda Function...\n")
    
    # Create deployment package
    zip_path = create_lambda_package()
    
    try:
        # Create IAM role
        print("\n" + "="*50)
        role_arn = create_lambda_execution_role()
        
        if not role_arn:
            print("❌ Failed to create IAM role")
            return
        
        # Deploy Lambda function
        print("\n" + "="*50)
        function_arn = deploy_lambda_function(zip_path, role_arn)
        
        if not function_arn:
            print("❌ Failed to deploy Lambda function")
            return
        
        # Create Function URL
        print("\n" + "="*50)
        config = load_config()
        function_name = config['lambda_functions']['query_handler']['function_name']
        function_url = create_function_url(function_name)
        
        if function_url:
            # Test the function
            print("\n" + "="*50)
            test_lambda_function(function_url)
        
        print("\n" + "="*50)
        print("✅ Query Handler Lambda deployment complete!")
        print(f"\n📋 Deployment Summary:")
        print(f"   Function ARN: {function_arn}")
        print(f"   Function URL: {function_url}")
        print(f"   IAM Role: {role_arn}")
        
    finally:
        # Clean up deployment package
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"🧹 Cleaned up: {zip_path}")

if __name__ == "__main__":
    main()