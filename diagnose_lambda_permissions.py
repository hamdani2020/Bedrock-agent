#!/usr/bin/env python3
"""
Diagnose Lambda function URL permission issues.
Identifies and fixes common permission problems.
"""

import boto3
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
from botocore.exceptions import ClientError

class LambdaPermissionDiagnostic:
    """Diagnose and fix Lambda function URL permission issues."""
    
    def __init__(self):
        """Initialize the diagnostic tool."""
        self.config = self.load_config()
        self.function_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
        self.function_name = None
        self.region = None
        self.issues_found = []
        self.fixes_applied = []
        
        if self.config:
            self.function_name = self.config['lambda_functions']['query_handler']['function_name']
            self.region = self.config['region']
    
    def load_config(self) -> Optional[Dict]:
        """Load AWS configuration."""
        try:
            with open('config/aws_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Config file not found")
            return None
    
    def log_issue(self, issue: str, details: str = ""):
        """Log an issue found."""
        self.issues_found.append({'issue': issue, 'details': details})
        print(f"❌ ISSUE: {issue}")
        if details:
            print(f"    {details}")
    
    def log_fix(self, fix: str, details: str = ""):
        """Log a fix applied."""
        self.fixes_applied.append({'fix': fix, 'details': details})
        print(f"✅ FIXED: {fix}")
        if details:
            print(f"    {details}")
    
    def test_function_url_access(self) -> bool:
        """Test direct access to Function URL."""
        print("\n🔗 Testing Function URL Access...")
        
        try:
            # Test with minimal payload
            response = requests.post(
                self.function_url,
                json={'query': 'test', 'sessionId': 'diagnostic-test'},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"    Status Code: {response.status_code}")
            print(f"    Response Headers: {dict(response.headers)}")
            
            if response.status_code == 403:
                self.log_issue(
                    "Function URL Access Denied", 
                    f"HTTP 403: {response.text}"
                )
                return False
            elif response.status_code == 200:
                print("✅ Function URL accessible")
                return True
            else:
                self.log_issue(
                    f"Unexpected HTTP Status: {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_issue("Function URL Connection Error", str(e))
            return False
    
    def check_function_url_config(self) -> bool:
        """Check Function URL configuration."""
        print("\n🔧 Checking Function URL Configuration...")
        
        if not self.function_name or not self.region:
            self.log_issue("Missing Configuration", "Function name or region not configured")
            return False
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Get Function URL configuration
            response = lambda_client.get_function_url_config(FunctionName=self.function_name)
            
            function_url = response['FunctionUrl']
            auth_type = response['AuthType']
            cors_config = response.get('Cors', {})
            
            print(f"    Function URL: {function_url}")
            print(f"    Auth Type: {auth_type}")
            print(f"    CORS Config: {cors_config}")
            
            # Check if URL matches expected
            if function_url != self.function_url:
                self.log_issue(
                    "Function URL Mismatch",
                    f"Expected: {self.function_url}, Actual: {function_url}"
                )
            
            # Check auth type
            if auth_type != 'NONE':
                self.log_issue(
                    "Function URL Auth Type",
                    f"Auth type is '{auth_type}', should be 'NONE' for public access"
                )
                return False
            
            print("✅ Function URL configuration looks correct")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                self.log_issue("Function URL Not Found", "Function URL not configured")
            else:
                self.log_issue("AWS API Error", f"{error_code}: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            self.log_issue("Configuration Check Error", str(e))
            return False
    
    def check_lambda_function_status(self) -> bool:
        """Check Lambda function status and configuration."""
        print("\n⚡ Checking Lambda Function Status...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Get function configuration
            response = lambda_client.get_function(FunctionName=self.function_name)
            config = response['Configuration']
            
            state = config['State']
            last_update_status = config['LastUpdateStatus']
            runtime = config['Runtime']
            handler = config['Handler']
            
            print(f"    Function State: {state}")
            print(f"    Last Update Status: {last_update_status}")
            print(f"    Runtime: {runtime}")
            print(f"    Handler: {handler}")
            
            if state != 'Active':
                self.log_issue("Function Not Active", f"Function state is '{state}'")
                return False
            
            if last_update_status != 'Successful':
                self.log_issue("Function Update Failed", f"Last update status: '{last_update_status}'")
                return False
            
            print("✅ Lambda function is active and healthy")
            return True
            
        except ClientError as e:
            self.log_issue("Lambda Function Check Error", str(e))
            return False
        except Exception as e:
            self.log_issue("Function Status Check Error", str(e))
            return False
    
    def check_iam_permissions(self) -> bool:
        """Check IAM permissions for Lambda execution."""
        print("\n🔐 Checking IAM Permissions...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Get function configuration to find execution role
            response = lambda_client.get_function(FunctionName=self.function_name)
            role_arn = response['Configuration']['Role']
            
            print(f"    Execution Role: {role_arn}")
            
            # Extract role name from ARN
            role_name = role_arn.split('/')[-1]
            
            # Check role exists and has proper policies
            iam = boto3.client('iam')
            
            try:
                role_response = iam.get_role(RoleName=role_name)
                print(f"    Role exists: {role_name}")
                
                # Check attached policies
                policies_response = iam.list_attached_role_policies(RoleName=role_name)
                attached_policies = policies_response['AttachedPolicies']
                
                print(f"    Attached Policies: {len(attached_policies)}")
                for policy in attached_policies:
                    print(f"      - {policy['PolicyName']}: {policy['PolicyArn']}")
                
                # Check for required policies
                required_policies = [
                    'AWSLambdaBasicExecutionRole',
                    'bedrock'  # Should have some bedrock policy
                ]
                
                policy_names = [p['PolicyName'] for p in attached_policies]
                missing_policies = []
                
                for req_policy in required_policies:
                    if not any(req_policy.lower() in name.lower() for name in policy_names):
                        missing_policies.append(req_policy)
                
                if missing_policies:
                    self.log_issue("Missing IAM Policies", f"Missing: {missing_policies}")
                    return False
                
                print("✅ IAM permissions look correct")
                return True
                
            except ClientError as e:
                self.log_issue("IAM Role Check Error", str(e))
                return False
                
        except Exception as e:
            self.log_issue("IAM Permission Check Error", str(e))
            return False
    
    def check_function_url_resource_policy(self) -> bool:
        """Check Function URL resource-based policy."""
        print("\n📋 Checking Function URL Resource Policy...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Try to get the function's resource-based policy
            try:
                policy_response = lambda_client.get_policy(FunctionName=self.function_name)
                policy = json.loads(policy_response['Policy'])
                
                print(f"    Resource Policy exists")
                print(f"    Policy: {json.dumps(policy, indent=2)}")
                
                # Check if policy allows public access for Function URL
                statements = policy.get('Statement', [])
                
                public_access_allowed = False
                for statement in statements:
                    if (statement.get('Effect') == 'Allow' and 
                        statement.get('Principal') == '*' and
                        'lambda:InvokeFunctionUrl' in statement.get('Action', [])):
                        public_access_allowed = True
                        break
                
                if not public_access_allowed:
                    self.log_issue(
                        "Function URL Policy Missing",
                        "No public access policy for InvokeFunctionUrl"
                    )
                    return False
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    self.log_issue(
                        "No Resource Policy",
                        "Function URL requires resource-based policy for public access"
                    )
                    return False
                else:
                    raise
            
            print("✅ Function URL resource policy is configured")
            return True
            
        except Exception as e:
            self.log_issue("Resource Policy Check Error", str(e))
            return False
    
    def fix_function_url_permissions(self) -> bool:
        """Fix Function URL permissions by adding resource-based policy."""
        print("\n🔧 Fixing Function URL Permissions...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Add resource-based policy to allow public access to Function URL
            policy_statement = {
                "Sid": "AllowPublicFunctionUrlAccess",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "lambda:InvokeFunctionUrl",
                "Resource": f"arn:aws:lambda:{self.region}:*:function:{self.function_name}",
                "Condition": {
                    "StringEquals": {
                        "lambda:FunctionUrlAuthType": "NONE"
                    }
                }
            }
            
            # Try to add the permission
            lambda_client.add_permission(
                FunctionName=self.function_name,
                StatementId="AllowPublicFunctionUrlAccess",
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                SourceAccount="*"
            )
            
            self.log_fix(
                "Added Function URL Permission",
                "Added resource-based policy for public Function URL access"
            )
            
            # Wait a moment for the permission to propagate
            time.sleep(5)
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceConflictException':
                print("    Permission already exists")
                return True
            else:
                self.log_issue("Permission Fix Failed", f"{error_code}: {e.response['Error']['Message']}")
                return False
        except Exception as e:
            self.log_issue("Permission Fix Error", str(e))
            return False
    
    def fix_function_url_auth_type(self) -> bool:
        """Fix Function URL auth type to NONE."""
        print("\n🔧 Fixing Function URL Auth Type...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Update Function URL configuration
            lambda_client.update_function_url_config(
                FunctionName=self.function_name,
                AuthType='NONE',
                Cors={
                    'AllowCredentials': False,
                    'AllowHeaders': [
                        'content-type',
                        'x-amz-date',
                        'authorization',
                        'x-api-key',
                        'x-amz-security-token'
                    ],
                    'AllowMethods': ['POST', 'OPTIONS'],
                    'AllowOrigins': [
                        'https://localhost:8501',
                        'https://*.streamlit.app',
                        'https://*.herokuapp.com',
                        '*'  # Allow all origins for testing
                    ],
                    'MaxAge': 300
                }
            )
            
            self.log_fix(
                "Updated Function URL Auth Type",
                "Set auth type to NONE and updated CORS configuration"
            )
            
            return True
            
        except Exception as e:
            self.log_issue("Auth Type Fix Error", str(e))
            return False
    
    def run_comprehensive_diagnosis(self) -> Dict:
        """Run comprehensive diagnosis and fix attempts."""
        print("🔍 Starting Lambda Function URL Diagnosis...")
        print(f"📅 Diagnosis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Function URL: {self.function_url}")
        print("=" * 70)
        
        if not self.config:
            return {'success': False, 'error': 'Configuration not available'}
        
        # Step 1: Test current access
        access_works = self.test_function_url_access()
        
        if access_works:
            print("\n✅ Function URL is working correctly!")
            return {'success': True, 'message': 'No issues found'}
        
        # Step 2: Check configurations
        url_config_ok = self.check_function_url_config()
        function_status_ok = self.check_lambda_function_status()
        iam_ok = self.check_iam_permissions()
        resource_policy_ok = self.check_function_url_resource_policy()
        
        # Step 3: Apply fixes
        fixes_successful = 0
        total_fixes = 0
        
        if not resource_policy_ok:
            total_fixes += 1
            if self.fix_function_url_permissions():
                fixes_successful += 1
        
        if not url_config_ok:
            total_fixes += 1
            if self.fix_function_url_auth_type():
                fixes_successful += 1
        
        # Step 4: Test again after fixes
        if total_fixes > 0:
            print(f"\n🔄 Applied {fixes_successful}/{total_fixes} fixes. Testing again...")
            time.sleep(10)  # Wait for changes to propagate
            
            final_test = self.test_function_url_access()
            
            if final_test:
                print("\n🎉 Function URL is now working after fixes!")
                return {'success': True, 'fixes_applied': fixes_successful}
        
        # Generate summary
        summary = {
            'success': False,
            'issues_found': len(self.issues_found),
            'fixes_applied': len(self.fixes_applied),
            'issues': self.issues_found,
            'fixes': self.fixes_applied
        }
        
        self.print_diagnosis_summary(summary)
        return summary
    
    def print_diagnosis_summary(self, summary: Dict):
        """Print diagnosis summary."""
        print("\n" + "=" * 70)
        print("📊 LAMBDA FUNCTION URL DIAGNOSIS SUMMARY")
        print("=" * 70)
        
        status = "✅ RESOLVED" if summary['success'] else "❌ ISSUES REMAIN"
        print(f"Status: {status}")
        print(f"Issues Found: {summary['issues_found']}")
        print(f"Fixes Applied: {summary['fixes_applied']}")
        
        if summary['issues']:
            print(f"\n❌ Issues Identified:")
            for issue in summary['issues']:
                print(f"   • {issue['issue']}")
                if issue['details']:
                    print(f"     {issue['details']}")
        
        if summary['fixes']:
            print(f"\n✅ Fixes Applied:")
            for fix in summary['fixes']:
                print(f"   • {fix['fix']}")
                if fix['details']:
                    print(f"     {fix['details']}")
        
        if not summary['success']:
            print(f"\n🔧 Manual Steps Required:")
            print("   1. Check AWS credentials and permissions")
            print("   2. Verify Lambda function is deployed correctly")
            print("   3. Ensure Function URL is configured with AuthType=NONE")
            print("   4. Add resource-based policy for public access")
            print("   5. Check CloudWatch logs for detailed errors")
        
        print("\n" + "=" * 70)

def main():
    """Main diagnostic function."""
    diagnostic = LambdaPermissionDiagnostic()
    results = diagnostic.run_comprehensive_diagnosis()
    
    import sys
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()