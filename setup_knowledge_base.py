#!/usr/bin/env python3
"""
Bedrock Knowledge Base Setup Script

This script provides a comprehensive setup process for creating a Bedrock Knowledge Base.
It includes credential checking, configuration validation, and step-by-step execution.

Requirements: 1.1, 1.2, 6.1, 6.5
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List

def check_aws_credentials() -> bool:
    """Check if AWS credentials are properly configured."""
    print("🔐 Checking AWS credentials...")
    
    # Check for AWS credentials in environment variables
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
    
    # Check for AWS profile
    aws_profile = os.environ.get('AWS_PROFILE')
    
    # Check for credentials file
    credentials_file = os.path.expanduser('~/.aws/credentials')
    config_file = os.path.expanduser('~/.aws/config')
    
    has_env_creds = aws_access_key and aws_secret_key
    has_profile = aws_profile is not None
    has_cred_file = os.path.exists(credentials_file)
    has_config_file = os.path.exists(config_file)
    
    print(f"   Environment credentials: {'✅' if has_env_creds else '❌'}")
    print(f"   AWS Profile set: {'✅' if has_profile else '❌'}")
    print(f"   Credentials file: {'✅' if has_cred_file else '❌'}")
    print(f"   Config file: {'✅' if has_config_file else '❌'}")
    
    if has_env_creds or has_profile or has_cred_file:
        print("✅ AWS credentials found")
        return True
    else:
        print("❌ No AWS credentials found")
        return False

def validate_configuration() -> Dict[str, Any]:
    """Validate the configuration files."""
    print("\n📋 Validating configuration files...")
    
    config_file = "config/aws_config.json"
    policies_file = "config/iam_policies.json"
    
    validation_results = {
        'config_exists': False,
        'policies_exist': False,
        'config_valid': False,
        'policies_valid': False,
        'config_data': None,
        'policies_data': None
    }
    
    # Check config file
    if os.path.exists(config_file):
        validation_results['config_exists'] = True
        print(f"✅ Configuration file found: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            validation_results['config_valid'] = True
            validation_results['config_data'] = config_data
            print("✅ Configuration file is valid JSON")
        except json.JSONDecodeError as e:
            print(f"❌ Configuration file has invalid JSON: {e}")
    else:
        print(f"❌ Configuration file not found: {config_file}")
    
    # Check policies file
    if os.path.exists(policies_file):
        validation_results['policies_exist'] = True
        print(f"✅ Policies file found: {policies_file}")
        
        try:
            with open(policies_file, 'r') as f:
                policies_data = json.load(f)
            validation_results['policies_valid'] = True
            validation_results['policies_data'] = policies_data
            print("✅ Policies file is valid JSON")
        except json.JSONDecodeError as e:
            print(f"❌ Policies file has invalid JSON: {e}")
    else:
        print(f"❌ Policies file not found: {policies_file}")
    
    return validation_results

def check_s3_access(config_data: Dict[str, Any]) -> bool:
    """Check if S3 access is properly configured."""
    print("\n📁 Checking S3 access configuration...")
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Get S3 configuration
        s3_config = config_data.get('s3', {}).get('data_bucket', {})
        bucket_name = s3_config.get('name')
        
        if not bucket_name:
            print("❌ S3 bucket name not found in configuration")
            return False
        
        print(f"🔍 Testing access to bucket: {bucket_name}")
        
        # Test S3 access
        s3_client = boto3.client('s3', region_name=config_data.get('region', 'us-west-2'))
        
        # Try to list objects in the bucket
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=s3_config.get('data_structure', {}).get('base_prefix', ''),
            MaxKeys=1
        )
        
        object_count = response.get('KeyCount', 0)
        print(f"✅ S3 access successful. Found {object_count} objects with prefix")
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not configured for S3 access")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ S3 bucket '{bucket_name}' does not exist")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to S3 bucket '{bucket_name}'")
        else:
            print(f"❌ S3 access error: {e}")
        return False
    except ImportError:
        print("❌ boto3 not installed. Run: pip install boto3")
        return False
    except Exception as e:
        print(f"❌ Unexpected error checking S3 access: {e}")
        return False

def check_bedrock_permissions(region: str) -> bool:
    """Check if Bedrock permissions are available."""
    print("\n🧠 Checking Bedrock service permissions...")
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Test Bedrock Agent access
        bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        
        # Try to list knowledge bases (this requires minimal permissions)
        try:
            response = bedrock_agent.list_knowledge_bases(maxResults=1)
            print("✅ Bedrock Agent access successful")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                print("❌ Access denied to Bedrock Agent service")
            elif error_code == 'UnauthorizedOperation':
                print("❌ Unauthorized to access Bedrock Agent")
            else:
                print(f"❌ Bedrock Agent error: {e}")
            return False
            
    except NoCredentialsError:
        print("❌ AWS credentials not configured for Bedrock access")
        return False
    except ImportError:
        print("❌ boto3 not installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error checking Bedrock permissions: {e}")
        return False

def generate_setup_commands(config_data: Dict[str, Any]) -> List[str]:
    """Generate the setup commands for Knowledge Base creation."""
    commands = []
    
    # IAM role creation
    role_name = config_data.get('iam', {}).get('knowledge_base_role', 'bedrock-knowledge-base-role')
    commands.append(f"# Create IAM role for Knowledge Base")
    commands.append(f"aws iam create-role --role-name {role_name} --assume-role-policy-document file://trust-policy.json")
    commands.append(f"aws iam put-role-policy --role-name {role_name} --policy-name {role_name}-policy --policy-document file://kb-permissions.json")
    
    # Knowledge Base creation
    kb_name = config_data.get('bedrock', {}).get('knowledge_base', {}).get('name', 'maintenance-fault-data-kb')
    commands.append(f"\n# Create Knowledge Base")
    commands.append(f"aws bedrock-agent create-knowledge-base --name {kb_name} --role-arn arn:aws:iam::ACCOUNT_ID:role/{role_name}")
    
    # Data source creation
    bucket_name = config_data.get('s3', {}).get('data_bucket', {}).get('name', 'your-bucket')
    commands.append(f"\n# Create data source")
    commands.append(f"aws bedrock-agent create-data-source --knowledge-base-id KB_ID --name s3-fault-data --data-source-configuration file://data-source-config.json")
    
    return commands

def create_policy_files(policies_data: Dict[str, Any], config_data: Dict[str, Any]):
    """Create the necessary policy files for AWS CLI commands."""
    print("\n📄 Creating policy files for AWS CLI...")
    
    # Trust policy for Bedrock service
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    with open('trust-policy.json', 'w') as f:
        json.dump(trust_policy, f, indent=2)
    print("✅ Created trust-policy.json")
    
    # Knowledge Base permissions policy
    kb_policy = policies_data.get('knowledge_base_policy', {})
    with open('kb-permissions.json', 'w') as f:
        json.dump(kb_policy, f, indent=2)
    print("✅ Created kb-permissions.json")
    
    # Data source configuration
    s3_config = config_data.get('s3', {}).get('data_bucket', {})
    bucket_name = s3_config.get('name', 'your-bucket')
    base_prefix = s3_config.get('data_structure', {}).get('base_prefix', '')
    
    data_source_config = {
        "type": "S3",
        "s3Configuration": {
            "bucketArn": f"arn:aws:s3:::{bucket_name}",
            "inclusionPrefixes": [base_prefix]
        }
    }
    
    with open('data-source-config.json', 'w') as f:
        json.dump(data_source_config, f, indent=2)
    print("✅ Created data-source-config.json")

def print_manual_setup_instructions(config_data: Dict[str, Any]):
    """Print manual setup instructions."""
    print("\n" + "=" * 60)
    print("📋 MANUAL SETUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1. 🔐 Configure AWS Credentials:")
    print("   aws configure")
    print("   # OR set environment variables:")
    print("   export AWS_ACCESS_KEY_ID=your_access_key")
    print("   export AWS_SECRET_ACCESS_KEY=your_secret_key")
    print("   export AWS_DEFAULT_REGION=us-west-2")
    
    print("\n2. 🧠 Enable Bedrock Model Access:")
    print("   - Go to AWS Console > Bedrock > Model access")
    print("   - Request access to:")
    print("     • Amazon Titan Embed Text v1 (for embeddings)")
    print("     • Anthropic Claude 3 Sonnet (for agent)")
    
    print("\n3. 📁 Verify S3 Data Access:")
    bucket_name = config_data.get('s3', {}).get('data_bucket', {}).get('name', 'your-bucket')
    prefix = config_data.get('s3', {}).get('data_bucket', {}).get('data_structure', {}).get('base_prefix', '')
    print(f"   aws s3 ls s3://{bucket_name}/{prefix}")
    
    print("\n4. 🚀 Run Knowledge Base Creation:")
    print("   python3 create_knowledge_base.py")
    
    print("\n5. 🧪 Test Knowledge Base:")
    print("   python3 test_knowledge_base.py")

def main():
    """Main setup validation and instruction function."""
    print("Bedrock Knowledge Base Setup Validator")
    print("=" * 50)
    
    # Step 1: Check AWS credentials
    has_credentials = check_aws_credentials()
    
    # Step 2: Validate configuration
    validation = validate_configuration()
    
    if not validation['config_valid'] or not validation['policies_valid']:
        print("\n❌ Configuration validation failed. Please fix configuration files.")
        return 1
    
    config_data = validation['config_data']
    policies_data = validation['policies_data']
    
    # Step 3: Check S3 access (only if credentials available)
    s3_access = False
    if has_credentials:
        s3_access = check_s3_access(config_data)
    
    # Step 4: Check Bedrock permissions (only if credentials available)
    bedrock_access = False
    if has_credentials:
        bedrock_access = check_bedrock_permissions(config_data.get('region', 'us-west-2'))
    
    # Step 5: Generate setup files
    create_policy_files(policies_data, config_data)
    
    # Summary and next steps
    print("\n" + "=" * 60)
    print("📊 SETUP VALIDATION SUMMARY")
    print("=" * 60)
    
    print(f"AWS Credentials: {'✅' if has_credentials else '❌'}")
    print(f"Configuration Files: {'✅' if validation['config_valid'] and validation['policies_valid'] else '❌'}")
    print(f"S3 Access: {'✅' if s3_access else '❌' if has_credentials else '⏳ Not tested'}")
    print(f"Bedrock Access: {'✅' if bedrock_access else '❌' if has_credentials else '⏳ Not tested'}")
    
    if has_credentials and s3_access and bedrock_access:
        print("\n🎉 All checks passed! Ready to create Knowledge Base.")
        print("\nNext steps:")
        print("1. Run: python3 create_knowledge_base.py")
        print("2. Test: python3 test_knowledge_base.py")
        return 0
    else:
        print_manual_setup_instructions(config_data)
        return 1

if __name__ == "__main__":
    sys.exit(main())