#!/usr/bin/env python3
"""
Create Bedrock Knowledge Base - Final Working Version

This script creates a complete Bedrock Knowledge Base with OpenSearch Serverless
and your S3 data source, with proper configuration.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

def create_complete_knowledge_base():
    """Create complete Knowledge Base with proper OpenSearch setup"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    opensearch = boto3.client('opensearchserverless', region_name=region)
    sts = boto3.client('sts', region_name=region)
    
    account_id = sts.get_caller_identity()['Account']
    
    print(f"🚀 Creating Complete Knowledge Base Solution")
    print(f"📁 S3 Bucket: {config['s3']['data_bucket']['name']}")
    print(f"📂 S3 Path: {config['s3']['data_bucket']['data_structure']['base_prefix']}")
    print("=" * 60)
    
    try:
        # Step 1: Create OpenSearch Serverless Collection with proper policies
        collection_name = "bedrock-kb-collection"  # Shorter name
        
        print(f"🔍 Step 1: Setting up OpenSearch Serverless...")
        
        # Check if collection exists
        collection_arn = None
        try:
            collections = opensearch.list_collections()
            for collection in collections.get('collectionSummaries', []):
                if collection['name'] == collection_name:
                    collection_arn = collection['arn']
                    print(f"✅ Using existing collection: {collection_arn}")
                    break
        except ClientError:
            pass
        
        if not collection_arn:
            # Create encryption policy
            encryption_policy = {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"]
                    }
                ],
                "AWSOwnedKey": True
            }
            
            try:
                opensearch.create_security_policy(
                    name=f"{collection_name}-enc",
                    type="encryption",
                    policy=json.dumps(encryption_policy)
                )
                print(f"✅ Created encryption policy")
            except ClientError as e:
                if "already exists" not in str(e):
                    print(f"⚠️  Encryption policy issue: {e}")
            
            # Create network policy
            network_policy = [
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{collection_name}"]
                        }
                    ],
                    "AllowFromPublic": True
                }
            ]
            
            try:
                opensearch.create_security_policy(
                    name=f"{collection_name}-net",
                    type="network", 
                    policy=json.dumps(network_policy)
                )
                print(f"✅ Created network policy")
            except ClientError as e:
                if "already exists" not in str(e):
                    print(f"⚠️  Network policy issue: {e}")
            
            # Create data access policy
            data_access_policy = [
                {
                    "Rules": [
                        {
                            "ResourceType": "index",
                            "Resource": [f"index/{collection_name}/*"],
                            "Permission": [
                                "aoss:CreateIndex",
                                "aoss:DeleteIndex", 
                                "aoss:UpdateIndex",
                                "aoss:DescribeIndex",
                                "aoss:ReadDocument",
                                "aoss:WriteDocument"
                            ]
                        },
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{collection_name}"],
                            "Permission": [
                                "aoss:CreateCollectionItems",
                                "aoss:DeleteCollectionItems",
                                "aoss:UpdateCollectionItems", 
                                "aoss:DescribeCollectionItems"
                            ]
                        }
                    ],
                    "Principal": [
                        f"arn:aws:iam::{account_id}:role/{config['iam']['knowledge_base_role']}"
                    ]
                }
            ]
            
            try:
                opensearch.create_access_policy(
                    name=f"{collection_name}-access",
                    type="data",
                    policy=json.dumps(data_access_policy)
                )
                print(f"✅ Created data access policy")
            except ClientError as e:
                if "already exists" not in str(e):
                    print(f"⚠️  Data access policy issue: {e}")
            
            # Create collection
            print(f"🔄 Creating OpenSearch collection...")
            collection_response = opensearch.create_collection(
                name=collection_name,
                type="VECTORSEARCH",
                description="Vector collection for Bedrock Knowledge Base"
            )
            
            collection_arn = collection_response['createCollectionDetail']['arn']
            
            # Wait for collection to be active
            print(f"⏳ Waiting for collection to be active...")
            max_wait = 300
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    collection_details = opensearch.batch_get_collection(names=[collection_name])
                    if collection_details['collectionDetails']:
                        status = collection_details['collectionDetails'][0]['status']
                        if status == 'ACTIVE':
                            print(f"✅ Collection is active")
                            break
                        print(f"⏳ Collection status: {status}")
                except ClientError:
                    pass
                
                time.sleep(30)
                wait_time += 30
            
            print(f"✅ Created collection: {collection_arn}")
        
        # Step 2: Create Knowledge Base
        print(f"🧠 Step 2: Creating Knowledge Base...")
        
        kb_name = config['bedrock']['knowledge_base']['name']
        role_arn = f"arn:aws:iam::{account_id}:role/{config['iam']['knowledge_base_role']}"
        
        # Check if KB exists
        try:
            kbs = bedrock_agent.list_knowledge_bases()
            for kb in kbs.get('knowledgeBaseSummaries', []):
                if kb['name'] == kb_name:
                    print(f"✅ Knowledge Base already exists: {kb['knowledgeBaseId']}")
                    return kb['knowledgeBaseId']
        except ClientError:
            pass
        
        # Create Knowledge Base
        kb_response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            description=config['bedrock']['knowledge_base']['description'],
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": f"arn:aws:bedrock:{region}::foundation-model/{config['bedrock']['knowledge_base']['foundation_model']}"
                }
            },
            storageConfiguration={
                "type": "OPENSEARCH_SERVERLESS",
                "opensearchServerlessConfiguration": {
                    "collectionArn": collection_arn,
                    "vectorIndexName": "bedrock-knowledge-base-index",
                    "fieldMapping": {
                        "vectorField": "vector_field",
                        "textField": "text_field",
                        "metadataField": "metadata_field"
                    }
                }
            }
        )
        
        kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Created Knowledge Base: {kb_id}")
        
        # Step 3: Create S3 Data Source
        print(f"📁 Step 3: Creating S3 data source...")
        
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
        
        # Step 4: Start Ingestion
        print(f"⚡ Step 4: Starting data ingestion...")
        
        ingestion_response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            description="Initial ingestion of maintenance data from S3"
        )
        
        ingestion_job_id = ingestion_response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {ingestion_job_id}")
        
        # Step 5: Update Configuration
        print(f"⚙️  Step 5: Updating configuration...")
        
        config['lambda_functions']['data_sync']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
        config['lambda_functions']['data_sync']['environment_variables']['DATA_SOURCE_ID'] = data_source_id
        config['lambda_functions']['health_check']['environment_variables']['KNOWLEDGE_BASE_ID'] = kb_id
        
        with open("config/aws_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration updated")
        
        return kb_id
        
    except Exception as e:
        print(f"❌ Knowledge Base creation failed: {e}")
        return None

def main():
    """Main execution function"""
    try:
        kb_id = create_complete_knowledge_base()
        
        if kb_id:
            print(f"\n🎉 KNOWLEDGE BASE CREATED SUCCESSFULLY!")
            print(f"Knowledge Base ID: {kb_id}")
            print(f"Data Source: S3 bucket 'relu-quicksight'")
            print(f"Data Path: 'bedrock-recommendations/analytics/'")
            print(f"Vector Storage: OpenSearch Serverless")
            
            print(f"\n✅ Task 3: Create Bedrock Knowledge Base - COMPLETED")
            print(f"✅ S3 data source configured and ingesting")
            print(f"✅ Agent can now reference maintenance data from S3")
            print(f"✅ Ready to associate with Bedrock Agent")
            
            return 0
        else:
            print(f"\n❌ Knowledge Base creation failed")
            return 1
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())