#!/usr/bin/env python3
"""
Test the new Knowledge Base integration via Lambda Function URL.
Check if conveyor-specific data is accessible through the complete system.
"""

import requests
import json
import time
from datetime import datetime

def test_new_kb_via_lambda():
    """Test new Knowledge Base integration via Lambda Function URL."""
    function_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    print("🔗 Testing New Knowledge Base via Lambda Function URL")
    print(f"📅 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 URL: {function_url}")
    print(f"📚 Testing KB: knowledge-base-conveyor-inference (ZECQSVPQJZ)")
    print("=" * 60)
    
    # Test cases specifically for the new Knowledge Base
    test_cases = [
        {
            'name': 'Conveyor Motor Status Query',
            'payload': {
                'query': 'What is the status of conveyor_motor_001? Show me any device reports.',
                'sessionId': f'conveyor-motor-test-{int(time.time())}'
            },
            'expected_keywords': ['conveyor_motor_001', 'device', 'motor', 'status']
        },
        {
            'name': 'Operating Conditions Query',
            'payload': {
                'query': 'What are the current operating conditions for the conveyor system? Show me the latest data.',
                'sessionId': f'operating-conditions-test-{int(time.time())}'
            },
            'expected_keywords': ['operating', 'conditions', 'conveyor', 'data']
        },
        {
            'name': 'Device Report Query',
            'payload': {
                'query': 'Show me the latest device reports for conveyor systems with timestamps.',
                'sessionId': f'device-report-test-{int(time.time())}'
            },
            'expected_keywords': ['device', 'report', 'timestamp', 'conveyor']
        },
        {
            'name': 'Specific Device ID Query',
            'payload': {
                'query': 'Do you have any information about device ID conveyor_motor_001?',
                'sessionId': f'device-id-test-{int(time.time())}'
            },
            'expected_keywords': ['conveyor_motor_001', 'device', 'information']
        }
    ]
    
    successful_tests = 0
    kb_data_found = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"   Query: {test_case['payload']['query']}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                function_url,
                json=test_case['payload'],
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'https://localhost:8501'
                },
                timeout=60
            )
            
            response_time = time.time() - start_time
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Time: {response_time:.2f}s")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    response_text = result.get('response', '')
                    session_id = result.get('sessionId', '')
                    
                    print(f"   Session ID: {session_id}")
                    print(f"   Response Preview: {response_text[:100]}...")
                    
                    if response_text and len(response_text) > 20:
                        successful_tests += 1
                        
                        # Check for specific Knowledge Base indicators
                        response_lower = response_text.lower()
                        
                        # Look for specific data indicators from the new KB
                        kb_indicators = [
                            'device id', 'conveyor_motor_001', 'timestamp', 
                            'device report', 'operating condition', '2025-09',
                            'sensor', 'motor', 'conveyor system'
                        ]
                        
                        kb_matches = sum(1 for indicator in kb_indicators 
                                       if indicator in response_lower)
                        
                        # Check for keyword matches
                        keyword_matches = sum(1 for keyword in test_case['expected_keywords'] 
                                            if keyword.lower() in response_lower)
                        
                        if kb_matches >= 2 or keyword_matches >= 3:
                            kb_data_found += 1
                            print(f"   ✅ SUCCESS - KB data detected (KB indicators: {kb_matches}, Keywords: {keyword_matches})")
                        else:
                            print(f"   ⚠️  SUCCESS - Generic response (KB indicators: {kb_matches}, Keywords: {keyword_matches})")
                    else:
                        print(f"   ❌ FAILED - Empty or short response")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ FAILED - Invalid JSON response")
            else:
                print(f"   ❌ FAILED - HTTP {response.status_code}")
                print(f"   Error: {response.text[:100]}")
        
        except requests.Timeout:
            print(f"   ❌ TIMEOUT - Request took longer than 60 seconds")
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
        
        # Add delay to avoid throttling
        if i < len(test_cases):
            print("   ⏳ Waiting 5 seconds to avoid throttling...")
            time.sleep(5)
    
    # Test a comparative query
    print(f"\n🔄 Comparative Analysis Test")
    print(f"   Query: Compare conveyor data with general maintenance recommendations")
    
    try:
        comparative_payload = {
            'query': 'Compare the conveyor motor data with general maintenance recommendations. What insights can you provide?',
            'sessionId': f'comparative-test-{int(time.time())}'
        }
        
        response = requests.post(
            function_url,
            json=comparative_payload,
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://localhost:8501'
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            if response_text and len(response_text) > 50:
                print(f"   ✅ SUCCESS - Comparative analysis provided")
                print(f"   Response Preview: {response_text[:150]}...")
            else:
                print(f"   ⚠️  LIMITED - Short comparative response")
        else:
            print(f"   ❌ FAILED - HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ ERROR - {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 NEW KNOWLEDGE BASE INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    success_rate = successful_tests / len(test_cases)
    kb_data_rate = kb_data_found / len(test_cases)
    
    print(f"Overall Success Rate: {success_rate:.0%} ({successful_tests}/{len(test_cases)})")
    print(f"KB Data Detection Rate: {kb_data_rate:.0%} ({kb_data_found}/{len(test_cases)})")
    print(f"Function URL: {function_url}")
    print(f"New KB ID: ZECQSVPQJZ")
    
    if success_rate >= 0.75:
        print("\n✅ INTEGRATION SUCCESS!")
        print("📝 Key findings:")
        print("   • Lambda Function URL is working correctly")
        print("   • Agent is responding to conveyor-specific queries")
        if kb_data_rate >= 0.5:
            print("   • New Knowledge Base data is being accessed")
            print("   • Conveyor-specific information is available")
        else:
            print("   • Agent may need more time to fully integrate new KB")
            print("   • Consider checking agent preparation status")
    else:
        print("\n⚠️  INTEGRATION NEEDS ATTENTION")
        print("📝 Issues identified:")
        print("   • Some queries are not working properly")
        print("   • Check agent and Knowledge Base status")
        print("   • Consider re-running tests after agent preparation completes")
    
    print(f"\n🚀 Next Steps:")
    print("   1. Update Streamlit app to include conveyor-specific queries")
    print("   2. Test with real conveyor maintenance scenarios")
    print("   3. Monitor agent performance with dual KB setup")
    print("   4. Consider optimizing queries for better KB utilization")
    
    print("\n" + "=" * 60)
    
    return {
        'success_rate': success_rate,
        'kb_data_rate': kb_data_rate,
        'successful_tests': successful_tests,
        'total_tests': len(test_cases),
        'kb_data_found': kb_data_found
    }

if __name__ == "__main__":
    results = test_new_kb_via_lambda()
    
    # Exit with success if both success rate and KB data rate are good
    import sys
    overall_success = results['success_rate'] >= 0.75 and results['kb_data_rate'] >= 0.25
    sys.exit(0 if overall_success else 1)