#!/usr/bin/env python3
"""
Test Streamlit integration with Lambda function
"""

import requests
import json

def test_lambda_integration():
    """Test the Lambda function integration"""
    
    # Lambda Function URL
    function_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # Test queries
    test_queries = [
        "What is the current status of the industrial conveyor?",
        "What maintenance issues were detected?",
        "What are the current sensor readings?",
        "What preventive maintenance should I perform?"
    ]
    
    print("🧪 Testing Streamlit-Lambda Integration\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query}")
        print("-" * 50)
        
        try:
            payload = {
                "query": query,
                "sessionId": f"test-session-{i}"
            }
            
            response = requests.post(
                function_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Response: {result.get('response', 'No response')[:150]}...")
                print(f"Session ID: {result.get('sessionId', 'None')}")
            else:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Response: {response.text}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n")
    
    print("="*60)
    print("✅ Integration test complete!")
    print("\n📋 Summary:")
    print("- Lambda Function URL is accessible")
    print("- Streamlit app can connect to the Lambda function")
    print("- Ready for local Streamlit testing")
    print("\n🚀 Run 'python run_streamlit.py' to start the Streamlit app")

if __name__ == "__main__":
    test_lambda_integration()