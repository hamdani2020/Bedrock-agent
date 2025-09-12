#!/usr/bin/env python3
"""
Simple Knowledge Base Creation

This script creates a minimal Bedrock Knowledge Base for testing.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

def create_simple_knowledge_base():
    """Create a simple Knowledge Base"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    sts = boto3.client('sts', region_name=region)
    
    # Get account ID
    account_id = sts.get_caller_identity()['Account']
    
    # Get the OpenSearch collection ARN
    opensearch_client = boto3.client('opensearchserverless', region_name=region)
    collections = opensearch_client.list_collections()
    
    collection_arn = None
    for collection in collections.get('collectionSummaries', []):
        if 'bedrock-agent-mainte-kb' in collection['name']:
            collection_arn = collection['arn']
            break
    
    if not collection_arn:
        print("❌ No OpenSearch collection found")
        return None
    
    print(f"✅ Using collection: {collection_arn}")
    
    # IAM role ARN
    role_arn = f"arn:aws:iam::{account_id}:role/bedrock-knowledge-base-role"
    
    try:
        print("🔄 Creating simple Knowledge Base...")
        
        # Simple Knowledge Base configuration
        kb_config = {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
            }
        }
        
        # Simple storage configuration - let Bedrock create the index
        storage_config = {
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": collection_arn,
                "vectorIndexName": "bedrock-knowledge-base-default-index",
                "fieldMapping": {
                    "vectorField": "bedrock-knowledge-base-default-vector",
                    "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                    "metadataField": "AMAZON_BEDROCK_METADATA"
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
        
        # Update config
        config['lambda_functions']['data_sync']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
        config['lambda_functions']['health_check']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
        
        with open("config/aws_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated configuration with KB ID: {kb_id}")
        return kb_id
        
    except ClientError as e:
        print(f"❌ Failed to create Knowledge Base: {e}")
        return None

def main():
    """Main execution function"""
    try:
        kb_id = create_simple_knowledge_base()
        if kb_id:
            print(f"\n🎉 Knowledge Base created successfully!")
            print(f"Knowledge Base ID: {kb_id}")
            return 0
        else:
            print(f"\n❌ Knowledge Base creation failed")
            return 1
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())