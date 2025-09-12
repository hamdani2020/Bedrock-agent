#!/usr/bin/env python3
"""
Direct test of the Lambda Function URL to see what's actually being returned.
"""
import requests
import json
import uuid

def test_lambda_url_direct():
    """Test the Lambda URL directly with different queries."""
    
    lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # Test queries - from generic to specific
    test_queries = [
        "Show me the latest device reports for conveyor systems with timestamps",
        "Show me data for conveyor_motor_001",
        "What are the sensor readings for conveyor_motor_001 from September 11, 2025?",
        "Show me RPM, temperature, and vibration data for conveyor motors",
        "What fault predictions do you have for equipment?",
        "Show me analytics data with timestamps from today",
        "What maintenance recommendations do you have for conveyor systems?",
        "System health check"
    ]
    
    print("Testing Lambda Function URL Directly")
    print("=" * 60)
    print(f"URL: {lambda_url}")
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Testing Query: {query}")
        print("-" * 40)
        
        try:
            # Create payload exactly like Streamlit does
            payload = {
                "query": query,
                "sessionId": str(uuid.uuid4())
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Make the request
            response = requests.post(
                lambda_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"Response Keys: {list(result.keys())}")
                    
                    response_text = result.get("response", "No response")
                    print(f"Response Length: {len(response_text)} characters")
                    print(f"Response Preview: {response_text[:200]}...")
                    
                    if "sessionId" in result:
                        print(f"Session ID: {result['sessionId']}")
                    
                    # Check if this looks like a generic response
                    generic_indicators = [
                        "general", "typically", "usually", "common", 
                        "recommended", "best practices", "in general",
                        "without specific", "I don't have access to"
                    ]
                    
                    is_generic = any(indicator in response_text.lower() for indicator in generic_indicators)
                    print(f"Appears Generic: {'Yes' if is_generic else 'No'}")
                    
                    # Check for specific data indicators
                    specific_indicators = [
                        "conveyor_motor_001", "RPM:", "temperature:", "vibration:",
                        "timestamp:", "fault detected", "sensor reading", "analytics"
                    ]
                    
                    has_specific_data = any(indicator in response_text.lower() for indicator in specific_indicators)
                    print(f"Contains Specific Data: {'Yes' if has_specific_data else 'No'}")
                    
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    print(f"Raw Response: {response.text[:500]}...")
            else:
                print(f"Error Response: {response.text}")
                
        except Exception as e:
            print(f"Request Error: {e}")
        
        print("\n" + "="*60 + "\n")

def test_with_enhanced_queries():
    """Test with more specific queries that should hit the knowledge base."""
    
    lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # More targeted queries based on the data we found
    specific_queries = [
        "Show me the latest data for conveyor_motor_001 with RPM and temperature readings",
        "What are the fault predictions for conveyor motor 001 from September 11, 2025?",
        "Show me analytics data from bedrock-recommendations with timestamps",
        "What sensor readings do you have for equipment with vibration and current measurements?",
        "Show me maintenance reports for conveyor systems with ball bearing fault predictions",
        "What device reports are available for September 11, 2025 with fault analysis?",
        "Show me equipment data with speed_rpm, temperature_celsius, and vibration_mms values",
        "What are the latest inference results for conveyor motor equipment?"
    ]
    
    print("Testing Enhanced Specific Queries")
    print("=" * 60)
    
    for i, query in enumerate(specific_queries, 1):
        print(f"{i}. Query: {query}")
        
        try:
            payload = {
                "query": query,
                "sessionId": str(uuid.uuid4())
            }
            
            response = requests.post(
                lambda_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                print(f"Response ({len(response_text)} chars): {response_text[:150]}...")
                
                # Check for knowledge base retrieval indicators
                kb_indicators = [
                    "based on the data", "according to", "from the records",
                    "the analysis shows", "data indicates", "reports show"
                ]
                
                uses_kb = any(indicator in response_text.lower() for indicator in kb_indicators)
                print(f"Uses Knowledge Base: {'Yes' if uses_kb else 'No'}")
                
            else:
                print(f"Error: {response.status_code}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_lambda_url_direct()
    test_with_enhanced_queries()