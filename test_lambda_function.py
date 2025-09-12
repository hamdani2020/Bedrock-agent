#!/usr/bin/env python3
"""
Test script for Lambda Function URL to debug Bedrock Agent integration.
"""
import requests
import json
import uuid

def test_lambda_function():
    """Test the Lambda Function URL with a sample query."""
    
    # Your Lambda Function URL
    function_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # Test payload
    payload = {
        "query": "What is the status of the industrial conveyor?",
        "sessionId": str(uuid.uuid4())
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print("🔍 Testing Lambda Function URL")
    print(f"URL: {function_url}")
    print(f"Query: {payload['query']}")
    print(f"Session: {payload['sessionId']}")
    print("-" * 50)
    
    try:
        response = requests.post(
            function_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Response: {result.get('response', 'No response field')}")
            print(f"Session ID: {result.get('sessionId', 'No session ID')}")
        else:
            print("❌ Error Response:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_lambda_function()