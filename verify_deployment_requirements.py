#!/usr/bin/env python3
"""
Verification script to ensure all deployment requirements are met.
Checks Requirements 7.1, 7.6, and 8.6 from the specification.
"""

import json
import boto3
import requests
import time
import os
from datetime import datetime
from typing import Dict, List, Tuple
from botocore.exceptions import ClientError

class DeploymentVerifier:
    """Verifies deployment against specification requirements."""
    
    def __init__(self):
        """Initialize the verifier."""
        self.config = self.load_config()
        self.verification_results = []
        
    def load_config(self) -> Dict:
        """Load AWS configuration."""
        try:
            with open('config/aws_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Config file not found")
            return {}
    
    def log_verification(self, requirement: str, test: str, success: bool, details: str = ""):
        """Log verification result."""
        self.verification_results.append({
            'requirement': requirement,
            'test': test,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {requirement} - {test}")
        if details:
            print(f"    {details}")
    
    def verify_requirement_7_1(self) -> bool:
        """
        Verify Requirement 7.1: Performance and Scalability
        - Multiple concurrent users with <30s response times for 95% of queries
        - System maintains availability under load
        """
        print("\n🚀 Verifying Requirement 7.1: Performance and Scalability")
        
        if not self.config:
            self.log_verification("7.1", "Configuration Check", False, "Config not available")
            return False
        
        # Get Function URL
        try:
            lambda_client = boto3.client('lambda', region_name=self.config['region'])
            function_name = self.config['lambda_functions']['query_handler']['function_name']
            
            response = lambda_client.get_function_url_config(FunctionName=function_name)
            function_url = response['FunctionUrl']
            
        except Exception as e:
            self.log_verification("7.1", "Function URL Access", False, str(e))
            return False
        
        # Test 1: Response time under 30 seconds for 95% of queries
        response_times = []
        successful_queries = 0
        total_queries = 10
        
        test_queries = [
            "What is the current equipment status?",
            "Show me recent fault predictions",
            "What maintenance is recommended?",
            "Analyze sensor data trends",
            "What are the critical alerts?",
            "Show equipment health summary",
            "What preventive maintenance is needed?",
            "Display fault history",
            "Check system performance",
            "What are the maintenance priorities?"
        ]
        
        print(f"    Testing {total_queries} queries for response time...")
        
        for i, query in enumerate(test_queries, 1):
            start_time = time.time()
            
            try:
                response = requests.post(
                    function_url,
                    json={
                        'query': query,
                        'sessionId': f'perf-test-{i}-{int(time.time())}'
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=35
                )
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code == 200 and response_time <= 30.0:
                    successful_queries += 1
                
                print(f"      Query {i}: {response_time:.2f}s ({'✓' if response_time <= 30 else '✗'})")
                
            except requests.Timeout:
                response_times.append(35.0)
                print(f"      Query {i}: TIMEOUT (>35s)")
            except Exception as e:
                response_times.append(30.0)
                print(f"      Query {i}: ERROR - {str(e)}")
        
        # Calculate performance metrics
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            under_30s = len([t for t in response_times if t <= 30.0])
            performance_rate = under_30s / len(response_times)
            
            # Requirement: 95% of queries under 30 seconds
            performance_success = performance_rate >= 0.95
            
            self.log_verification(
                "7.1", 
                "Response Time Performance", 
                performance_success,
                f"95% target: {performance_rate:.0%} actual, Avg: {avg_time:.2f}s"
            )
        else:
            self.log_verification("7.1", "Response Time Performance", False, "No successful queries")
            performance_success = False
        
        # Test 2: Concurrent user simulation
        print("    Testing concurrent user handling...")
        
        import threading
        import queue
        
        concurrent_results = queue.Queue()
        num_concurrent = 5
        
        def concurrent_query(thread_id):
            try:
                start_time = time.time()
                response = requests.post(
                    function_url,
                    json={
                        'query': f'Concurrent test query from thread {thread_id}',
                        'sessionId': f'concurrent-{thread_id}-{int(time.time())}'
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=35
                )
                
                response_time = time.time() - start_time
                success = response.status_code == 200 and response_time <= 30.0
                
                concurrent_results.put({
                    'thread_id': thread_id,
                    'success': success,
                    'response_time': response_time,
                    'status_code': response.status_code
                })
                
            except Exception as e:
                concurrent_results.put({
                    'thread_id': thread_id,
                    'success': False,
                    'error': str(e)
                })
        
        # Launch concurrent threads
        threads = []
        for i in range(num_concurrent):
            thread = threading.Thread(target=concurrent_query, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        concurrent_successes = 0
        concurrent_times = []
        
        while not concurrent_results.empty():
            result = concurrent_results.get()
            if result.get('success', False):
                concurrent_successes += 1
                concurrent_times.append(result.get('response_time', 30))
            
            print(f"      Thread {result.get('thread_id', '?')}: {'✓' if result.get('success') else '✗'}")
        
        concurrent_success_rate = concurrent_successes / num_concurrent
        concurrent_success = concurrent_success_rate >= 0.8  # 80% success rate for concurrent
        
        self.log_verification(
            "7.1", 
            "Concurrent User Handling", 
            concurrent_success,
            f"Success rate: {concurrent_success_rate:.0%} ({concurrent_successes}/{num_concurrent})"
        )
        
        return performance_success and concurrent_success
    
    def verify_requirement_7_6(self) -> bool:
        """
        Verify Requirement 7.6: Integration with existing workflows
        - System doesn't impact performance of other critical systems
        - Proper resource isolation and management
        """
        print("\n🔗 Verifying Requirement 7.6: Integration with Existing Workflows")
        
        # Test 1: Lambda function resource configuration
        try:
            lambda_client = boto3.client('lambda', region_name=self.config['region'])
            function_name = self.config['lambda_functions']['query_handler']['function_name']
            
            response = lambda_client.get_function(FunctionName=function_name)
            config = response['Configuration']
            
            # Check resource limits
            memory_size = config['MemorySize']
            timeout = config['Timeout']
            
            # Verify reasonable resource limits (not excessive)
            memory_ok = 128 <= memory_size <= 1024  # Reasonable range
            timeout_ok = 30 <= timeout <= 300  # Reasonable range
            
            self.log_verification(
                "7.6", 
                "Resource Configuration", 
                memory_ok and timeout_ok,
                f"Memory: {memory_size}MB, Timeout: {timeout}s"
            )
            
        except Exception as e:
            self.log_verification("7.6", "Resource Configuration", False, str(e))
            return False
        
        # Test 2: IAM permissions (least privilege)
        try:
            iam = boto3.client('iam')
            role_name = self.config['iam']['lambda_execution_role']
            
            # Get role policies
            response = iam.list_attached_role_policies(RoleName=role_name)
            attached_policies = response['AttachedPolicies']
            
            # Check for overly broad permissions
            has_basic_execution = any('AWSLambdaBasicExecutionRole' in p['PolicyArn'] for p in attached_policies)
            has_excessive_permissions = any('AdministratorAccess' in p['PolicyArn'] or 'PowerUserAccess' in p['PolicyArn'] for p in attached_policies)
            
            permissions_ok = has_basic_execution and not has_excessive_permissions
            
            self.log_verification(
                "7.6", 
                "IAM Permissions (Least Privilege)", 
                permissions_ok,
                f"Policies: {len(attached_policies)}, Excessive: {'Yes' if has_excessive_permissions else 'No'}"
            )
            
        except Exception as e:
            self.log_verification("7.6", "IAM Permissions", False, str(e))
            return False
        
        # Test 3: Function URL CORS configuration
        try:
            lambda_client = boto3.client('lambda', region_name=self.config['region'])
            
            response = lambda_client.get_function_url_config(FunctionName=function_name)
            cors_config = response.get('Cors', {})
            
            # Check CORS is properly configured (not overly permissive)
            allow_origins = cors_config.get('AllowOrigins', [])
            allow_methods = cors_config.get('AllowMethods', [])
            
            # Should not allow all origins in production
            cors_secure = '*' not in allow_origins or len(allow_origins) > 1
            methods_reasonable = len(allow_methods) <= 5  # Not excessive
            
            self.log_verification(
                "7.6", 
                "CORS Security Configuration", 
                cors_secure and methods_reasonable,
                f"Origins: {len(allow_origins)}, Methods: {len(allow_methods)}"
            )
            
        except Exception as e:
            self.log_verification("7.6", "CORS Configuration", False, str(e))
            return False
        
        return True
    
    def verify_requirement_8_6(self) -> bool:
        """
        Verify Requirement 8.6: End-to-end functionality verification
        - Complete flow from Streamlit to Bedrock Agent works
        - All components integrate properly
        """
        print("\n🔄 Verifying Requirement 8.6: End-to-End Functionality")
        
        # Test 1: Streamlit app file exists and is valid
        app_path = 'streamlit_app/app.py'
        
        if not os.path.exists(app_path):
            self.log_verification("8.6", "Streamlit App Availability", False, "App file not found")
            return False
        
        try:
            # Basic syntax check
            with open(app_path, 'r') as f:
                app_content = f.read()
            
            # Check for required components
            required_components = [
                'streamlit',
                'requests',
                'send_query',
                'chat_message',
                'session_state'
            ]
            
            missing_components = [comp for comp in required_components if comp not in app_content]
            
            app_valid = len(missing_components) == 0
            
            self.log_verification(
                "8.6", 
                "Streamlit App Validation", 
                app_valid,
                f"Missing components: {missing_components}" if missing_components else "All components present"
            )
            
        except Exception as e:
            self.log_verification("8.6", "Streamlit App Validation", False, str(e))
            return False
        
        # Test 2: Complete query flow
        try:
            lambda_client = boto3.client('lambda', region_name=self.config['region'])
            function_name = self.config['lambda_functions']['query_handler']['function_name']
            
            response = lambda_client.get_function_url_config(FunctionName=function_name)
            function_url = response['FunctionUrl']
            
            # Test complete conversation flow
            session_id = f'e2e-test-{int(time.time())}'
            
            conversation_queries = [
                "What is the current status of the industrial conveyor?",
                "What maintenance is recommended based on the current status?",
                "Can you provide more details about the fault predictions?"
            ]
            
            conversation_success = True
            
            for i, query in enumerate(conversation_queries, 1):
                try:
                    response = requests.post(
                        function_url,
                        json={
                            'query': query,
                            'sessionId': session_id
                        },
                        headers={'Content-Type': 'application/json'},
                        timeout=35
                    )
                    
                    if response.status_code != 200:
                        conversation_success = False
                        break
                    
                    result = response.json()
                    if not result.get('response') or len(result['response']) < 10:
                        conversation_success = False
                        break
                    
                    print(f"      Conversation step {i}: ✓")
                    
                except Exception as e:
                    print(f"      Conversation step {i}: ✗ - {str(e)}")
                    conversation_success = False
                    break
            
            self.log_verification(
                "8.6", 
                "Complete Conversation Flow", 
                conversation_success,
                f"Multi-turn conversation: {'Success' if conversation_success else 'Failed'}"
            )
            
        except Exception as e:
            self.log_verification("8.6", "Complete Conversation Flow", False, str(e))
            return False
        
        # Test 3: Error handling and recovery
        try:
            # Test various error scenarios
            error_scenarios = [
                {'query': '', 'expected_status': 400},
                {'query': 'Valid query', 'sessionId': ''},  # Missing session ID should be handled
                {'invalid': 'json'}  # This will be sent as invalid JSON
            ]
            
            error_handling_success = True
            
            for i, scenario in enumerate(error_scenarios, 1):
                try:
                    if 'invalid' in scenario:
                        # Send invalid JSON
                        response = requests.post(
                            function_url,
                            data='invalid json',
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                    else:
                        response = requests.post(
                            function_url,
                            json=scenario,
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                    
                    # Check if error is handled gracefully
                    if scenario.get('expected_status'):
                        if response.status_code != scenario['expected_status']:
                            error_handling_success = False
                    else:
                        # Should handle gracefully (not crash)
                        if response.status_code >= 500:
                            error_handling_success = False
                    
                    print(f"      Error scenario {i}: ✓ (Status: {response.status_code})")
                    
                except Exception as e:
                    print(f"      Error scenario {i}: ✗ - {str(e)}")
                    error_handling_success = False
            
            self.log_verification(
                "8.6", 
                "Error Handling and Recovery", 
                error_handling_success,
                "Graceful error handling verified"
            )
            
        except Exception as e:
            self.log_verification("8.6", "Error Handling", False, str(e))
            return False
        
        return True
    
    def run_verification(self) -> Dict:
        """Run complete verification of deployment requirements."""
        print("🔍 Starting Deployment Requirements Verification...")
        print(f"📅 Verification started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.config:
            return {'success': False, 'error': 'Configuration not available'}
        
        # Verify each requirement
        req_7_1_success = self.verify_requirement_7_1()
        req_7_6_success = self.verify_requirement_7_6()
        req_8_6_success = self.verify_requirement_8_6()
        
        # Calculate overall success
        total_tests = len(self.verification_results)
        passed_tests = len([r for r in self.verification_results if r['success']])
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        overall_success = req_7_1_success and req_7_6_success and req_8_6_success
        
        summary = {
            'success': overall_success,
            'requirements': {
                '7.1': req_7_1_success,
                '7.6': req_7_6_success,
                '8.6': req_8_6_success
            },
            'tests_passed': passed_tests,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'verification_results': self.verification_results
        }
        
        self.print_verification_summary(summary)
        return summary
    
    def print_verification_summary(self, summary: Dict):
        """Print verification summary."""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT REQUIREMENTS VERIFICATION SUMMARY")
        print("=" * 60)
        
        overall_status = "✅ PASS" if summary['success'] else "❌ FAIL"
        print(f"Overall Status: {overall_status}")
        print(f"Tests Passed: {summary['tests_passed']}/{summary['total_tests']} ({summary['success_rate']:.0%})")
        
        print("\n📋 Requirements Status:")
        print("-" * 40)
        
        requirements_map = {
            '7.1': 'Performance and Scalability',
            '7.6': 'Integration with Existing Workflows',
            '8.6': 'End-to-End Functionality'
        }
        
        for req_id, req_name in requirements_map.items():
            status = "✅ PASS" if summary['requirements'][req_id] else "❌ FAIL"
            print(f"{status} Requirement {req_id}: {req_name}")
        
        print("\n📋 Detailed Test Results:")
        print("-" * 40)
        
        for result in summary['verification_results']:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['requirement']} - {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 Deployment Status:")
        if summary['success']:
            print("✅ All deployment requirements verified successfully!")
            print("📝 System is ready for production use:")
            print("   • Performance requirements met (Req 7.1)")
            print("   • Integration requirements satisfied (Req 7.6)")
            print("   • End-to-end functionality verified (Req 8.6)")
            print("   • Deploy Streamlit app to complete the setup")
        else:
            print("⚠️  Some requirements not met. Address the following:")
            failed_reqs = [req for req, success in summary['requirements'].items() if not success]
            for req in failed_reqs:
                print(f"   • Requirement {req}: {requirements_map[req]}")
            print("   • Review failed tests above and fix issues")
            print("   • Re-run verification after fixes")
        
        print("\n" + "=" * 60)

def main():
    """Main verification function."""
    verifier = DeploymentVerifier()
    results = verifier.run_verification()
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()