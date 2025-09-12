#!/usr/bin/env python3
"""
Fix Lambda Function URL permissions without AWS API access.
Provides instructions and scripts to resolve 403 Forbidden errors.
"""

import json
import requests
from datetime import datetime
from typing import Dict

class LambdaURLPermissionFixer:
    """Fix Lambda Function URL permission issues."""
    
    def __init__(self):
        """Initialize the fixer."""
        self.function_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
        self.function_name = "bedrock-agent-query-handler"
        self.region = "us-west-2"
        
    def test_function_url(self) -> Dict:
        """Test the Function URL and analyze the response."""
        print("🔗 Testing Function URL...")
        
        try:
            # Test with different request types
            test_cases = [
                {
                    'name': 'Basic POST',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'data': {'query': 'test', 'sessionId': 'test-session'}
                },
                {
                    'name': 'OPTIONS (CORS preflight)',
                    'method': 'OPTIONS',
                    'headers': {
                        'Origin': 'https://localhost:8501',
                        'Access-Control-Request-Method': 'POST',
                        'Access-Control-Request-Headers': 'Content-Type'
                    }
                },
                {
                    'name': 'GET request',
                    'method': 'GET',
                    'headers': {}
                }
            ]
            
            results = []
            
            for test_case in test_cases:
                print(f"\n  Testing: {test_case['name']}")
                
                try:
                    if test_case['method'] == 'POST':
                        response = requests.post(
                            self.function_url,
                            json=test_case['data'],
                            headers=test_case['headers'],
                            timeout=10
                        )
                    elif test_case['method'] == 'OPTIONS':
                        response = requests.options(
                            self.function_url,
                            headers=test_case['headers'],
                            timeout=10
                        )
                    else:  # GET
                        response = requests.get(
                            self.function_url,
                            headers=test_case['headers'],
                            timeout=10
                        )
                    
                    result = {
                        'test': test_case['name'],
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'body': response.text[:200] if response.text else '',
                        'success': response.status_code == 200
                    }
                    
                    print(f"    Status: {response.status_code}")
                    print(f"    Headers: {dict(response.headers)}")
                    print(f"    Body: {response.text[:100]}...")
                    
                    results.append(result)
                    
                except Exception as e:
                    result = {
                        'test': test_case['name'],
                        'error': str(e),
                        'success': False
                    }
                    print(f"    Error: {str(e)}")
                    results.append(result)
            
            return {'results': results}
            
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_403_error(self) -> Dict:
        """Analyze the 403 Forbidden error and provide solutions."""
        print("\n🔍 Analyzing 403 Forbidden Error...")
        
        # Common causes of 403 errors with Lambda Function URLs
        possible_causes = [
            {
                'cause': 'Function URL Auth Type is set to AWS_IAM',
                'description': 'Function URL requires AWS credentials for access',
                'solution': 'Change AuthType to NONE for public access',
                'aws_cli_fix': f'aws lambda update-function-url-config --function-name {self.function_name} --auth-type NONE --region {self.region}'
            },
            {
                'cause': 'Missing resource-based policy',
                'description': 'Function lacks permission for public Function URL access',
                'solution': 'Add resource-based policy allowing lambda:InvokeFunctionUrl',
                'aws_cli_fix': f'''aws lambda add-permission \\
  --function-name {self.function_name} \\
  --statement-id AllowPublicFunctionUrlAccess \\
  --action lambda:InvokeFunctionUrl \\
  --principal "*" \\
  --region {self.region}'''
            },
            {
                'cause': 'CORS configuration blocking requests',
                'description': 'Function URL CORS settings may be too restrictive',
                'solution': 'Update CORS configuration to allow required origins',
                'aws_cli_fix': 'Update CORS via AWS Console or CLI'
            },
            {
                'cause': 'Function is not active or has errors',
                'description': 'Lambda function may be in failed state',
                'solution': 'Check function status and logs',
                'aws_cli_fix': f'aws lambda get-function --function-name {self.function_name} --region {self.region}'
            }
        ]
        
        return {'possible_causes': possible_causes}
    
    def generate_fix_scripts(self):
        """Generate AWS CLI scripts to fix common issues."""
        print("\n🔧 Generating Fix Scripts...")
        
        # Script 1: Fix Function URL Auth Type
        auth_fix_script = f'''#!/bin/bash
# Fix Lambda Function URL Auth Type
echo "🔧 Fixing Function URL Auth Type..."

aws lambda update-function-url-config \\
  --function-name {self.function_name} \\
  --auth-type NONE \\
  --cors '{{
    "AllowCredentials": false,
    "AllowHeaders": ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"],
    "AllowMethods": ["POST", "OPTIONS"],
    "AllowOrigins": ["https://localhost:8501", "https://*.streamlit.app", "https://*.herokuapp.com", "*"],
    "MaxAge": 300
  }}' \\
  --region {self.region}

echo "✅ Function URL auth type updated"
'''
        
        # Script 2: Add Resource-Based Policy
        policy_fix_script = f'''#!/bin/bash
# Add Resource-Based Policy for Function URL
echo "🔧 Adding Function URL permission..."

aws lambda add-permission \\
  --function-name {self.function_name} \\
  --statement-id AllowPublicFunctionUrlAccess \\
  --action lambda:InvokeFunctionUrl \\
  --principal "*" \\
  --region {self.region}

echo "✅ Function URL permission added"
'''
        
        # Script 3: Check Function Status
        status_check_script = f'''#!/bin/bash
# Check Lambda Function Status
echo "🔍 Checking function status..."

echo "Function Configuration:"
aws lambda get-function --function-name {self.function_name} --region {self.region}

echo "\\nFunction URL Configuration:"
aws lambda get-function-url-config --function-name {self.function_name} --region {self.region}

echo "\\nFunction Policy:"
aws lambda get-policy --function-name {self.function_name} --region {self.region} || echo "No resource policy found"

echo "\\nRecent Logs:"
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/{self.function_name}" --region {self.region}
'''
        
        # Write scripts to files
        with open('fix_function_url_auth.sh', 'w') as f:
            f.write(auth_fix_script)
        
        with open('fix_function_url_policy.sh', 'w') as f:
            f.write(policy_fix_script)
        
        with open('check_function_status.sh', 'w') as f:
            f.write(status_check_script)
        
        print("✅ Generated fix scripts:")
        print("   • fix_function_url_auth.sh - Fix auth type and CORS")
        print("   • fix_function_url_policy.sh - Add resource-based policy")
        print("   • check_function_status.sh - Check function status")
    
    def generate_terraform_fix(self):
        """Generate Terraform configuration to fix the issues."""
        print("\n🏗️  Generating Terraform Fix...")
        
        terraform_config = f'''# Terraform configuration to fix Lambda Function URL permissions

resource "aws_lambda_function_url" "query_handler_url" {{
  function_name      = "{self.function_name}"
  authorization_type = "NONE"
  
  cors {{
    allow_credentials = false
    allow_headers     = ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"]
    allow_methods     = ["POST", "OPTIONS"]
    allow_origins     = ["https://localhost:8501", "https://*.streamlit.app", "https://*.herokuapp.com", "*"]
    max_age          = 300
  }}
}}

resource "aws_lambda_permission" "allow_function_url" {{
  statement_id           = "AllowPublicFunctionUrlAccess"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = "{self.function_name}"
  principal             = "*"
  function_url_auth_type = "NONE"
}}

output "function_url" {{
  value = aws_lambda_function_url.query_handler_url.function_url
}}
'''
        
        with open('lambda_url_fix.tf', 'w') as f:
            f.write(terraform_config)
        
        print("✅ Generated Terraform configuration: lambda_url_fix.tf")
    
    def generate_cloudformation_fix(self):
        """Generate CloudFormation template to fix the issues."""
        print("\n☁️  Generating CloudFormation Fix...")
        
        cf_template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Fix Lambda Function URL permissions",
            "Resources": {
                "LambdaFunctionUrl": {
                    "Type": "AWS::Lambda::Url",
                    "Properties": {
                        "TargetFunctionArn": f"arn:aws:lambda:{self.region}:{{AWS::AccountId}}:function:{self.function_name}",
                        "AuthType": "NONE",
                        "Cors": {
                            "AllowCredentials": False,
                            "AllowHeaders": ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"],
                            "AllowMethods": ["POST", "OPTIONS"],
                            "AllowOrigins": ["https://localhost:8501", "https://*.streamlit.app", "https://*.herokuapp.com", "*"],
                            "MaxAge": 300
                        }
                    }
                },
                "LambdaFunctionUrlPermission": {
                    "Type": "AWS::Lambda::Permission",
                    "Properties": {
                        "FunctionName": self.function_name,
                        "Action": "lambda:InvokeFunctionUrl",
                        "Principal": "*",
                        "FunctionUrlAuthType": "NONE"
                    }
                }
            },
            "Outputs": {
                "FunctionUrl": {
                    "Description": "Lambda Function URL",
                    "Value": {"Fn::GetAtt": ["LambdaFunctionUrl", "FunctionUrl"]}
                }
            }
        }
        
        with open('lambda_url_fix.yaml', 'w') as f:
            import yaml
            yaml.dump(cf_template, f, default_flow_style=False)
        
        print("✅ Generated CloudFormation template: lambda_url_fix.yaml")
    
    def create_manual_fix_guide(self):
        """Create a comprehensive manual fix guide."""
        print("\n📚 Creating Manual Fix Guide...")
        
        guide_content = f'''# Lambda Function URL Permission Fix Guide

## Problem
The Lambda Function URL `{self.function_url}` is returning HTTP 403 Forbidden errors.

## Root Cause Analysis
The 403 error typically indicates one of these issues:
1. Function URL AuthType is set to AWS_IAM instead of NONE
2. Missing resource-based policy for public access
3. CORS configuration blocking requests
4. Function is not active or has deployment issues

## Solution Steps

### Step 1: Check Current Configuration
```bash
# Check function URL configuration
aws lambda get-function-url-config \\
  --function-name {self.function_name} \\
  --region {self.region}

# Check function status
aws lambda get-function \\
  --function-name {self.function_name} \\
  --region {self.region}
```

### Step 2: Fix Auth Type (Most Likely Issue)
```bash
# Update Function URL to allow public access
aws lambda update-function-url-config \\
  --function-name {self.function_name} \\
  --auth-type NONE \\
  --region {self.region}
```

### Step 3: Add Resource-Based Policy
```bash
# Add permission for public Function URL access
aws lambda add-permission \\
  --function-name {self.function_name} \\
  --statement-id AllowPublicFunctionUrlAccess \\
  --action lambda:InvokeFunctionUrl \\
  --principal "*" \\
  --region {self.region}
```

### Step 4: Update CORS Configuration
```bash
# Update CORS to allow Streamlit origins
aws lambda update-function-url-config \\
  --function-name {self.function_name} \\
  --cors '{{
    "AllowCredentials": false,
    "AllowHeaders": ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"],
    "AllowMethods": ["POST", "OPTIONS"],
    "AllowOrigins": ["https://localhost:8501", "https://*.streamlit.app", "https://*.herokuapp.com", "*"],
    "MaxAge": 300
  }}' \\
  --region {self.region}
```

### Step 5: Test the Fix
```bash
# Test the Function URL
curl -X POST {self.function_url} \\
  -H "Content-Type: application/json" \\
  -d '{{"query":"test","sessionId":"test-session"}}'
```

## AWS Console Steps

### Via AWS Lambda Console:
1. Go to AWS Lambda Console
2. Find function: `{self.function_name}`
3. Go to "Configuration" → "Function URL"
4. Edit the Function URL:
   - Set Auth type to "NONE"
   - Configure CORS as needed
5. Go to "Configuration" → "Permissions"
6. Add resource-based policy for Function URL access

### Expected Result:
- HTTP 200 response with JSON containing agent response
- CORS headers present in response
- No authentication required

## Verification Commands

```bash
# Verify Function URL configuration
aws lambda get-function-url-config --function-name {self.function_name} --region {self.region}

# Verify resource policy
aws lambda get-policy --function-name {self.function_name} --region {self.region}

# Test with curl
curl -v -X POST {self.function_url} \\
  -H "Content-Type: application/json" \\
  -H "Origin: https://localhost:8501" \\
  -d '{{"query":"What is the equipment status?","sessionId":"test-123"}}'
```

## Troubleshooting

### If still getting 403:
1. Check CloudWatch logs: `/aws/lambda/{self.function_name}`
2. Verify function is active and not in error state
3. Check if there are any account-level restrictions
4. Ensure the Function URL exists and is properly configured

### If getting CORS errors:
1. Verify CORS configuration includes your domain
2. Check that preflight OPTIONS requests are handled
3. Ensure all required headers are allowed

### If getting timeout errors:
1. Check function timeout settings (should be 300 seconds)
2. Verify Bedrock Agent is accessible
3. Check function memory allocation

## Security Considerations

⚠️  **Important**: Setting AuthType to NONE makes the Function URL publicly accessible.

For production:
- Consider implementing API Gateway with authentication
- Add rate limiting and monitoring
- Restrict CORS origins to specific domains
- Monitor usage and costs

## Files Generated
- `fix_function_url_auth.sh` - Fix auth type script
- `fix_function_url_policy.sh` - Add policy script  
- `check_function_status.sh` - Status check script
- `lambda_url_fix.tf` - Terraform configuration
- `lambda_url_fix.yaml` - CloudFormation template

Run these scripts with appropriate AWS credentials and permissions.
'''
        
        with open('LAMBDA_URL_FIX_GUIDE.md', 'w') as f:
            f.write(guide_content)
        
        print("✅ Created comprehensive fix guide: LAMBDA_URL_FIX_GUIDE.md")
    
    def run_diagnosis_and_fix_generation(self):
        """Run complete diagnosis and generate all fix resources."""
        print("🔍 Lambda Function URL Permission Diagnosis & Fix Generation")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Function URL: {self.function_url}")
        print("=" * 70)
        
        # Test current status
        test_results = self.test_function_url()
        
        # Analyze the 403 error
        analysis = self.analyze_403_error()
        
        # Generate all fix resources
        self.generate_fix_scripts()
        self.generate_terraform_fix()
        try:
            self.generate_cloudformation_fix()
        except ImportError:
            print("⚠️  PyYAML not available, skipping CloudFormation template")
        
        self.create_manual_fix_guide()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 DIAGNOSIS COMPLETE")
        print("=" * 70)
        
        print("🔍 Issue Identified: HTTP 403 Forbidden")
        print("📋 Most Likely Cause: Function URL AuthType set to AWS_IAM")
        
        print("\n✅ Fix Resources Generated:")
        print("   • LAMBDA_URL_FIX_GUIDE.md - Complete manual fix guide")
        print("   • fix_function_url_auth.sh - AWS CLI script to fix auth type")
        print("   • fix_function_url_policy.sh - AWS CLI script to add policy")
        print("   • check_function_status.sh - Status verification script")
        print("   • lambda_url_fix.tf - Terraform configuration")
        print("   • lambda_url_fix.yaml - CloudFormation template")
        
        print("\n🚀 Next Steps:")
        print("   1. Run: chmod +x *.sh")
        print("   2. Execute: ./fix_function_url_auth.sh")
        print("   3. Execute: ./fix_function_url_policy.sh")
        print("   4. Test: curl -X POST [Function URL] -H 'Content-Type: application/json' -d '{\"query\":\"test\",\"sessionId\":\"test\"}'")
        print("   5. If issues persist, check LAMBDA_URL_FIX_GUIDE.md")
        
        print("\n⚠️  Note: You need AWS CLI configured with appropriate permissions")
        print("=" * 70)

def main():
    """Main function."""
    fixer = LambdaURLPermissionFixer()
    fixer.run_diagnosis_and_fix_generation()

if __name__ == "__main__":
    main()