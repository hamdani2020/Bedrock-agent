#!/usr/bin/env python3
"""
Test both the Lambda Function URL and API Gateway endpoints to compare responses.
"""
import requests
import json
import uuid

def test_endpoint(endpoint_url, endpoint_name):
    """Test a specific endpoint with the same queries."""
    
    print(f"\nTesting {endpoint_name}")
    print("=" * 60)
    print(f"URL: {endpoint_url}")
    
    # Test queries that should return specific data
    test_queries = [
        "What faults have been detected in the equipment?",
        "Show me data for conveyor_motor_001",
        "What are the sensor readings for conveyor_motor_001?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 40)
        
        try:
            payload = {
                "query": query,
                "sessionId": str(uuid.uuid4())
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                endpoint_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    response_text = result.get("response", "No response")
                    
                    print(f"Response Length: {len(response_text)} characters")
                    print(f"Response Preview: {response_text[:200]}...")
                    
                    # Check for specific vs generic indicators
                    specific_indicators = [
                        "conveyor_motor_001", "ball bearing fault", "belt slippage",
                        "September 11", "RPM", "temperature", "vibration"
                    ]
                    
                    generic_indicators = [
                        "without access to", "I don't have access", "general", 
                        "typically", "usually", "common faults"
                    ]
                    
                    has_specific = any(indicator.lower() in response_text.lower() for indicator in specific_indicators)
                    is_generic = any(indicator.lower() in response_text.lower() for indicator in generic_indicators)
                    
                    print(f"Contains Specific Data: {'✓ Yes' if has_specific else '✗ No'}")
                    print(f"Generic Response: {'⚠️  Yes' if is_generic else '✓ No'}")
                    
                    # Check for function call errors
                    if "function call" in response_text.lower() or "format is incorrect" in response_text.lower():
                        print("🔧 Contains function call errors")
                    
                except json.JSONDecodeError:
                    print(f"Invalid JSON response: {response.text[:200]}...")
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("⏱️  Request timed out")
        except requests.exceptions.ConnectionError:
            print("🔌 Connection error")
        except Exception as e:
            print(f"❌ Error: {e}")

def compare_endpoints():
    """Compare both endpoints side by side."""
    
    print("Comparing Lambda Function URL vs API Gateway")
    print("=" * 80)
    
    # Lambda Function URL
    lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # API Gateway URL
    api_gateway_url = "https://i9998zjrdh.execute-api.us-west-2.amazonaws.com/prod/query/"
    
    test_endpoint(lambda_url, "Lambda Function URL")
    test_endpoint(api_gateway_url, "API Gateway")
    
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print("If API Gateway returns specific data but Lambda Function URL doesn't,")
    print("then the issue is with the Lambda Function URL configuration or code.")
    print("\nPossible causes:")
    print("1. Different Lambda functions behind each endpoint")
    print("2. Different environment variables")
    print("3. Different IAM permissions")
    print("4. Different agent/alias IDs configured")

def test_streamlit_current_config():
    """Test what endpoint Streamlit is currently using."""
    
    print("\n" + "=" * 80)
    print("STREAMLIT CONFIGURATION CHECK")
    print("=" * 80)
    
    try:
        # Read Streamlit app to see current endpoint
        with open('streamlit_app/app.py', 'r') as f:
            content = f.read()
        
        # Look for the default endpoint
        if 'mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws' in content:
            print("✓ Streamlit is configured to use Lambda Function URL")
            print("  URL: https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/")
        elif 'i9998zjrdh.execute-api.us-west-2.amazonaws.com' in content:
            print("✓ Streamlit is configured to use API Gateway")
            print("  URL: https://i9998zjrdh.execute-api.us-west-2.amazonaws.com/prod/query/")
        else:
            print("? Could not determine Streamlit endpoint configuration")
        
        print("\nRECOMMENDATION:")
        print("If API Gateway works better, update Streamlit to use that endpoint instead.")
        
    except Exception as e:
        print(f"Error reading Streamlit config: {e}")

if __name__ == "__main__":
    compare_endpoints()
    test_streamlit_current_config()