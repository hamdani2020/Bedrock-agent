#!/usr/bin/env python3
"""
Test the Lambda with the same query that works in console.
"""
import requests
import json
import uuid

def test_specific_query():
    """Test with the exact query that works in console."""
    
    function_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    payload = {
        "query": "Show me the temperature and vibration levels",
        "sessionId": str(uuid.uuid4())
    }
    
    print("🔍 Testing specific query that works in console")
    print(f"Query: {payload['query']}")
    print("-" * 50)
    
    try:
        response = requests.post(function_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            agent_response = result.get('response', '')
            
            print("Lambda Response:")
            print(agent_response)
            print("\n" + "="*50)
            print("Console Response (for comparison):")
            print("The current temperature of the conveyor system is 39.59°C, which is within the acceptable range of 35.4°C to 43.74°C based on historical data. The current vibration level is 0.66 mm/s, which is also within the normal operating range of 0.65 m/s² to 0.77 m/s².")
            
            # Check if responses are similar
            if "39.59°C" in agent_response or "0.66 mm/s" in agent_response:
                print("\n✅ Lambda agent has access to specific data!")
            else:
                print("\n❌ Lambda agent giving generic response - Knowledge Base issue")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_specific_query()