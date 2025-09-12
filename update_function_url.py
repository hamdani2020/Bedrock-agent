#!/usr/bin/env python3
"""
Update Function URL configuration
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

def update_function_url():
    """Update Function URL configuration"""
    config = load_config()
    if not config:
        return None
    
    try:
        lambda_client = boto3.client('lambda', region_name=config['region'])
        
        function_config = config['lambda_functions']['query_handler']
        function_name = function_config['function_name']
        
        print(f"🔄 Updating Function URL configuration for: {function_name}")
        
        # Update Function URL configuration
        cors_config = function_config['function_url']['cors']
        
        response = lambda_client.update_function_url_config(
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
        print(f"✅ Function URL updated: {function_url}")
        
        return function_url
        
    except ClientError as e:
        print(f"❌ Error updating Function URL: {e}")
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
            print(f"   Response: {result.get('response', 'No response')[:300]}...")
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
    print("🔄 Updating Function URL configuration...\n")
    
    function_url = update_function_url()
    
    if function_url:
        test_lambda_function(function_url)
        
        print("\n" + "="*50)
        print("✅ Function URL update complete!")
        print(f"   URL: {function_url}")
    else:
        print("❌ Failed to update Function URL")

if __name__ == "__main__":
    main()