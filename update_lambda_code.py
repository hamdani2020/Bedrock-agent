#!/usr/bin/env python3
"""
Update Lambda function code with improved error handling
"""

import boto3
import json
import zipfile
import os
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
    print("📦 Creating updated Lambda deployment package...")
    
    # Create zip file
    zip_path = 'query_handler_updated.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the Lambda function code
        zip_file.write('lambda_functions/query_handler/lambda_function.py', 'lambda_function.py')
    
    print(f"✅ Created deployment package: {zip_path}")
    return zip_path

def update_lambda_function(zip_path):
    """Update Lambda function code"""
    config = load_config()
    if not config:
        return False
    
    try:
        lambda_client = boto3.client('lambda', region_name=config['region'])
        
        function_name = config['lambda_functions']['query_handler']['function_name']
        
        # Read the zip file
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        print(f"🔄 Updating Lambda function code: {function_name}")
        
        # Update function code
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function code updated")
        print(f"   Last Modified: {response.get('LastModified', 'Unknown')}")
        print(f"   Code Size: {response.get('CodeSize', 0)} bytes")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error updating Lambda function: {e}")
        return False

def test_updated_function():
    """Test the updated Lambda function"""
    config = load_config()
    if not config:
        return False
    
    try:
        lambda_client = boto3.client('lambda', region_name=config['region'])
        
        function_name = config['lambda_functions']['query_handler']['function_name']
        
        print(f"\n🧪 Testing updated Lambda function...")
        
        # Test with valid query
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'query': 'What maintenance issues were detected in the industrial conveyor?',
                'sessionId': 'test-session-456'
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        print(f"   Status Code: {response_payload.get('statusCode', 'Unknown')}")
        
        if response_payload.get('statusCode') == 200:
            body = json.loads(response_payload.get('body', '{}'))
            print(f"✅ Valid query test successful!")
            print(f"   Response: {body.get('response', 'No response')[:150]}...")
        else:
            print(f"❌ Valid query test failed")
            print(f"   Response: {response_payload}")
        
        # Test with invalid query (empty)
        print(f"\n🧪 Testing error handling with empty query...")
        
        test_event_empty = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'query': '',
                'sessionId': 'test-session-error'
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event_empty)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 400:
            print(f"✅ Error handling test successful!")
            body = json.loads(response_payload.get('body', '{}'))
            print(f"   Error message: {body.get('message', 'No message')}")
        else:
            print(f"⚠️  Error handling test unexpected result: {response_payload.get('statusCode')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def main():
    """Main function"""
    print("🔄 Updating Lambda function with improved error handling...\n")
    
    # Create deployment package
    zip_path = create_lambda_package()
    
    try:
        # Update Lambda function
        if update_lambda_function(zip_path):
            # Test the updated function
            test_updated_function()
        
        print("\n" + "="*50)
        print("✅ Lambda function update complete!")
        
    finally:
        # Clean up deployment package
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"🧹 Cleaned up: {zip_path}")

if __name__ == "__main__":
    main()