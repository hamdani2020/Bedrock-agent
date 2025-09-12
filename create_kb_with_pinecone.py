#!/usr/bin/env python3
"""
Create Knowledge Base with Pinecone

This script creates a Bedrock Knowledge Base using Pinecone as the vector store.
"""

import json
import boto3
from botocore.exceptions import ClientError

def create_kb_with_pinecone():
    """Create Knowledge Base with Pinecone vector store"""
    
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
        print("🔄 Creating Knowledge Base with Pinecone...")
        
        # Knowledge Base configuration
        kb_config = {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
            }
        }
        
        # Pinecone storage configuration
        storage_config = {
            "type": "PINECONE",
            "pineconeConfiguration": {
                "connectionString": "https://maintenance-kb-12345.svc.us-west1-gcp.pinecone.io",
                "credentialsSecretArn": f"arn:aws:secretsmanager:{region}:{account_id}:secret:pinecone-api-key",
                "namespace": "maintenance-data",
                "fieldMapping": {
                    "textField": "text",
                    "metadataField": "metadata"
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
        print("ℹ️  This is a test to see Pinecone configuration requirements")
        kb_id = create_kb_with_pinecone()
        return 0 if kb_id else 1
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())