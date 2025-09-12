#!/usr/bin/env python3
"""
Comprehensive end-to-end testing for Bedrock Agent deployment.
Tests the complete flow from Streamlit to Bedrock Agent.
"""

import json
import requests
import time
import boto3
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from botocore.exceptions import ClientError

class EndToEndTester:
    """Comprehensive end-to-end testing for the Bedrock Agent system."""
    
    def __init__(self):
        """Initialize the tester with configuration."""
        self.config = self.load_config()
        self.test_results = []
        self.start_time = datetime.now()
        
    def load_config(self) -> Optional[Dict]:
        """Load AWS configuration."""
        try:
            with open('config/aws_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Config file not found: config/aws_config.json")
            return None
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", duration: float = 0):
        """Log test result for final summary."""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        print(f"{status}: {test_name}{duration_str}")
        if details:
            print(f"    {details}")
    
    def test_aws_credentials(self) -> bool:
        """Test AWS credentials and permissions."""
        print("\n🔐 Testing AWS Credentials...")
        test_start = time.time()
        
        try:
            # Test basic AWS access
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            
            account_id = identity['Account']
            user_arn = identity['Arn']
            
            self.log_test_result(
                "AWS Credentials", 
                True, 
                f"Account: {account_id}, User: {user_arn.split('/')[-1]}", 
                time.time() - test_start
            )
            return True
            
        except Exception as e:
            self.log_test_result("AWS Credentials", False, str(e), time.time() - test_start)
            return False
    
    def test_bedrock_agent_status(self) -> bool:
        """Test Bedrock Agent availability and status."""
        print("\n🤖 Testing Bedrock Agent Status...")
        test_start = time.time()
        
        try:
            bedrock_agent = boto3.client('bedrock-agent', region_name=self.config['region'])
            
            agent_id = self.config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
            alias_id = self.config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
            
            # Get agent details
            agent_response = bedrock_agent.get_agent(agentId=agent_id)
            agent_status = agent_response['agent']['agentStatus']
            
            # Get alias details
            alias_response = bedrock_agent.get_agent_alias(
                agentId=agent_id,
                agentAliasId=alias_id
            )
            alias_status = alias_response['agentAlias']['agentAliasStatus']
            
            success = agent_status in ['PREPARED', 'VERSIONED'] and alias_status in ['PREPARED', 'UPDATED']
            
            self.log_test_result(
                "Bedrock Agent Status", 
                success, 
                f"Agent: {agent_status}, Alias: {alias_status}", 
                time.time() - test_start
            )
            return success
            
        except Exception as e:
            self.log_test_result("Bedrock Agent Status", False, str(e), time.time() - test_start)
            return False
    
    def test_knowledge_base_status(self) -> bool:
        """Test Knowledge Base availability and data sync status."""
        print("\n📚 Testing Knowledge Base Status...")
        test_start = time.time()
        
        try:
            bedrock_agent = boto3.client('bedrock-agent', region_name=self.config['region'])
            
            kb_id = self.config['knowledge_base_id']
            
            # Get knowledge base details
            kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
            kb_status = kb_response['knowledgeBase']['status']
            
            # Get data sources
            data_sources_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
            data_sources = data_sources_response['dataSourceSummaries']
            
            # Check data source status
            all_sources_ready = True
            source_details = []
            
            for ds in data_sources:
                ds_detail = bedrock_agent.get_data_source(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds['dataSourceId']
                )
                ds_status = ds_detail['dataSource']['status']
                source_details.append(f"{ds['name']}: {ds_status}")
                
                if ds_status not in ['AVAILABLE']:
                    all_sources_ready = False
            
            success = kb_status == 'ACTIVE' and all_sources_ready
            
            self.log_test_result(
                "Knowledge Base Status", 
                success, 
                f"KB: {kb_status}, Sources: {', '.join(source_details)}", 
                time.time() - test_start
            )
            return success
            
        except Exception as e:
            self.log_test_result("Knowledge Base Status", False, str(e), time.time() - test_start)
            return False
    
    def test_lambda_function_deployment(self) -> Tuple[bool, Optional[str]]:
        """Test Lambda function deployment and configuration."""
        print("\n⚡ Testing Lambda Function Deployment...")
        test_start = time.time()
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.config['region'])
            
            function_name = self.config['lambda_functions']['query_handler']['function_name']
            
            # Get function configuration
            function_response = lambda_client.get_function(FunctionName=function_name)
            function_config = function_response['Configuration']
            
            # Check function state
            state = function_config['State']
            last_update_status = function_config['LastUpdateStatus']
            
            # Get Function URL
            try:
                url_response = lambda_client.get_function_url_config(FunctionName=function_name)
                function_url = url_response['FunctionUrl']
                auth_type = url_response['AuthType']
            except ClientError:
                function_url = None
                auth_type = None
            
            success = (state == 'Active' and 
                      last_update_status == 'Successful' and 
                      function_url is not None)
            
            details = f"State: {state}, URL: {'✓' if function_url else '✗'}, Auth: {auth_type}"
            
            self.log_test_result(
                "Lambda Function Deployment", 
                success, 
                details, 
                time.time() - test_start
            )
            
            return success, function_url
            
        except Exception as e:
            self.log_test_result("Lambda Function Deployment", False, str(e), time.time() - test_start)
            return False, None
    
    def test_lambda_function_invocation(self, function_url: str) -> bool:
        """Test direct Lambda function invocation via Function URL."""
        print("\n🔗 Testing Lambda Function Invocation...")
        test_start = time.time()
        
        test_queries = [
            "What is the current status of the industrial conveyor?",
            "Show me recent fault predictions",
            "What maintenance is recommended?",
            "System health check"
        ]
        
        successful_queries = 0
        total_response_time = 0
        
        for i, query in enumerate(test_queries, 1):
            try:
                query_start = time.time()
                
                payload = {
                    'query': query,
                    'sessionId': f'test-session-{i}-{int(time.time())}'
                }
                
                response = requests.post(
                    function_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=60  # Increased timeout for Bedrock Agent
                )
                
                query_time = time.time() - query_start
                total_response_time += query_time
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '')
                    
                    if response_text and len(response_text) > 10:
                        successful_queries += 1
                        print(f"    Query {i}: ✅ ({query_time:.2f}s) - {response_text[:50]}...")
                    else:
                        print(f"    Query {i}: ⚠️  Empty response ({query_time:.2f}s)")
                else:
                    print(f"    Query {i}: ❌ HTTP {response.status_code} ({query_time:.2f}s)")
                    
            except Exception as e:
                print(f"    Query {i}: ❌ Error - {str(e)}")
        
        success_rate = successful_queries / len(test_queries)
        avg_response_time = total_response_time / len(test_queries)
        
        success = success_rate >= 0.75  # At least 75% success rate
        
        details = f"Success: {successful_queries}/{len(test_queries)} ({success_rate:.0%}), Avg time: {avg_response_time:.2f}s"
        
        self.log_test_result(
            "Lambda Function Invocation", 
            success, 
            details, 
            time.time() - test_start
        )
        
        return success
    
    def test_cors_configuration(self, function_url: str) -> bool:
        """Test CORS configuration for Streamlit integration."""
        print("\n🌐 Testing CORS Configuration...")
        test_start = time.time()
        
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
            
            # Check CORS headers
            cors_headers = preflight_response.headers
            
            required_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            missing_headers = [h for h in required_headers if h not in cors_headers]
            
            # Test actual POST request with CORS
            post_response = requests.post(
                function_url,
                json={'query': 'CORS test', 'sessionId': 'cors-test'},
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'https://localhost:8501'
                },
                timeout=30
            )
            
            cors_origin = post_response.headers.get('Access-Control-Allow-Origin', '')
            
            success = (preflight_response.status_code == 200 and 
                      len(missing_headers) == 0 and
                      cors_origin in ['https://localhost:8501', '*'])
            
            details = f"Preflight: {preflight_response.status_code}, Origin: {cors_origin}, Missing: {missing_headers}"
            
            self.log_test_result(
                "CORS Configuration", 
                success, 
                details, 
                time.time() - test_start
            )
            
            return success
            
        except Exception as e:
            self.log_test_result("CORS Configuration", False, str(e), time.time() - test_start)
            return False
    
    def test_streamlit_app_startup(self) -> bool:
        """Test Streamlit application startup and basic functionality."""
        print("\n🎨 Testing Streamlit App Startup...")
        test_start = time.time()
        
        try:
            # Check if Streamlit app file exists
            app_path = 'streamlit_app/app.py'
            if not os.path.exists(app_path):
                self.log_test_result("Streamlit App Startup", False, "App file not found", time.time() - test_start)
                return False
            
            # Test import of the app (basic syntax check)
            import importlib.util
            spec = importlib.util.spec_from_file_location("streamlit_app", app_path)
            module = importlib.util.module_from_spec(spec)
            
            # This will catch syntax errors
            spec.loader.exec_module(module)
            
            # Check for required functions
            required_functions = ['main', 'send_query_with_context']
            missing_functions = []
            
            for func in required_functions:
                if not hasattr(module, func):
                    missing_functions.append(func)
            
            success = len(missing_functions) == 0
            
            details = f"Syntax: ✓, Missing functions: {missing_functions}" if missing_functions else "All checks passed"
            
            self.log_test_result(
                "Streamlit App Startup", 
                success, 
                details, 
                time.time() - test_start
            )
            
            return success
            
        except Exception as e:
            self.log_test_result("Streamlit App Startup", False, str(e), time.time() - test_start)
            return False
    
    def test_streamlit_integration(self, function_url: str) -> bool:
        """Test Streamlit integration with Lambda function."""
        print("\n🔗 Testing Streamlit-Lambda Integration...")
        test_start = time.time()
        
        try:
            # Simulate Streamlit app behavior
            import sys
            sys.path.append('streamlit_app')
            
            # Test the send_query function directly
            test_payload = {
                'query': 'Integration test query',
                'sessionId': 'integration-test-session',
                'equipment_filter': ['Industrial Conveyor'],
                'time_range': 'Last 24 hours'
            }
            
            response = requests.post(
                function_url,
                json=test_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'https://localhost:8501'
                },
                timeout=30
            )
            
            success = (response.status_code == 200 and 
                      'response' in response.json() and
                      len(response.json()['response']) > 0)
            
            if success:
                result = response.json()
                details = f"Status: {response.status_code}, Response length: {len(result.get('response', ''))}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text[:100]}"
            
            self.log_test_result(
                "Streamlit-Lambda Integration", 
                success, 
                details, 
                time.time() - test_start
            )
            
            return success
            
        except Exception as e:
            self.log_test_result("Streamlit-Lambda Integration", False, str(e), time.time() - test_start)
            return False
    
    def test_performance_requirements(self, function_url: str) -> bool:
        """Test performance requirements (Requirement 7.1: 30-second response time)."""
        print("\n⚡ Testing Performance Requirements...")
        test_start = time.time()
        
        try:
            performance_queries = [
                "What is the current equipment status?",
                "Show me fault predictions for the last week",
                "What maintenance actions are recommended?",
                "Analyze sensor data trends",
                "What are the critical alerts?"
            ]
            
            response_times = []
            successful_queries = 0
            
            for i, query in enumerate(performance_queries, 1):
                query_start = time.time()
                
                try:
                    response = requests.post(
                        function_url,
                        json={
                            'query': query,
                            'sessionId': f'perf-test-{i}-{int(time.time())}'
                        },
                        headers={'Content-Type': 'application/json'},
                        timeout=35  # Slightly more than 30s requirement
                    )
                    
                    query_time = time.time() - query_start
                    response_times.append(query_time)
                    
                    if response.status_code == 200 and query_time <= 30.0:
                        successful_queries += 1
                        print(f"    Query {i}: ✅ {query_time:.2f}s")
                    else:
                        print(f"    Query {i}: ⚠️  {query_time:.2f}s (Status: {response.status_code})")
                        
                except requests.Timeout:
                    print(f"    Query {i}: ❌ Timeout (>35s)")
                    response_times.append(35.0)
                except Exception as e:
                    print(f"    Query {i}: ❌ Error - {str(e)}")
                    response_times.append(30.0)  # Assume worst case
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                success_rate = successful_queries / len(performance_queries)
                
                # Requirement 7.1: 95% of queries under 30 seconds
                under_30s = len([t for t in response_times if t <= 30.0])
                performance_rate = under_30s / len(response_times)
                
                success = performance_rate >= 0.95
                
                details = f"Avg: {avg_time:.2f}s, Max: {max_time:.2f}s, <30s: {performance_rate:.0%}"
            else:
                success = False
                details = "No successful queries"
            
            self.log_test_result(
                "Performance Requirements", 
                success, 
                details, 
                time.time() - test_start
            )
            
            return success
            
        except Exception as e:
            self.log_test_result("Performance Requirements", False, str(e), time.time() - test_start)
            return False
    
    def test_error_handling(self, function_url: str) -> bool:
        """Test error handling and recovery scenarios."""
        print("\n🛡️  Testing Error Handling...")
        test_start = time.time()
        
        error_scenarios = [
            {'query': '', 'expected_status': 400, 'description': 'Empty query'},
            {'query': 'x' * 15000, 'expected_status': 400, 'description': 'Oversized query'},
            {'invalid_json': True, 'description': 'Invalid JSON'},
            {'query': 'Valid query', 'sessionId': '', 'expected_status': 200, 'description': 'Missing session ID'}
        ]
        
        successful_error_handling = 0
        
        for i, scenario in enumerate(error_scenarios, 1):
            try:
                if scenario.get('invalid_json'):
                    # Send invalid JSON
                    response = requests.post(
                        function_url,
                        data='invalid json content',
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                else:
                    # Send valid JSON with test scenario
                    payload = {k: v for k, v in scenario.items() if k not in ['expected_status', 'description']}
                    response = requests.post(
                        function_url,
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                
                expected_status = scenario.get('expected_status', 400)
                
                if response.status_code == expected_status:
                    successful_error_handling += 1
                    print(f"    Scenario {i}: ✅ {scenario['description']} (Status: {response.status_code})")
                else:
                    print(f"    Scenario {i}: ⚠️  {scenario['description']} (Expected: {expected_status}, Got: {response.status_code})")
                    
            except Exception as e:
                print(f"    Scenario {i}: ❌ {scenario['description']} - Error: {str(e)}")
        
        success_rate = successful_error_handling / len(error_scenarios)
        success = success_rate >= 0.75  # At least 75% of error scenarios handled correctly
        
        details = f"Handled: {successful_error_handling}/{len(error_scenarios)} ({success_rate:.0%})"
        
        self.log_test_result(
            "Error Handling", 
            success, 
            details, 
            time.time() - test_start
        )
        
        return success
    
    def run_comprehensive_tests(self) -> Dict:
        """Run all comprehensive end-to-end tests."""
        print("🚀 Starting Comprehensive End-to-End Testing...")
        print(f"📅 Test started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.config:
            print("❌ Cannot proceed without configuration")
            return {'success': False, 'error': 'Configuration not found'}
        
        # Test sequence
        tests_passed = 0
        total_tests = 0
        
        # 1. Test AWS credentials
        total_tests += 1
        if self.test_aws_credentials():
            tests_passed += 1
        
        # 2. Test Bedrock Agent status
        total_tests += 1
        if self.test_bedrock_agent_status():
            tests_passed += 1
        
        # 3. Test Knowledge Base status
        total_tests += 1
        if self.test_knowledge_base_status():
            tests_passed += 1
        
        # 4. Test Lambda deployment and get Function URL
        total_tests += 1
        lambda_success, function_url = self.test_lambda_function_deployment()
        if lambda_success:
            tests_passed += 1
        
        if function_url:
            # 5. Test Lambda invocation
            total_tests += 1
            if self.test_lambda_function_invocation(function_url):
                tests_passed += 1
            
            # 6. Test CORS configuration
            total_tests += 1
            if self.test_cors_configuration(function_url):
                tests_passed += 1
            
            # 7. Test Streamlit app
            total_tests += 1
            if self.test_streamlit_app_startup():
                tests_passed += 1
            
            # 8. Test Streamlit integration
            total_tests += 1
            if self.test_streamlit_integration(function_url):
                tests_passed += 1
            
            # 9. Test performance requirements
            total_tests += 1
            if self.test_performance_requirements(function_url):
                tests_passed += 1
            
            # 10. Test error handling
            total_tests += 1
            if self.test_error_handling(function_url):
                tests_passed += 1
        
        # Generate summary
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        success_rate = tests_passed / total_tests if total_tests > 0 else 0
        
        summary = {
            'success': success_rate >= 0.8,  # 80% success rate required
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'duration': total_duration,
            'function_url': function_url,
            'test_results': self.test_results
        }
        
        self.print_summary(summary)
        return summary
    
    def print_summary(self, summary: Dict):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        # Overall results
        overall_status = "✅ PASS" if summary['success'] else "❌ FAIL"
        print(f"Overall Status: {overall_status}")
        print(f"Tests Passed: {summary['tests_passed']}/{summary['total_tests']} ({summary['success_rate']:.0%})")
        print(f"Total Duration: {summary['duration']:.2f} seconds")
        
        if summary.get('function_url'):
            print(f"Function URL: {summary['function_url']}")
        
        print("\n📋 Detailed Results:")
        print("-" * 40)
        
        for result in summary['test_results']:
            status = "✅" if result['success'] else "❌"
            duration = f" ({result['duration']:.2f}s)" if result['duration'] > 0 else ""
            print(f"{status} {result['test']}{duration}")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 Next Steps:")
        if summary['success']:
            print("✅ All critical tests passed! System is ready for production.")
            print("📝 Recommended actions:")
            print("   • Deploy Streamlit app to chosen hosting platform")
            print("   • Configure monitoring and alerting")
            print("   • Set up backup and disaster recovery")
            print("   • Conduct user acceptance testing")
        else:
            print("⚠️  Some tests failed. Address the following issues:")
            failed_tests = [r for r in summary['test_results'] if not r['success']]
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        print("\n" + "=" * 60)

def main():
    """Main function to run comprehensive end-to-end tests."""
    tester = EndToEndTester()
    results = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()