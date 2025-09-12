#!/usr/bin/env python3
"""
Create Knowledge Base with RDS PostgreSQL

This script creates a Bedrock Knowledge Base using RDS PostgreSQL with pgvector.
"""

import json
import boto3
from botocore.exceptions import ClientError

def create_kb_with_rds():
    """Create Knowledge Base with RDS PostgreSQL vector store"""
    
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
        print("🔄 Creating Knowledge Base with RDS PostgreSQL...")
        
        # Knowledge Base configuration
        kb_config = {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
            }
        }
        
        # RDS storage configuration
        storage_config = {
            "type": "RDS",
            "rdsConfiguration": {
                "resourceArn": f"arn:aws:rds:{region}:{account_id}:cluster:bedrock-kb-cluster",
                "credentialsSecretArn": f"arn:aws:secretsmanager:{region}:{account_id}:secret:bedrock-kb-credentials",
                "databaseName": "bedrock_kb",
                "tableName": "bedrock_kb_table",
                "fieldMapping": {
                    "primaryKeyField": "id",
                    "vectorField": "embedding",
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
        print("ℹ️  This is a test to see RDS configuration requirements")
        kb_id = create_kb_with_rds()
        return 0 if kb_id else 1
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())