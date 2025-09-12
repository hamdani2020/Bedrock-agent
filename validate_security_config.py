#!/usr/bin/env python3
"""
Validate security configuration for Bedrock Agent system.
Tests IAM roles, CORS settings, and authentication mechanisms.
"""
import json
import boto3
import requests
from typing import Dict, Any, List
from botocore.exceptions import ClientError

def load_config() -> Dict[str, Any]:
    """Load AWS configuration."""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ AWS config file not found")
        return {}

def validate_iam_roles(iam_client) -> Dict[str, bool]:
    """Validate IAM roles exist and have proper policies."""
    config = load_config()
    results = {}
    
    roles_to_check = [
        config['iam']['lambda_execution_role'],
        config['iam']['bedrock_agent_role'],
        config['iam']['knowledge_base_role']
    ]
    
    for role_name in roles_to_check:
        try:
            # Check if role exists
            response = iam_client.get_role(RoleName=role_name)
            print(f"✅ Role exists: {role_name}")
            
            # Check attached policies
            policies = iam_client.list_attached_role_policies(RoleName=role_name)
            print(f"   Attached policies: {len(policies['AttachedPolicies'])}")
            
            for policy in policies['AttachedPolicies']:
                print(f"   - {policy['PolicyName']}")
            
            results[role_name] = True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"❌ Role not found: {role_name}")
                results[role_name] = False
            else:
                print(f"❌ Error checking role {role_name}: {e}")
                results[role_name] = False
    
    return results

def validate_function_urls(lambda_client) -> Dict[str, Dict[str, Any]]:
    """Validate Lambda Function URLs and CORS configuration."""
    config = load_config()
    results = {}
    
    for function_key, function_config in config['lambda_functions'].items():
        if 'function_url' in function_config:
            function_name = function_config['function_name']
            
            try:
                # Get Function URL configuration
                response = lambda_client.get_function_url_config(
                    FunctionName=function_name
                )
                
                url_config = {
                    'url': response['FunctionUrl'],
                    'auth_type': response['AuthType'],
                    'cors': response.get('Cors', {}),
                    'creation_time': response['CreationTime']
                }
                
                print(f"✅ Function URL configured: {function_name}")
                print(f"   URL: {url_config['url']}")
                print(f"   Auth: {url_config['auth_type']}")
                print(f"   CORS Origins: {url_config['cors'].get('AllowOrigins', [])}")
                
                results[function_name] = url_config
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"❌ Function URL not found: {function_name}")
                    results[function_name] = {'error': 'Not found'}
                else:
                    print(f"❌ Error checking Function URL for {function_name}: {e}")
                    results[function_name] = {'error': str(e)}
    
    return results

