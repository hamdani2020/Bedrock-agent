#!/usr/bin/env python3
"""
Create Minimal Knowledge Base

This script creates a minimal Bedrock Knowledge Base with OpenSearch Serverless.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

def create_minimal_knowledge_base():
    """Create a minimal Knowledge Base"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    opensearch_client = boto3.client('opensearchserverless', region_name=region)
    sts = boto3.client('sts', region_name=region)
    
    # Get account ID
    account_id = sts.get_caller_identity()['Account']
    
    # Get the OpenSearch collection ARN
    collections = opensearch_client.list_collections()
    
    collection_arn = None
    collection_id = None
    for collection in collections.get('collectionSummaries', []):
        if 'bedrock-agent-mainte-kb' in collection['name']:
            collection_arn = collection['arn']
            collection_id = collection['id']
            break
    
    if not collection_arn:
        print("❌ No OpenSearch collection found")
        return None
    
    print(f"✅ Using collection: {collection_arn}")
    print(f"✅ Collection ID: {collection_id}")
    
    # IAM role ARN
    role_arn = f"arn:aws:iam::{account_id}:role/bedrock-knowledge-base-role"
    
    try:
        print("🔄 Creating minimal Knowledge Base...")
        
        # Try different index names to see which one works
        index_names = [
            f"bedrock-kb-{int(time.time())}",  # Unique timestamp-based name
            "maintenance-kb-index",
            "bedrock-knowledge-base-index",
            "default-index"
        ]
        
        for index_name in index_names:
            try:
                print(f"🔄 Trying with index name: {index_name}")
                
                # Knowledge Base configuration
                kb_config = {
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
                    }
                }
                
                # Storage configuration
                storage_config = {
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": collection_arn,
                        "vectorIndexName": index_name,
                        "fieldMapping": {
                            "vectorField": "vector",
                            "textField": "text",
                            "metadataField": "metadata"
                        }
                    }
                }
                
                # Create Knowledge Base
                response = bedrock_agent.create_knowledge_base(
                    name=f"maintenance-fault-kb-{int(time.time())}",  # Unique name
                    description="Knowledge base for maintenance fault data",
                    roleArn=role_arn,
                    knowledgeBaseConfiguration=kb_config,
                    storageConfiguration=storage_config
                )
                
                kb_id = response['knowledgeBase']['knowledgeBaseId']
                print(f"✅ Created Knowledge Base: {kb_id}")
                print(f"✅ Used index name: {index_name}")
                
                # Update config
                config['lambda_functions']['data_sync']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
                config['lambda_functions']['health_check']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
                
                with open("config/aws_config.json", 'w') as f:
                    json.dump(config, f, indent=2)
                
                print(f"✅ Updated configuration with KB ID: {kb_id}")
                return kb_id
                
            except ClientError as e:
                print(f"❌ Failed with index {index_name}: {e}")
                continue
        
        print("❌ All index names failed")
        return None
        
    except Exception as e:
        print(f"❌ Failed to create Knowledge Base: {e}")
        return None

def main():
    """Main execution function"""
    try:
        kb_id = create_minimal_knowledge_base()
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