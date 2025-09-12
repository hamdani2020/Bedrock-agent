#!/usr/bin/env python3
"""
Create Knowledge Base with Amazon OpenSearch Service

This script creates a Bedrock Knowledge Base using Amazon OpenSearch Service
(managed service, not serverless).
"""

import json
import boto3
from botocore.exceptions import ClientError

def create_opensearch_managed_kb():
    """Create Knowledge Base with Amazon OpenSearch Service"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    sts = boto3.client('sts', region_name=region)
    
    # Get account ID
    account_id = sts.get_caller_identity()['Account']
    
    # IAM role ARN
    role_arn = f"arn:aws:iam::{account_id}:role/bedrock-knowledge-base-role"
    
    try:
        print("🔄 Creating Knowledge Base with Amazon OpenSearch Service...")
        
        # Knowledge Base configuration
        kb_config = {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
            }
        }
        
        # OpenSearch Service configuration (not serverless)
        storage_config = {
            "type": "OPENSEARCH_SERVICE",
            "opensearchServiceConfiguration": {
                "clusterArn": f"arn:aws:es:{region}:{account_id}:domain/bedrock-kb-domain",
                "vectorIndexName": "maintenance-data-index",
                "fieldMapping": {
                    "vectorField": "vector_field",
                    "textField": "text_field",
                    "metadataField": "metadata_field"
                }
            }
        }
        
        # Create Knowledge Base
        response = bedrock_agent.create_knowledge_base(
            name="maintenance-fault-kb",
            description="Knowledge base for maintenance fault data",
            roleArn=role_arn,
            knowledgeBaseConfiguration=kb_config,
            storageConfiguration=storage_config
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Created Knowledge Base: {kb_id}")
        return kb_id
        
    except ClientError as e:
        print(f"❌ Failed to create Knowledge Base: {e}")
        return None

def main():
    """Main execution function"""
    try:
        print("ℹ️  This will test OpenSearch Service configuration")
        kb_id = create_opensearch_managed_kb()
        return 0 if kb_id else 1
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())