#!/usr/bin/env python3
"""
Complete system deployment script for Bedrock Agent maintenance system.
Deploys Lambda function, configures Function URL, and prepares for Streamlit deployment.
"""

import json
import boto3
import zipfile
import os
import time
import subprocess
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
from botocore.exceptions import ClientError

class SystemDeployer:
    """Complete system deployment manager."""
    
    def __init__(self):
        """Initialize the deployer."""
        self.config = self.load_config()
        self.deployment_log = []
        self.start_time = datetime.now()
        
    def load_config(self) -> Optional[Dict]:
        """Load AWS configuration."""
        try:
            with open('config/aws_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Config file not found: config/aws_config.json")
            return None
    
    def log_step(self, step: str, success: bool, details: str = ""):
        """Log deployment step."""
        self.deployment_log.append({
            'step': step,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        status = "✅" if success else "❌"
        print(f"{status} {step}")
        if details:
            print(f"    {details}")
    
    def create_lambda_package(self) -> str:
        """Create deployment package for Lambda function."""
        print("\n📦 Creating Lambda Deployment Package...")
        
        zip_path = 'lambda_deployment.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add main Lambda function
            zip_file.write('lambda_functions/query_handler/lambda_function.py', 'lambda_function.py')
            
            # Add shared utilities if they exist
            shared_dir = 'lambda_functions/shared'
            if os.path.exists(shared_dir):
                for root, dirs, files in os.walk(shared_dir):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, 'lambda_functions')
                            zip_file.write(file_path, arc_path)
            
            # Add requirements if they exist
            requirements_path = 'lambda_functions/query_handler/requirements.txt'
            if os.path.exists(requirements_path):
                zip_file.write(requirements_path, 'requirements.txt')
        
        self.log_step("Lambda Package Creation", True, f"Created: {zip_path}")
        return zip_path
    
    def ensure_iam_role(self) -> Optional[str]:
        """Ensure IAM role exists with proper permissions."""
        print("\n🔐 Configuring IAM Role...")
        
        try:
            iam = boto3.client('iam')
            role_name = self.config['iam']['lambda_execution_role']
            
            # Check if role exists
            try:
                response = iam.get_role(RoleName=role_name)
                role_arn = response['Role']['Arn']
                self.log_step("IAM Role Check", True, f"Role exists: {role_name}")
                
                # Verify policies are attached
                self.verify_role_policies(iam, role_name)
                return role_arn
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise
            
            # Create role if it doesn't exist
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            response = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Execution role for Bedrock Agent Lambda functions'
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach required policies
            self.attach_role_policies(iam, role_name)
            
            # Wait for role propagation
            time.sleep(10)
            
            self.log_step("IAM Role Creation", True, f"Created: {role_arn}")
            return role_arn
            
        except Exception as e:
            self.log_step("IAM Role Configuration", False, str(e))
            return None
    
    def verify_role_policies(self, iam, role_name: str):
        """Verify required policies are attached to the role."""
        try:
            # Check attached policies
            response = iam.list_attached_role_policies(RoleName=role_name)
            attached_policies = [p['PolicyArn'] for p in response['AttachedPolicies']]
            
            required_aws_policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            ]
            
            missing_policies = [p for p in required_aws_policies if p not in attached_policies]
            
            if missing_policies:
                self.attach_role_policies(iam, role_name)
            
        except Exception as e:
            print(f"    Warning: Could not verify policies: {e}")
    
    def attach_role_policies(self, iam, role_name: str):
        """Attach required policies to the role."""
        # Attach AWS managed policy
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Create and attach Bedrock policy
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent",
                        "bedrock:InvokeModel",
                        "bedrock:GetAgent",
                        "bedrock:GetAgentAlias"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        
        policy_name = f"{role_name}-bedrock-policy"
        
        try:
            # Get account ID for policy ARN
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            
            # Try to create policy (ignore if exists)
            try:
                iam.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(bedrock_policy),
                    Description='Bedrock Agent access policy for Lambda'
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'EntityAlreadyExists':
                    raise
            
            # Attach policy
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            
        except Exception as e:
            print(f"    Warning: Policy attachment issue: {e}")
    
    def deploy_lambda_function(self, zip_path: str, role_arn: str) -> Tuple[bool, Optional[str]]:
        """Deploy or update Lambda function."""
        print("\n⚡ Deploying Lambda Function...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.config['region'])
            function_config = self.config['lambda_functions']['query_handler']
            function_name = function_config['function_name']
            
            # Read deployment package
            with open(zip_path, 'rb') as zip_file:
                zip_content = zip_file.read()
            
            # Check if function exists
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                
                # Update existing function
                lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Runtime=function_config['runtime'],
                    Handler='lambda_function.lambda_handler',
                    Role=role_arn,
                    Timeout=function_config['timeout'],
                    MemorySize=function_config['memory_size'],
                    Environment={'Variables': function_config['environment_variables']}
                )
                
                function_arn = response['Configuration']['FunctionArn']
                self.log_step("Lambda Function Update", True, f"Updated: {function_name}")
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
                
                # Create new function
                response = lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=function_config['runtime'],
                    Role=role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_content},
                    Description='Bedrock Agent query handler',
                    Timeout=function_config['timeout'],
                    MemorySize=function_config['memory_size'],
                    Environment={'Variables': function_config['environment_variables']}
                )
                
                function_arn = response['FunctionArn']
                self.log_step("Lambda Function Creation", True, f"Created: {function_name}")
            
            # Wait for function to be ready
            print("    Waiting for function to be active...")
            waiter = lambda_client.get_waiter('function_active')
            waiter.wait(FunctionName=function_name, WaiterConfig={'Delay': 2, 'MaxAttempts': 30})
            
            return True, function_arn
            
        except Exception as e:
            self.log_step("Lambda Function Deployment", False, str(e))
            return False, None
    
    def configure_function_url(self, function_name: str) -> Optional[str]:
        """Configure Function URL for the Lambda function."""
        print("\n🔗 Configuring Function URL...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.config['region'])
            function_config = self.config['lambda_functions']['query_handler']
            
            # Check if Function URL already exists
            try:
                response = lambda_client.get_function_url_config(FunctionName=function_name)
                function_url = response['FunctionUrl']
                self.log_step("Function URL Check", True, f"URL exists: {function_url}")
                return function_url
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
            
            # Create Function URL
            response = lambda_client.create_function_url_config(
                FunctionName=function_name,
                AuthType=function_config['function_url']['auth_type'],
                Cors=function_config['function_url']['cors']
            )
            
            function_url = response['FunctionUrl']
            self.log_step("Function URL Creation", True, f"Created: {function_url}")
            
            return function_url
            
        except Exception as e:
            self.log_step("Function URL Configuration", False, str(e))
            return None
    
    def test_deployment(self, function_url: str) -> bool:
        """Test the deployed system."""
        print("\n🧪 Testing Deployment...")
        
        try:
            import requests
            
            # Test basic functionality
            test_payload = {
                'query': 'System deployment test - what is the current equipment status?',
                'sessionId': f'deployment-test-{int(time.time())}'
            }
            
            response = requests.post(
                function_url,
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                if response_text and len(response_text) > 10:
                    self.log_step("Deployment Test", True, f"Response: {response_text[:100]}...")
                    return True
                else:
                    self.log_step("Deployment Test", False, "Empty or invalid response")
                    return False
            else:
                self.log_step("Deployment Test", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_step("Deployment Test", False, str(e))
            return False
    
    def prepare_streamlit_deployment(self, function_url: str):
        """Prepare Streamlit app for deployment."""
        print("\n🎨 Preparing Streamlit Deployment...")
        
        try:
            # Update Streamlit app configuration with the Function URL
            app_path = 'streamlit_app/app.py'
            
            if os.path.exists(app_path):
                # Read current app content
                with open(app_path, 'r') as f:
                    app_content = f.read()
                
                # Check if the Function URL is already configured
                if function_url in app_content:
                    self.log_step("Streamlit Configuration", True, "Function URL already configured")
                else:
                    # Update default API endpoint in the app
                    updated_content = app_content.replace(
                        'value="https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"',
                        f'value="{function_url}"'
                    )
                    
                    if updated_content != app_content:
                        with open(app_path, 'w') as f:
                            f.write(updated_content)
                        self.log_step("Streamlit Configuration", True, "Updated Function URL in app")
                    else:
                        self.log_step("Streamlit Configuration", True, "No update needed")
                
                # Create deployment instructions
                self.create_streamlit_deployment_guide(function_url)
                
            else:
                self.log_step("Streamlit Configuration", False, "App file not found")
                
        except Exception as e:
            self.log_step("Streamlit Configuration", False, str(e))
    
    def create_streamlit_deployment_guide(self, function_url: str):
        """Create deployment guide for Streamlit app."""
        guide_content = f"""# Streamlit App Deployment Guide

## Deployment Information
- **Function URL**: {function_url}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Local Testing
To test the Streamlit app locally:

```bash
# Install requirements
pip install -r streamlit_app/requirements.txt

# Run the app
streamlit run streamlit_app/app.py
```

## Deployment Options

### Option 1: Streamlit Cloud (Recommended for Development)
1. Push your code to GitHub
2. Go to https://share.streamlit.io/
3. Connect your GitHub repository
4. Deploy the app from `streamlit_app/app.py`

### Option 2: AWS ECS/Fargate (Production)
1. Create a Dockerfile in the streamlit_app directory
2. Build and push to ECR
3. Deploy using ECS service

### Option 3: Heroku
1. Create a Procfile: `web: streamlit run streamlit_app/app.py --server.port=$PORT --server.address=0.0.0.0`
2. Deploy to Heroku

## Configuration
The app is pre-configured with the Function URL: {function_url}

## Testing Checklist
- [ ] App starts without errors
- [ ] Can connect to Lambda function
- [ ] Chat interface works
- [ ] Responses are received from Bedrock Agent
- [ ] Error handling works properly
- [ ] Session management functions correctly

## Monitoring
- Monitor Lambda function logs in CloudWatch
- Check Function URL metrics
- Monitor Streamlit app performance

## Support
If you encounter issues:
1. Check Lambda function logs in CloudWatch
2. Verify Function URL is accessible
3. Test Lambda function directly using the test script
4. Check CORS configuration if having browser issues
"""
        
        with open('STREAMLIT_DEPLOYMENT_GUIDE.md', 'w') as f:
            f.write(guide_content)
        
        self.log_step("Deployment Guide", True, "Created STREAMLIT_DEPLOYMENT_GUIDE.md")
    
    def deploy_complete_system(self) -> Dict:
        """Deploy the complete system."""
        print("🚀 Starting Complete System Deployment...")
        print(f"📅 Deployment started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.config:
            return {'success': False, 'error': 'Configuration not found'}
        
        deployment_success = True
        function_url = None
        
        try:
            # Step 1: Create Lambda package
            zip_path = self.create_lambda_package()
            
            # Step 2: Ensure IAM role
            role_arn = self.ensure_iam_role()
            if not role_arn:
                deployment_success = False
            
            # Step 3: Deploy Lambda function
            if deployment_success:
                lambda_success, function_arn = self.deploy_lambda_function(zip_path, role_arn)
                if not lambda_success:
                    deployment_success = False
            
            # Step 4: Configure Function URL
            if deployment_success:
                function_name = self.config['lambda_functions']['query_handler']['function_name']
                function_url = self.configure_function_url(function_name)
                if not function_url:
                    deployment_success = False
            
            # Step 5: Test deployment
            if deployment_success and function_url:
                test_success = self.test_deployment(function_url)
                if not test_success:
                    deployment_success = False
            
            # Step 6: Prepare Streamlit deployment
            if deployment_success and function_url:
                self.prepare_streamlit_deployment(function_url)
            
            # Clean up
            if os.path.exists(zip_path):
                os.remove(zip_path)
                print(f"🧹 Cleaned up: {zip_path}")
            
        except Exception as e:
            self.log_step("System Deployment", False, f"Unexpected error: {str(e)}")
            deployment_success = False
        
        # Generate summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        summary = {
            'success': deployment_success,
            'function_url': function_url,
            'duration': duration,
            'deployment_log': self.deployment_log
        }
        
        self.print_deployment_summary(summary)
        return summary
    
    def print_deployment_summary(self, summary: Dict):
        """Print deployment summary."""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        status = "✅ SUCCESS" if summary['success'] else "❌ FAILED"
        print(f"Status: {status}")
        print(f"Duration: {summary['duration']:.2f} seconds")
        
        if summary.get('function_url'):
            print(f"Function URL: {summary['function_url']}")
        
        print("\n📋 Deployment Steps:")
        print("-" * 40)
        
        for step in summary['deployment_log']:
            status_icon = "✅" if step['success'] else "❌"
            print(f"{status_icon} {step['step']}")
            if step['details']:
                print(f"    {step['details']}")
        
        print("\n🎯 Next Steps:")
        if summary['success']:
            print("✅ System deployment completed successfully!")
            print("📝 To complete the setup:")
            print("   1. Review STREAMLIT_DEPLOYMENT_GUIDE.md")
            print("   2. Test the system using test_end_to_end_deployment.py")
            print("   3. Deploy Streamlit app to your chosen platform")
            print("   4. Configure monitoring and alerting")
        else:
            print("⚠️  Deployment failed. Check the errors above and:")
            print("   1. Verify AWS credentials and permissions")
            print("   2. Check Bedrock Agent and Knowledge Base status")
            print("   3. Review CloudWatch logs for detailed errors")
            print("   4. Run the deployment script again after fixing issues")
        
        print("\n" + "=" * 60)

def main():
    """Main deployment function."""
    deployer = SystemDeployer()
    results = deployer.deploy_complete_system()
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()