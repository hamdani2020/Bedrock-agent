#!/usr/bin/env python3
"""
Test very specific queries that should definitely hit the knowledge base data.
"""
import requests
import json
import uuid

def test_specific_queries():
    """Test queries that should return specific knowledge base data."""
    
    lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # Very specific queries based on the KB data we found
    specific_queries = [
        "Show me the device report for conveyor_motor_001 from September 11, 2025",
        "What are the RPM and temperature readings for conveyor_motor_001?",
        "What ball bearing faults were detected on September 11, 2025?",
        "Show me the maintenance analytics report for industrial conveyor",
        "What is the risk level for the ball bearing fault detected?",
        "Show me sensor data with timestamps from 2025-09-11",
        "What fault predictions are available for conveyor motor 001?",
        "Show me the latest device reports with vibration and current measurements"
    ]
    
    print("Testing Specific Knowledge Base Queries")
    print("=" * 60)
    
    for i, query in enumerate(specific_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 50)
        
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
                
                print(f"Response ({len(response_text)} chars):")
                print(response_text)
                
                # Check for very specific data points we know exist
                specific_data_points = [
                    "conveyor_motor_001",
                    "2025-09-11",
                    "September 11",
                    "ball bearing fault",
                    "belt slippage", 
                    "117.1 rpm",
                    "118.6 rpm",
                    "42.82 °C",
                    "43.74 °C",
                    "0.65 m/s²",
                    "0.72 m/s²",
                    "484.8 kg",
                    "500.0 kg",
                    "MEDIUM",
                    "CRITICAL",
                    "23:14"
                ]
                
                found_data = [point for point in specific_data_points if point.lower() in response_text.lower()]
                
                if found_data:
                    print(f"\n✅ Found specific data: {', '.join(found_data[:5])}")
                    if len(found_data) > 5:
                        print(f"   ... and {len(found_data) - 5} more data points")
                else:
                    print("\n⚠️  No specific data points found")
                
                # Check for knowledge base retrieval indicators
                kb_indicators = [
                    "based on the data", "according to the report", "the analysis shows",
                    "data indicates", "from the records", "timestamp shows"
                ]
                
                uses_kb = any(indicator.lower() in response_text.lower() for indicator in kb_indicators)
                if uses_kb:
                    print("✓ Response indicates knowledge base usage")
                
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

def test_direct_agent_with_specific_queries():
    """Test the agent directly with specific queries."""
    
    print("\n" + "=" * 60)
    print("Testing Agent Directly with Specific Queries")
    print("=" * 60)
    
    import boto3
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    # Test one very specific query
    query = "Show me the device report for conveyor_motor_001 with timestamp 2025-09-11T23:14:25"
    
    print(f"Query: {query}")
    
    try:
        response = bedrock_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId="specific-test-session",
            inputText=query
        )
        
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    full_response += chunk_text
        
        print(f"\nDirect Agent Response ({len(full_response)} chars):")
        print(full_response)
        
        # Look for the exact data we know exists
        exact_matches = [
            "conveyor_motor_001",
            "2025-09-11T23:14:25",
            "117.1 rpm",
            "484.8 kg",
            "42.82 °C",
            "0.65 m/s²"
        ]
        
        found_exact = [match for match in exact_matches if match in full_response]
        
        if found_exact:
            print(f"\n🎯 Found exact matches: {', '.join(found_exact)}")
        else:
            print("\n❓ No exact matches found - agent may not be retrieving specific records")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_specific_queries()
    test_direct_agent_with_specific_queries()