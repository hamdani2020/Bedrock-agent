#!/usr/bin/env python3
"""
Test the updated Lambda function to see if it's now working correctly.
"""
import requests
import json
import uuid

def test_updated_lambda_function():
    """Test the updated Lambda function with various queries."""
    
    print("Testing Updated Lambda Function")
    print("=" * 60)
    
    lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # Test queries from generic to specific
    test_queries = [
        "What faults have been detected in the equipment?",
        "Show me data for conveyor_motor_001",
        "What are the sensor readings for conveyor_motor_001 from September 11, 2025?",
        "What ball bearing faults were detected on September 11, 2025?",
        "Show me the maintenance analytics report for industrial conveyor",
        "What is the risk level for detected faults?",
        "Show me device reports with timestamps from 2025-09-11"
    ]
    
    success_count = 0
    
    for i, query in enumerate(test_queries, 1):
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
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                print(f"Response Length: {len(response_text)} characters")
                print(f"Response Preview: {response_text[:300]}...")
                
                # Check for specific data points we know exist in the knowledge base
                specific_data_points = [
                    "conveyor_motor_001",
                    "ball bearing fault",
                    "belt slippage", 
                    "September 11",
                    "2025-09-11",
                    "117.1 rpm",
                    "118.6 rpm",
                    "42.82 °C",
                    "43.74 °C",
                    "0.65 m/s²",
                    "0.72 m/s²",
                    "484.8 kg",
                    "500.0 kg",
                    "MEDIUM",
                    "CRITICAL"
                ]
                
                # Check for error indicators
                error_indicators = [
                    "function call format",
                    "get_sensor_data",
                    "Service configuration error",
                    "not properly configured",
                    "I'm unable to retrieve",
                    "I've attempted multiple times"
                ]
                
                # Check for knowledge base usage indicators
                kb_indicators = [
                    "based on the data",
                    "according to the report",
                    "the analysis shows",
                    "data indicates",
                    "from the records",
                    "timestamp shows",
                    "device report",
                    "maintenance report"
                ]
                
                found_specific = [point for point in specific_data_points if point.lower() in response_text.lower()]
                found_errors = [error for error in error_indicators if error.lower() in response_text.lower()]
                found_kb_usage = [indicator for indicator in kb_indicators if indicator.lower() in response_text.lower()]
                
                print(f"\nAnalysis:")
                if found_specific:
                    print(f"✅ Specific Data Found: {', '.join(found_specific[:3])}")
                    if len(found_specific) > 3:
                        print(f"   ... and {len(found_specific) - 3} more")
                    success_count += 1
                
                if found_errors:
                    print(f"❌ Errors Found: {', '.join(found_errors[:2])}")
                
                if found_kb_usage:
                    print(f"📚 KB Usage Indicators: {', '.join(found_kb_usage[:2])}")
                
                if not found_specific and not found_errors:
                    print("⚠️  Generic response (no specific data or errors)")
                
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error Details: {error_data}")
                except:
                    print(f"Error Response: {response.text[:200]}...")
                    
        except requests.exceptions.Timeout:
            print("⏱️  Request timed out")
        except requests.exceptions.ConnectionError:
            print("🔌 Connection error")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"TEST SUMMARY")
    print(f"=" * 60)
    print(f"Queries with Specific Data: {success_count}/{len(test_queries)}")
    
    if success_count >= len(test_queries) // 2:
        print("✅ LAMBDA FUNCTION IS WORKING!")
        print("The Lambda function is successfully accessing knowledge base data.")
        return True
    else:
        print("⚠️  LAMBDA FUNCTION NEEDS MORE WORK")
        print("Some queries are still not returning specific knowledge base data.")
        return False

def test_streamlit_integration():
    """Test if Streamlit should now work correctly."""
    
    print(f"\n" + "=" * 60)
    print("STREAMLIT INTEGRATION TEST")
    print("=" * 60)
    
    # Test the exact same query that Streamlit would send
    streamlit_query = "What faults have been detected in the equipment?"
    
    print(f"Testing Streamlit-style query: {streamlit_query}")
    
    try:
        lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
        
        payload = {
            "query": streamlit_query,
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
            
            print(f"\nStreamlit Response ({len(response_text)} chars):")
            print(response_text)
            
            # Compare with what we expect from AWS console
            expected_data = [
                "ball bearing fault",
                "belt slippage",
                "conveyor_motor_001",
                "September 11"
            ]
            
            found_expected = [data for data in expected_data if data.lower() in response_text.lower()]
            
            if found_expected:
                print(f"\n✅ SUCCESS! Found expected data: {', '.join(found_expected)}")
                print("🎉 Streamlit should now show the same data as AWS console!")
                return True
            else:
                print(f"\n⚠️  No expected specific data found")
                print("Streamlit may still show generic responses")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Test the Lambda function
    lambda_works = test_updated_lambda_function()
    
    # Test Streamlit integration
    streamlit_ready = test_streamlit_integration()
    
    print(f"\n" + "🎯" * 20)
    print("FINAL RESULTS")
    print("🎯" * 20)
    
    if lambda_works and streamlit_ready:
        print("🎉 COMPLETE SUCCESS!")
        print("✅ Lambda function is working correctly")
        print("✅ Streamlit should now show specific equipment data")
        print("\nNext steps:")
        print("1. Run: python run_streamlit.py")
        print("2. Ask: 'What faults have been detected in the equipment?'")
        print("3. You should see specific data about conveyor_motor_001 and ball bearing faults!")
    elif lambda_works:
        print("✅ Lambda function is working")
        print("⚠️  But may need more specific queries for best results")
        print("Try asking more specific questions in Streamlit")
    else:
        print("⚠️  Lambda function still needs work")
        print("Check the agent configuration or try different queries")