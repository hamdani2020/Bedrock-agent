#!/usr/bin/env python3
"""
AWS Setup Validation Script

This script validates AWS credentials and permissions required for Bedrock Agent setup.
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_aws_credentials():
    """Validate AWS credentials"""
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        
        logger.info("✅ AWS Credentials Valid")
        logger.info(f"Account ID: {identity['Account']}")
        logger.info(f"User ARN: {identity['Arn']}")
        return True
        
    except NoCredentialsError:
        logger.error("❌ No AWS credentials found")
        logger.error("Please configure AWS credentials using:")
        logger.error("  aws configure")
        logger.error("  or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return False
        
    except ClientError as e:
        logger.error(f"❌ AWS credentials invalid: {e}")
        return False

def validate_bedrock_access():
    """Validate Bedrock service access"""
    try:
        bedrock_client = boto3.client('bedrock', region_name='us-west-2')
        
        # Try to list foundation models
        response = bedrock_client.list_foundation_models()
        logger.info("✅ Bedrock service access validated")
        
        # Check for required models
        models = response.get('modelSummaries', [])
        required_models = [
            'anthropic.claude-3-sonnet-20240229-v1:0',
            'amazon.titan-embed-text-v1'
        ]
        
        available_models = [model['modelId'] for model in models]
        
        for model in required_models:
            if model in available_models:
                logger.info(f"✅ Model available: {model}")
            else:
                logger.warning(f"⚠️  Model not found: {model}")
        
        return True
        
    except ClientError as e:
        if 'AccessDenied' in str(e):
            logger.error("❌ Access denied to Bedrock service")
            logger.error("Please ensure your AWS user/role has Bedrock permissions")
        else:
            logger.error(f"❌ Bedrock access validation failed: {e}")
        return False

def validate_bedrock_agent_access():
    """Validate Bedrock Agent service access"""
    try:
        bedrock_agent_client = boto3.client('bedrock-agent', region_name='us-west-2')
        
        # Try to list agents
        response = bedrock_agent_client.list_agents()
        logger.info("✅ Bedrock Agent service access validated")
        return True
        
    except ClientError as e:
        if 'AccessDenied' in str(e):
            logger.error("❌ Access denied to Bedrock Agent service")
            logger.error("Please ensure your AWS user/role has Bedrock Agent permissions")
        else:
            logger.error(f"❌ Bedrock Agent access validation failed: {e}")
        return False

def validate_iam_permissions():
    """Validate IAM permissions for role creation"""
    try:
        iam_client = boto3.client('iam')
        
        # Try to list roles (basic IAM read permission)
        iam_client.list_roles(MaxItems=1)
        logger.info("✅ IAM read access validated")
        
        # Note: We can't easily test IAM write permissions without actually creating something
        logger.info("ℹ️  IAM write permissions will be tested during agent creation")
        return True
        
    except ClientError as e:
        if 'AccessDenied' in str(e):
            logger.error("❌ Access denied to IAM service")
            logger.error("Please ensure your AWS user/role has IAM permissions")
        else:
            logger.error(f"❌ IAM access validation failed: {e}")
        return False

def validate_knowledge_base_exists():
    """Check if Knowledge Base exists"""
    try:
        with open('config/aws_config.json', 'r') as f:
            config = json.load(f)
        
        kb_id = config['lambda_functions']['data_sync']['environment_variables'].get('KNOWLEDGE_BASE_ID')
        
        if not kb_id:
            logger.warning("⚠️  Knowledge Base ID not found in configuration")
            logger.warning("Please run create_knowledge_base.py first")
            return False
        
        # Validate Knowledge Base exists
        bedrock_agent_client = boto3.client('bedrock-agent', region_name='us-west-2')
        
        try:
            kb_response = bedrock_agent_client.get_knowledge_base(knowledgeBaseId=kb_id)
            logger.info(f"✅ Knowledge Base found: {kb_id}")
            logger.info(f"Status: {kb_response['knowledgeBase']['status']}")
            return True
            
        except ClientError as e:
            if 'ResourceNotFoundException' in str(e):
                logger.error(f"❌ Knowledge Base {kb_id} not found")
                logger.error("Please run create_knowledge_base.py first")
            else:
                logger.error(f"❌ Knowledge Base validation failed: {e}")
            return False
        
    except FileNotFoundError:
        logger.error("❌ Configuration file not found: config/aws_config.json")
        return False
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON in configuration file")
        return False

def main():
    """Main validation function"""
    logger.info("AWS Setup Validation for Bedrock Agent")
    logger.info("=" * 50)
    
    validations = [
        ("AWS Credentials", validate_aws_credentials),
        ("Bedrock Service Access", validate_bedrock_access),
        ("Bedrock Agent Service Access", validate_bedrock_agent_access),
        ("IAM Permissions", validate_iam_permissions),
        ("Knowledge Base Exists", validate_knowledge_base_exists)
    ]
    
    results = {}
    all_passed = True
    
    for name, validation_func in validations:
        logger.info(f"\nValidating: {name}")
        logger.info("-" * 30)
        
        try:
            result = validation_func()
            results[name] = result
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            results[name] = False
            all_passed = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 50)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{name}: {status}")
    
    if all_passed:
        logger.info("\n🎉 All validations passed! Ready to create Bedrock Agent.")
        return 0
    else:
        logger.info("\n⚠️  Some validations failed. Please fix the issues above before proceeding.")
        return 1

if __name__ == "__main__":
    exit(main())