def test_cors_configuration(function_urls: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
    """Test CORS configuration by making preflight requests."""
    results = {}
    
    test_origins = [
        'https://localhost:8501',
        'https://malicious-site.com',  # Should be rejected
        'https://test.streamlit.app'
    ]
    
    for function_name, url_config in function_urls.items():
        if 'url' in url_config:
            function_url = url_config['url']
            print(f"\n🧪 Testing CORS for {function_name}...")
            
            for origin in test_origins:
                try:
                    # Make preflight request
                    response = requests.options(
                        function_url,
                        headers={
                            'Origin': origin,
                            'Access-Control-Request-Method': 'POST',
                            'Access-Control-Request-Headers': 'content-type'
                        },
                        timeout=10
                    )
                    
                    allowed_origin = response.headers.get('Access-Control-Allow-Origin', '')
                    
                    if origin == 'https://malicious-site.com':
                        # This should be rejected
                        if allowed_origin == origin:
                            print(f"   ⚠️  {origin}: Incorrectly allowed (security risk)")
                            results[f"{function_name}_{origin}"] = False
                        else:
                            print(f"   ✅ {origin}: Correctly rejected")
                            results[f"{function_name}_{origin}"] = True
                    else:
                        # These should be allowed
                        if allowed_origin == origin or allowed_origin == '*':
                            print(f"   ✅ {origin}: Correctly allowed")
                            results[f"{function_name}_{origin}"] = True
                        else:
                            print(f"   ❌ {origin}: Incorrectly rejected")
                            results[f"{function_name}_{origin}"] = False
                
                except requests.exceptions.RequestException as e:
                    print(f"   ❌ {origin}: Request failed - {e}")
                    results[f"{function_name}_{origin}"] = False
    
    return results

def validate_authentication(function_urls: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
    """Validate authentication configuration."""
    results = {}
    
    for function_name, url_config in function_urls.items():
        if 'auth_type' in url_config:
            auth_type = url_config['auth_type']
            
            if function_name == 'bedrock-agent-session-manager':
                # Should use IAM authentication
                if auth_type == 'AWS_IAM':
                    print(f"✅ {function_name}: Correctly using IAM authentication")
                    results[function_name] = True
                else:
                    print(f"❌ {function_name}: Should use IAM authentication, found {auth_type}")
                    results[function_name] = False
            
            elif function_name == 'bedrock-agent-health-check':
                # Can use NONE for public health checks
                if auth_type in ['NONE', 'AWS_IAM']:
                    print(f"✅ {function_name}: Using {auth_type} authentication")
                    results[function_name] = True
                else:
                    print(f"❌ {function_name}: Unexpected auth type {auth_type}")
                    results[function_name] = False
            
            else:
                # Other functions can use NONE but should have request validation
                print(f"✅ {function_name}: Using {auth_type} authentication")
                results[function_name] = True
    
    return results

def check_security_headers(function_urls: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
    """Check if security headers are properly configured."""
    results = {}
    
    required_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Strict-Transport-Security'
    ]
    
    for function_name, url_config in function_urls.items():
        if 'url' in url_config:
            function_url = url_config['url']
            
            try:
                # Make a test request
                response = requests.post(
                    function_url,
                    json={'query': 'test', 'sessionId': 'test'},
                    timeout=10
                )
                
                missing_headers = []
                for header in required_headers:
                    if header not in response.headers:
                        missing_headers.append(header)
                
                if not missing_headers:
                    print(f"✅ {function_name}: All security headers present")
                    results[function_name] = True
                else:
                    print(f"⚠️  {function_name}: Missing headers: {missing_headers}")
                    results[function_name] = False
                
            except requests.exceptions.RequestException as e:
                print(f"❌ {function_name}: Could not test headers - {e}")
                results[function_name] = False
    
    return results

def main():
    """Main validation function."""
    print("🔒 Validating Bedrock Agent Security Configuration")
    print("=" * 60)
    
    # Initialize AWS clients
    iam_client = boto3.client('iam')
    lambda_client = boto3.client('lambda')
    
    # 1. Validate IAM roles
    print("\n1️⃣  Validating IAM Roles...")
    iam_results = validate_iam_roles(iam_client)
    
    # 2. Validate Function URLs
    print("\n2️⃣  Validating Function URLs...")
    function_url_results = validate_function_urls(lambda_client)
    
    # 3. Test CORS configuration
    print("\n3️⃣  Testing CORS Configuration...")
    cors_results = test_cors_configuration(function_url_results)
    
    # 4. Validate authentication
    print("\n4️⃣  Validating Authentication...")
    auth_results = validate_authentication(function_url_results)
    
    # 5. Check security headers
    print("\n5️⃣  Checking Security Headers...")
    header_results = check_security_headers(function_url_results)
    
    # Summary
    print("\n📊 Security Validation Summary")
    print("=" * 40)
    
    total_checks = 0
    passed_checks = 0
    
    # IAM roles
    for role, passed in iam_results.items():
        total_checks += 1
        if passed:
            passed_checks += 1
    
    # CORS tests
    for test, passed in cors_results.items():
        total_checks += 1
        if passed:
            passed_checks += 1
    
    # Authentication tests
    for func, passed in auth_results.items():
        total_checks += 1
        if passed:
            passed_checks += 1
    
    # Security headers
    for func, passed in header_results.items():
        total_checks += 1
        if passed:
            passed_checks += 1
    
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    print(f"Success rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 All security validations passed!")
    else:
        print(f"\n⚠️  {total_checks - passed_checks} security issues found. Please review and fix.")
    
    return passed_checks == total_checks

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)