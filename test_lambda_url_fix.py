#!/usr/bin/env python3
"""
Test Lambda Function URL after applying permission fixes.
"""

import requests
import json
import time
from datetime import datetime

def test_lambda_url_after_fix():
    """Test the Lambda Function URL after applying fixes."""
    function_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    print("🧪 Testing Lambda Function URL After Fix")
    print(f"📅 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 URL: {function_url}")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            'name': 'Basic Connectivity Test',
            'payload': {
                'query': 'System connectivity test after permission fix',
                'sessionId': f'fix-test-{int(time.time())}'
            }
        },
        {
            'name': 'Equipment Status Query',
            'payload': {
                'query': 'What is the current status of the industrial conveyor?',
                'sessionId': f'equipment-test-{int(time.time())}'
            }
        },
        {
            'name': 'Maintenance Recommendation Query',
            'payload': {
                'query': 'What maintenance actions are recommended?',
                'sessionId': f'maintenance-test-{int(time.time())}'
            }
        }
    ]
    
    successful_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        
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
                    
                    print(f"   ✅ SUCCESS")
                    print(f"   Session ID: {session_id}")
                    print(f"   Response Preview: {response_text[:100]}...")
                    
                    successful_tests += 1
                    
                except json.JSONDecodeError:
                    print(f"   ⚠️  Invalid JSON response: {response.text[:100]}")
            else:
                print(f"   ❌ FAILED - HTTP {response.status_code}")
                print(f"   Error: {response.text}")
                
                # Check for specific error types
                if response.status_code == 403:
                    print("   💡 Still getting 403 - permission fix may not have been applied")
                elif response.status_code == 500:
                    print("   💡 Internal error - check Lambda function logs")
                elif response.status_code == 502:
                    print("   💡 Bad Gateway - Lambda function may have errors")
        
        except requests.Timeout:
            print(f"   ❌ TIMEOUT - Request took longer than 60 seconds")
        except requests.ConnectionError:
            print(f"   ❌ CONNECTION ERROR - Cannot reach the Function URL")
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
    
    # Test CORS functionality
    print(f"\n🌐 Testing CORS Configuration...")
    
    try:
        # Test preflight request
        preflight_response = requests.options(
            function_url,
            headers={
                'Origin': 'https://localhost:8501',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=10
        )
        
        print(f"   Preflight Status: {preflight_response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': preflight_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': preflight_response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': preflight_response.headers.get('Access-Control-Allow-Headers')
        }
        
        print(f"   CORS Headers: {cors_headers}")
        
        if preflight_response.status_code == 200:
            print(f"   ✅ CORS working correctly")
        else:
            print(f"   ⚠️  CORS may have issues")
            
    except Exception as e:
        print(f"   ❌ CORS test failed: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    success_rate = successful_tests / len(test_cases)
    
    if success_rate == 1.0:
        print("🎉 ALL TESTS PASSED! Lambda Function URL is working correctly.")
        print("✅ Permission fixes were successful")
        print("✅ Bedrock Agent integration is functional")
        print("✅ Ready for Streamlit app deployment")
    elif success_rate > 0:
        print(f"⚠️  PARTIAL SUCCESS: {successful_tests}/{len(test_cases)} tests passed")
        print("💡 Some functionality working, may need additional fixes")
    else:
        print("❌ ALL TESTS FAILED")
        print("💡 Permission fixes may not have been applied correctly")
        print("💡 Check the fix guide: LAMBDA_URL_FIX_GUIDE.md")
    
    print(f"\nSuccess Rate: {success_rate:.0%}")
    print(f"Function URL: {function_url}")
    
    # Next steps
    if success_rate == 1.0:
        print("\n🚀 Next Steps:")
        print("   1. Deploy Streamlit app using STREAMLIT_DEPLOYMENT_GUIDE.md")
        print("   2. Test end-to-end functionality with real users")
        print("   3. Set up monitoring and alerting")
    else:
        print("\n🔧 Troubleshooting Steps:")
        print("   1. Verify AWS CLI commands were executed successfully")
        print("   2. Check CloudWatch logs for Lambda function errors")
        print("   3. Confirm Function URL auth type is set to NONE")
        print("   4. Verify resource-based policy was added")
        print("   5. Review LAMBDA_URL_FIX_GUIDE.md for detailed steps")

if __name__ == "__main__":
    test_lambda_url_after_fix()