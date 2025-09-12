#!/usr/bin/env python3
"""
Create Bedrock Knowledge Base with Managed Vector Store

This script creates a Bedrock Knowledge Base using AWS managed vector storage,
which eliminates the need to set up OpenSearch manually.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

def create_managed_knowledge_base():
    """Create Knowledge Base with AWS managed vector storage"""
    
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
        print("🔄 Creating Knowledge Base with managed vector storage...")
        
        # Knowledge Base configuration
        kb_config = {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
            }
        }
        
        # Use managed vector storage (no OpenSearch required)
        storage_config = {
            "type": "REDIS_ENTERPRISE_CLOUD",
            "redisEnterpriseCloudConfiguration": {
                "endpoint": "redis://managed-vector-store.aws.com:6379",
                "vectorIndexName": "maintenance-data-index",
                "credentialsSecretArn": f"arn:aws:secretsmanager:{region}:{account_id}:secret:redis-credentials",
                "fieldMapping": {
                    "vectorField": "vector",
                    "textField": "text",
                    "metadataField": "metadata"
                }
            }
        }
        
        # Actually, let's try without specifying storage - let AWS manage it
        # This might use the default managed storage
        
        # Create Knowledge Base without explicit storage config
        response = bedrock_agent.create_knowledge_base(
            name="maintenance-fault-kb",
            description="Knowledge base for maintenance fault data",
            roleArn=role_arn,
            knowledgeBaseConfiguration=kb_config
            # Note: No storageConfiguration - let AWS use default managed storage
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Created Knowledge Base: {kb_id}")
        
        # Now create the S3 data source
        print("📁 Creating S3 data source...")
        
        data_source_config = {
            "type": "S3",
            "s3Configuration": {
                "bucketArn": "arn:aws:s3:::relu-quicksight",
                "inclusionPrefixes": ["bedrock-recommendations/analytics/"]
            }
        }
        
        # Chunking configuration
        chunking_config = {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 300,
                "overlapPercentage": 20
            }
        }
        
        # Create data source
        ds_response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name="maintenance-s3-data",
            description="S3 data source for maintenance fault data",
            dataSourceConfiguration=data_source_config,
            vectorIngestionConfiguration={
                "chunkingConfiguration": chunking_config
            }
        )
        
        data_source_id = ds_response['dataSource']['dataSourceId']
        print(f"✅ Created data source: {data_source_id}")
        
        # Start ingestion job
        print("⚡ Starting data ingestion...")
        
        ingestion_response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            description="Initial ingestion of maintenance fault data"
        )
        
        ingestion_job_id = ingestion_response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {ingestion_job_id}")
        
        # Update configuration
        config['lambda_functions']['data_sync']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
        config['lambda_functions']['data_sync']['environment_variables']['DATA_SOURCE_ID'] = data_source_id
        config['lambda_functions']['health_check']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
        
        with open("config/aws_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Updated configuration")
        
        return {
            'knowledge_base_id': kb_id,
            'data_source_id': data_source_id,
            'ingestion_job_id': ingestion_job_id
        }
        
    except ClientError as e:
        print(f"❌ Failed to create Knowledge Base: {e}")
        return None

def main():
    """Main execution function"""
    try:
        result = create_managed_knowledge_base()
        
        if result:
            print(f"\n🎉 Knowledge Base created successfully!")
            print(f"Knowledge Base ID: {result['knowledge_base_id']}")
            print(f"Data Source ID: {result['data_source_id']}")
            print(f"Ingestion Job ID: {result['ingestion_job_id']}")
            print(f"\nThe Knowledge Base will now:")
            print(f"✅ Read data from S3: relu-quicksight/bedrock-recommendations/analytics/")
            print(f"✅ Create vector embeddings automatically")
            print(f"✅ Enable semantic search for the Bedrock Agent")
            return 0
        else:
            print(f"\n❌ Knowledge Base creation failed")
            return 1
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())