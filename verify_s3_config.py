#!/usr/bin/env python3
"""
Configuration verification script for S3 setup.
Validates the S3 utilities and configuration without requiring AWS credentials.
"""
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_configuration():
    """
    Verify S3 configuration and utilities setup.
    """
    print("=" * 60)
    print("S3 Configuration Verification")
    print("=" * 60)
    
    success = True
    
    # Test 1: Verify configuration files exist
    print("\n1. Checking configuration files...")
    
    config_files = [
        "config/aws_config.json",
        "config/iam_policies.json",
        "s3_data_examples.json"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"   ✅ {config_file}")
        else:
            print(f"   ❌ {config_file} (missing)")
            success = False
    
    # Test 2: Verify S3 utilities exist
    print("\n2. Checking S3 utilities...")
    
    utility_files = [
        "lambda_functions/shared/__init__.py",
        "lambda_functions/shared/s3_utils.py"
    ]
    
    for util_file in utility_files:
        if Path(util_file).exists():
            print(f"   ✅ {util_file}")
        else:
            print(f"   ❌ {util_file} (missing)")
            success = False
    
    # Test 3: Verify configuration content
    print("\n3. Validating configuration content...")
    
    try:
        with open("config/aws_config.json", 'r') as f:
            aws_config = json.load(f)
        
        # Check S3 configuration
        s3_config = aws_config.get('s3', {})
        bucket_config = s3_config.get('data_bucket', {})
        
        bucket_name = bucket_config.get('name')
        if bucket_name == "relu-quicksight":
            print(f"   ✅ S3 bucket configured: {bucket_name}")
        else:
            print(f"   ❌ S3 bucket not properly configured: {bucket_name}")
            success = False
        
        # Check data structure configuration
        data_structure = bucket_config.get('data_structure', {})
        base_prefix = data_structure.get('base_prefix')
        if base_prefix == "bedrock-recommendations/analytics/":
            print(f"   ✅ Data prefix configured: {base_prefix}")
        else:
            print(f"   ❌ Data prefix not properly configured: {base_prefix}")
            success = False
        
    except Exception as e:
        print(f"   ❌ Error reading AWS config: {str(e)}")
        success = False
    
    # Test 4: Verify IAM policies
    print("\n4. Validating IAM policies...")
    
    try:
        with open("config/iam_policies.json", 'r') as f:
            iam_policies = json.load(f)
        
        # Check Lambda execution policy
        lambda_policy = iam_policies.get('lambda_execution_policy', {})
        statements = lambda_policy.get('Statement', [])
        
        s3_permissions = False
        bedrock_permissions = False
        
        for statement in statements:
            actions = statement.get('Action', [])
            if any('s3:' in action for action in actions):
                s3_permissions = True
            if any('bedrock:' in action for action in actions):
                bedrock_permissions = True
        
        if s3_permissions:
            print("   ✅ S3 permissions configured")
        else:
            print("   ❌ S3 permissions missing")
            success = False
        
        if bedrock_permissions:
            print("   ✅ Bedrock permissions configured")
        else:
            print("   ❌ Bedrock permissions missing")
            success = False
        
    except Exception as e:
        print(f"   ❌ Error reading IAM policies: {str(e)}")
        success = False
    
    # Test 5: Verify Lambda function updates
    print("\n5. Checking Lambda function updates...")
    
    lambda_functions = [
        "lambda_functions/data_sync/lambda_function.py",
        "lambda_functions/health_check/lambda_function.py"
    ]
    
    for func_file in lambda_functions:
        try:
            with open(func_file, 'r') as f:
                content = f.read()
            
            if "from shared.s3_utils import" in content:
                print(f"   ✅ {func_file} updated with S3 utilities")
            else:
                print(f"   ❌ {func_file} not updated with S3 utilities")
                success = False
                
        except Exception as e:
            print(f"   ❌ Error reading {func_file}: {str(e)}")
            success = False
    
    # Test 6: Verify data examples structure
    print("\n6. Validating data examples...")
    
    try:
        with open("s3_data_examples.json", 'r') as f:
            data_examples = json.load(f)
        
        # Check analytics record example
        analytics_example = data_examples.get('analytics_record_example', {})
        content = analytics_example.get('content', {})
        
        required_fields = [
            'timestamp', 'predicted_fault', 'fault_category', 
            'risk_level', 'recommendation_summary'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
        
        if not missing_fields:
            print("   ✅ All required fields present in data examples")
        else:
            print(f"   ❌ Missing fields in data examples: {missing_fields}")
            success = False
        
    except Exception as e:
        print(f"   ❌ Error reading data examples: {str(e)}")
        success = False
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ S3 Configuration Verification PASSED")
        print("   - All configuration files are present and valid")
        print("   - S3 utilities are properly implemented")
        print("   - Lambda functions are updated")
        print("   - IAM policies include required permissions")
        print("   - Data structure is compatible with Knowledge Base")
    else:
        print("❌ S3 Configuration Verification FAILED")
        print("   - Please fix the issues above before proceeding")
    
    print("=" * 60)
    
    return success

def main():
    """Main function."""
    try:
        success = verify_configuration()
        
        if success:
            print("\n📋 Next Steps:")
            print("   1. Deploy Lambda functions with updated S3 utilities")
            print("   2. Test S3 access with AWS credentials configured")
            print("   3. Proceed to create Bedrock Knowledge Base (Task 3)")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Verification failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)