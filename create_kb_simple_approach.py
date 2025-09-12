#!/usr/bin/env python3
"""
Simple Knowledge Base Creation

This script creates a Bedrock Knowledge Base with a simplified approach,
focusing on getting it working with S3 data.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

def create_simple_knowledge_base():
    """Create Knowledge Base with simplified configuration"""
    
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
        print("🔄 Creating simple Knowledge Base...")
        
        # Try with minimal configuration first
        kb_config = {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
            }
        }
        
        # Let's try with Pinecone (external service) as it might be simpler
        # But first, let's see what happens if we just try to create without storage
        
        print("📋 Attempting to create Knowledge Base...")
        
        # First, let's see what storage types are supported by trying different ones
        storage_types_to_try = [
            {
                "name": "OpenSearch Serverless (simplified)",
                "config": {
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": "arn:aws:aoss:us-west-2:315990007223:collection/wy8n1vaz6ysu7iuuqhnl",
                        "vectorIndexName": "maintenance-index",
                        "fieldMapping": {
                            "vectorField": "vector",
                            "textField": "text",
                            "metadataField": "metadata"
                        }
                    }
                }
            }
        ]
        
        for storage_option in storage_types_to_try:
            try:
                print(f"🔄 Trying {storage_option['name']}...")
                
                response = bedrock_agent.create_knowledge_base(
                    name="maintenance-fault-kb",
                    description="Knowledge base for maintenance fault data",
                    roleArn=role_arn,
                    knowledgeBaseConfiguration=kb_config,
                    storageConfiguration=storage_option['config']
                )
                
                kb_id = response['knowledgeBase']['knowledgeBaseId']
                print(f"✅ Created Knowledge Base with {storage_option['name']}: {kb_id}")
                
                # Create S3 data source
                print("📁 Creating S3 data source...")
                
                data_source_response = bedrock_agent.create_data_source(
                    knowledgeBaseId=kb_id,
                    name="maintenance-s3-data",
                    description="S3 data source for maintenance fault data",
                    dataSourceConfiguration={
                        "type": "S3",
                        "s3Configuration": {
                            "bucketArn": "arn:aws:s3:::relu-quicksight",
                            "inclusionPrefixes": ["bedrock-recommendations/analytics/"]
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
                
                data_source_id = data_source_response['dataSource']['dataSourceId']
                print(f"✅ Created data source: {data_source_id}")
                
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
                    'storage_type': storage_option['name']
                }
                
            except ClientError as e:
                print(f"❌ Failed with {storage_option['name']}: {e}")
                continue
        
        print("❌ All storage options failed")
        return None
        
    except Exception as e:
        print(f"❌ Failed to create Knowledge Base: {e}")
        return None

def main():
    """Main execution function"""
    try:
        result = create_simple_knowledge_base()
        
        if result:
            print(f"\n🎉 Knowledge Base created successfully!")
            print(f"Knowledge Base ID: {result['knowledge_base_id']}")
            print(f"Data Source ID: {result['data_source_id']}")
            print(f"Storage Type: {result['storage_type']}")
            print(f"\nNext steps:")
            print(f"1. Start ingestion job to load S3 data")
            print(f"2. Associate Knowledge Base with Bedrock Agent")
            print(f"3. Test the complete system")
            return 0
        else:
            print(f"\n❌ Knowledge Base creation failed with all storage options")
            return 1
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())