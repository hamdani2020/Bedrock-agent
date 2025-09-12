#!/usr/bin/env python3
"""
Create Function URL for existing Lambda function
"""

import boto3
import json
import requests
from botocore.exceptions import ClientError

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def create_function_url():
    """Create Function URL for the Lambda function"""
    config = load_config()
    if not config:
        return None
    
    try:
        lambda_client = boto3.client('lambda', region_name=config['region'])
        
        function_config = config['lambda_functions']['query_handler']
        function_name = function_config['function_name']
        
        print(f"🔗 Creating Function URL for: {function_name}")
        
        # Check if Function URL already exists
        try:
            response = lambda_client.get_function_url_config(FunctionName=function_name)
            function_url = response['FunctionUrl']
            print(f"✅ Function URL already exists: {function_url}")
            return function_url
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
        # Create Function URL with proper CORS format
        cors_config = function_config['function_url']['cors']
        
        response = lambda_client.create_function_url_config(
            FunctionName=function_name,
            AuthType=function_config['function_url']['auth_type'],
            Cors={
                'AllowCredentials': cors_config['allow_credentials'],
                'AllowHeaders': cors_config['allow_headers'],
                'AllowMethods': cors_config['allow_methods'],
                'AllowOrigins': cors_config['allow_origins'],
                'MaxAge': cors_config['max_age']
            }
        )
        
        function_url = response['FunctionUrl']
        print(f"✅ Function URL created: {function_url}")
        
        return function_url
        
    except ClientError as e:
        print(f"❌ Error creating Function URL: {e}")
        return None

def test_lambda_function(function_url):
    """Test the Lambda function"""
    print(f"\n🧪 Testing Lambda function...")
    
    test_payload = {
        'query': 'What is the current status of the industrial conveyor based on the maintenance data?',
        'sessionId': 'test-session-123'
    }
    
    try:
        print(f"   Sending request to: {function_url}")
        print(f"   Payload: {test_payload}")
        
        response = requests.post(
            function_url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test successful!")
            print(f"   Response: {result.get('response', 'No response')[:200]}...")
            return True
        else:
            print(f"❌ Test failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main function"""
    print("🔗 Creating Function URL for Query Handler Lambda...\n")
    
    function_url = create_function_url()
    
    if function_url:
        test_lambda_function(function_url)
        
        print("\n" + "="*50)
        print("✅ Function URL setup complete!")
        print(f"   URL: {function_url}")
        print("\n📋 You can now use this URL to query the Bedrock Agent from your Streamlit app")
    else:
        print("❌ Failed to create Function URL")

if __name__ == "__main__":
    main()