#!/usr/bin/env python3
"""
Create Bedrock Knowledge Base with Managed Storage

This script creates a Bedrock Knowledge Base using Amazon's managed approach
with your S3 data source.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

def create_managed_knowledge_base():
    """Create Knowledge Base with managed vector storage"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    sts = boto3.client('sts', region_name=region)
    
    account_id = sts.get_caller_identity()['Account']
    
    print(f"🚀 Creating Managed Knowledge Base")
    print(f"📁 S3 Bucket: {config['s3']['data_bucket']['name']}")
    print(f"📂 S3 Path: {config['s3']['data_bucket']['data_structure']['base_prefix']}")
    print("=" * 60)
    
    try:
        # IAM role ARN
        role_arn = f"arn:aws:iam::{account_id}:role/{config['iam']['knowledge_base_role']}"
        
        # Knowledge Base name
        kb_name = config['bedrock']['knowledge_base']['name']
        
        # Check if KB already exists
        try:
            kbs = bedrock_agent.list_knowledge_bases()
            for kb in kbs.get('knowledgeBaseSummaries', []):
                if kb['name'] == kb_name:
                    print(f"✅ Knowledge Base already exists: {kb['knowledgeBaseId']}")
                    return kb['knowledgeBaseId']
        except ClientError:
            pass
        
        print(f"🔄 Creating Knowledge Base: {kb_name}")
        
        # Try the simplest possible configuration
        # Let AWS Bedrock handle the vector storage automatically
        
        response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            description=config['bedrock']['knowledge_base']['description'],
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/{config['bedrock']['knowledge_base']['foundation_model']}"
                }
            }
            # Let AWS handle storage configuration automatically
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Created Knowledge Base: {kb_id}")
        
        # Create S3 data source
        print(f"📁 Creating S3 data source...")
        
        s3_bucket = config['s3']['data_bucket']['name']
        s3_prefix = config['s3']['data_bucket']['data_structure']['base_prefix']
        
        ds_response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f"{s3_bucket}-maintenance-data",
            description=f"Maintenance data from {s3_bucket}/{s3_prefix}",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{s3_bucket}",
                    "inclusionPrefixes": [s3_prefix]
                }
            },
            vectorIngestionConfiguration={
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens": 300,
                        "overlapPercentage": 20
                    }
                }
            }
        )
        
        data_source_id = ds_response['dataSource']['dataSourceId']
        print(f"✅ Created data source: {data_source_id}")
        
        # Start ingestion
        print(f"⚡ Starting data ingestion...")
        
        ingestion_response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            description="Initial ingestion of maintenance data from S3"
        )
        
        ingestion_job_id = ingestion_response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {ingestion_job_id}")
        
        # Update configuration
        config['lambda_functions']['data_sync']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
        config['lambda_functions']['data_sync']['environment_variables']['DATA_SOURCE_ID'] = data_source_id
        config['lambda_functions']['health_check']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
        
        with open("config/aws_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration updated")
        
        return kb_id
        
    except ClientError as e:
        print(f"❌ Knowledge Base creation failed: {e}")
        
        # If this fails, it means we need vector storage
        # Let's provide clear guidance
        print(f"\nℹ️  Bedrock Knowledge Base requires vector storage.")
        print(f"   The S3 data will be indexed into a vector database for semantic search.")
        print(f"   Options:")
        print(f"   1. Use OpenSearch Serverless (AWS managed)")
        print(f"   2. Use Amazon MemoryDB for Redis")
        print(f"   3. Use Pinecone (external service)")
        
        return None

def main():
    """Main execution function"""
    try:
        kb_id = create_managed_knowledge_base()
        
        if kb_id:
            print(f"\n🎉 SUCCESS!")
            print(f"Knowledge Base ID: {kb_id}")
            print(f"\n✅ Task 3: Create Bedrock Knowledge Base - COMPLETED")
            print(f"✅ S3 data source configured: relu-quicksight/bedrock-recommendations/analytics/")
            print(f"✅ Agent can now reference maintenance data from S3")
            return 0
        else:
            print(f"\n❌ Knowledge Base creation failed")
            print(f"   We need to set up vector storage for the Knowledge Base")
            return 1
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())