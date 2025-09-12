#!/usr/bin/env python3
"""
Bedrock Knowledge Base Creation Script

This script creates a Bedrock Knowledge Base for the maintenance fault data system.
It handles:
1. IAM role creation for Knowledge Base access
2. OpenSearch Serverless collection setup
3. Knowledge Base creation with S3 data source configuration
4. Data ingestion and testing

Requirements: 1.1, 1.2, 6.1, 6.5
"""

import json
import boto3
import time
import sys
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, Optional

class BedrockKnowledgeBaseCreator:
    def __init__(self, config_file: str = "config/aws_config.json"):
        """Initialize the Knowledge Base creator with configuration."""
        self.config = self._load_config(config_file)
        self.region = self.config["region"]
        
        # Initialize AWS clients
        try:
            self.bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
            self.iam = boto3.client('iam', region_name=self.region)
            self.opensearch_serverless = boto3.client('opensearchserverless', region_name=self.region)
            self.sts = boto3.client('sts', region_name=self.region)
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please configure your AWS credentials.")
            sys.exit(1)
        
        # Get account ID for ARN construction
        try:
            self.account_id = self.sts.get_caller_identity()['Account']
        except Exception as e:
            print(f"❌ Failed to get AWS account ID: {e}")
            sys.exit(1)
            
        print(f"✅ Initialized for account {self.account_id} in region {self.region}")

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file {config_file} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def create_knowledge_base_iam_role(self) -> str:
        """Create IAM role for Knowledge Base with required permissions."""
        role_name = self.config["iam"]["knowledge_base_role"]
        
        # Trust policy for Bedrock service
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Load permissions policy from config
        with open("config/iam_policies.json", 'r') as f:
            policies = json.load(f)
        
        permissions_policy = policies["knowledge_base_policy"]
        
        try:
            # Check if role already exists
            try:
                role = self.iam.get_role(RoleName=role_name)
                print(f"✅ IAM role {role_name} already exists")
                return role['Role']['Arn']
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise
            
            # Create the role
            print(f"🔄 Creating IAM role {role_name}...")
            role_response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="IAM role for Bedrock Knowledge Base to access S3 and OpenSearch"
            )
            
            # Attach the permissions policy
            policy_name = f"{role_name}-policy"
            self.iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permissions_policy)
            )
            
            # Wait for role to be available
            print("⏳ Waiting for IAM role to be available...")
            time.sleep(10)
            
            role_arn = role_response['Role']['Arn']
            print(f"✅ Created IAM role: {role_arn}")
            return role_arn
            
        except ClientError as e:
            print(f"❌ Failed to create IAM role: {e}")
            raise

    def create_opensearch_collection(self) -> str:
        """Create OpenSearch Serverless collection for Knowledge Base."""
        # Generate collection name (max 32 chars for OpenSearch Serverless)
        collection_name = f"{self.config['project_name'][:20]}-kb"
        
        try:
            # Check if collection already exists
            try:
                collections = self.opensearch_serverless.list_collections()
                for collection in collections.get('collectionSummaries', []):
                    if collection['name'] == collection_name:
                        print(f"✅ OpenSearch collection {collection_name} already exists")
                        return collection['arn']
            except ClientError:
                pass
            
            print(f"🔄 Creating OpenSearch Serverless collection {collection_name}...")
            
            # Create security policy for encryption
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
                self.opensearch_serverless.create_security_policy(
                    name=f"{collection_name[:20]}-enc",
                    type="encryption",
                    policy=json.dumps(encryption_policy)
                )
            except ClientError as e:
                if "already exists" not in str(e):
                    print(f"⚠️  Encryption policy creation failed: {e}")
            
            # Create network policy for access
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
                self.opensearch_serverless.create_security_policy(
                    name=f"{collection_name[:20]}-net",
                    type="network",
                    policy=json.dumps(network_policy)
                )
            except ClientError as e:
                if "already exists" not in str(e):
                    print(f"⚠️  Network policy creation failed: {e}")
            
            # Create data access policy for the Knowledge Base role
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
                        f"arn:aws:iam::{self.account_id}:role/{self.config['iam']['knowledge_base_role']}"
                    ]
                }
            ]
            
            try:
                self.opensearch_serverless.create_access_policy(
                    name=f"{collection_name[:20]}-access",
                    type="data",
                    policy=json.dumps(data_access_policy)
                )
                print(f"✅ Created data access policy")
            except ClientError as e:
                if "already exists" not in str(e):
                    print(f"⚠️  Data access policy creation failed: {e}")
            
            # Create the collection
            collection_response = self.opensearch_serverless.create_collection(
                name=collection_name,
                type="VECTORSEARCH",
                description="Vector collection for Bedrock Knowledge Base maintenance data"
            )
            
            # Wait for collection to be active
            print("⏳ Waiting for OpenSearch collection to be active...")
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    collection_details = self.opensearch_serverless.batch_get_collection(
                        names=[collection_name]
                    )
                    if collection_details['collectionDetails']:
                        status = collection_details['collectionDetails'][0]['status']
                        if status == 'ACTIVE':
                            break
                        print(f"⏳ Collection status: {status}")
                except ClientError:
                    pass
                
                time.sleep(30)
                wait_time += 30
            
            collection_arn = collection_response['createCollectionDetail']['arn']
            print(f"✅ Created OpenSearch collection: {collection_arn}")
            return collection_arn
            
        except ClientError as e:
            print(f"❌ Failed to create OpenSearch collection: {e}")
            raise

    def create_knowledge_base(self, role_arn: str, collection_arn: str) -> str:
        """Create the Bedrock Knowledge Base."""
        kb_config = self.config["bedrock"]["knowledge_base"]
        kb_name = kb_config["name"]
        
        try:
            # Check if Knowledge Base already exists
            try:
                knowledge_bases = self.bedrock_agent.list_knowledge_bases()
                for kb in knowledge_bases.get('knowledgeBaseSummaries', []):
                    if kb['name'] == kb_name:
                        print(f"✅ Knowledge Base {kb_name} already exists")
                        return kb['knowledgeBaseId']
            except ClientError:
                pass
            
            print(f"🔄 Creating Knowledge Base {kb_name}...")
            
            # Extract collection ID from ARN
            collection_id = collection_arn.split('/')[-1]
            
            # Knowledge Base configuration
            kb_configuration = {
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": f"arn:aws:bedrock:{self.region}::foundation-model/{kb_config['foundation_model']}"
                }
            }
            
            # Storage configuration for OpenSearch Serverless
            # Let Bedrock create the index automatically
            storage_configuration = {
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
            kb_response = self.bedrock_agent.create_knowledge_base(
                name=kb_name,
                description=kb_config["description"],
                roleArn=role_arn,
                knowledgeBaseConfiguration=kb_configuration,
                storageConfiguration=storage_configuration
            )
            
            knowledge_base_id = kb_response['knowledgeBase']['knowledgeBaseId']
            print(f"✅ Created Knowledge Base: {knowledge_base_id}")
            return knowledge_base_id
            
        except ClientError as e:
            print(f"❌ Failed to create Knowledge Base: {e}")
            raise

    def create_data_source(self, knowledge_base_id: str) -> str:
        """Create S3 data source for the Knowledge Base."""
        s3_config = self.config["s3"]["data_bucket"]
        bucket_name = s3_config["name"]
        data_prefix = s3_config["data_structure"]["base_prefix"]
        
        try:
            print(f"🔄 Creating S3 data source for bucket {bucket_name}...")
            
            # Data source configuration
            data_source_config = {
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{bucket_name}",
                    "inclusionPrefixes": [data_prefix]
                }
            }
            
            # Chunking configuration
            chunking_config = self.config["bedrock"]["knowledge_base"]["chunking_strategy"]
            
            # Vector ingestion configuration
            vector_ingestion_config = {
                "chunkingConfiguration": {
                    "chunkingStrategy": chunking_config["chunking_strategy"],
                    "fixedSizeChunkingConfiguration": chunking_config["fixed_size_chunking_configuration"]
                }
            }
            
            # Create data source
            ds_response = self.bedrock_agent.create_data_source(
                knowledgeBaseId=knowledge_base_id,
                name=f"{bucket_name}-fault-data",
                description=f"S3 data source for fault prediction data from {bucket_name}",
                dataSourceConfiguration=data_source_config,
                vectorIngestionConfiguration=vector_ingestion_config
            )
            
            data_source_id = ds_response['dataSource']['dataSourceId']
            print(f"✅ Created data source: {data_source_id}")
            return data_source_id
            
        except ClientError as e:
            print(f"❌ Failed to create data source: {e}")
            raise

    def start_ingestion_job(self, knowledge_base_id: str, data_source_id: str) -> str:
        """Start data ingestion job for the Knowledge Base."""
        try:
            print("🔄 Starting data ingestion job...")
            
            ingestion_response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=knowledge_base_id,
                dataSourceId=data_source_id,
                description="Initial ingestion of fault prediction data"
            )
            
            ingestion_job_id = ingestion_response['ingestionJob']['ingestionJobId']
            print(f"✅ Started ingestion job: {ingestion_job_id}")
            
            # Monitor ingestion job status
            print("⏳ Monitoring ingestion job progress...")
            max_wait = 600  # 10 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    job_status = self.bedrock_agent.get_ingestion_job(
                        knowledgeBaseId=knowledge_base_id,
                        dataSourceId=data_source_id,
                        ingestionJobId=ingestion_job_id
                    )
                    
                    status = job_status['ingestionJob']['status']
                    print(f"⏳ Ingestion status: {status}")
                    
                    if status == 'COMPLETE':
                        print("✅ Data ingestion completed successfully!")
                        break
                    elif status == 'FAILED':
                        failure_reasons = job_status['ingestionJob'].get('failureReasons', [])
                        print(f"❌ Ingestion failed: {failure_reasons}")
                        break
                        
                except ClientError as e:
                    print(f"⚠️  Error checking ingestion status: {e}")
                
                time.sleep(30)
                wait_time += 30
            
            return ingestion_job_id
            
        except ClientError as e:
            print(f"❌ Failed to start ingestion job: {e}")
            raise

    def test_knowledge_base(self, knowledge_base_id: str) -> bool:
        """Test the Knowledge Base with sample queries."""
        try:
            print("🔄 Testing Knowledge Base with sample queries...")
            
            test_queries = [
                "What are the most common fault types?",
                "Show me recent bearing failures",
                "What sensor readings indicate critical faults?"
            ]
            
            for query in test_queries:
                try:
                    print(f"🔍 Testing query: {query}")
                    
                    response = self.bedrock_agent.retrieve(
                        knowledgeBaseId=knowledge_base_id,
                        retrievalQuery={
                            'text': query
                        },
                        retrievalConfiguration={
                            'vectorSearchConfiguration': {
                                'numberOfResults': 3
                            }
                        }
                    )
                    
                    results = response.get('retrievalResults', [])
                    print(f"✅ Retrieved {len(results)} results for query")
                    
                    if results:
                        # Show first result as example
                        first_result = results[0]
                        content = first_result.get('content', {}).get('text', '')[:200]
                        score = first_result.get('score', 0)
                        print(f"   Sample result (score: {score:.3f}): {content}...")
                    
                except ClientError as e:
                    print(f"⚠️  Query test failed: {e}")
                    return False
            
            print("✅ Knowledge Base testing completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Knowledge Base testing failed: {e}")
            return False

    def update_config_with_ids(self, knowledge_base_id: str, data_source_id: str):
        """Update configuration file with created resource IDs."""
        try:
            # Update Lambda environment variables
            self.config["lambda_functions"]["data_sync"]["environment_variables"]["KNOWLEDGE_BASE_ID"] = knowledge_base_id
            self.config["lambda_functions"]["data_sync"]["environment_variables"]["DATA_SOURCE_ID"] = data_source_id
            self.config["lambda_functions"]["health_check"]["environment_variables"]["KNOWLEDGE_BASE_ID"] = knowledge_base_id
            
            # Save updated configuration
            with open("config/aws_config.json", 'w') as f:
                json.dump(self.config, f, indent=2)
            
            print("✅ Updated configuration file with Knowledge Base IDs")
            
        except Exception as e:
            print(f"⚠️  Failed to update configuration: {e}")

    def create_complete_knowledge_base(self) -> Dict[str, str]:
        """Execute the complete Knowledge Base creation process."""
        print("🚀 Starting Bedrock Knowledge Base creation process...")
        print("=" * 60)
        
        try:
            # Step 1: Create IAM role
            print("\n📋 Step 1: Creating IAM role for Knowledge Base...")
            role_arn = self.create_knowledge_base_iam_role()
            
            # Step 2: Create OpenSearch collection
            print("\n🔍 Step 2: Creating OpenSearch Serverless collection...")
            collection_arn = self.create_opensearch_collection()
            
            # Step 3: Create Knowledge Base
            print("\n🧠 Step 3: Creating Bedrock Knowledge Base...")
            knowledge_base_id = self.create_knowledge_base(role_arn, collection_arn)
            
            # Step 4: Create data source
            print("\n📁 Step 4: Creating S3 data source...")
            data_source_id = self.create_data_source(knowledge_base_id)
            
            # Step 5: Start ingestion
            print("\n⚡ Step 5: Starting data ingestion...")
            ingestion_job_id = self.start_ingestion_job(knowledge_base_id, data_source_id)
            
            # Step 6: Test Knowledge Base
            print("\n🧪 Step 6: Testing Knowledge Base...")
            test_success = self.test_knowledge_base(knowledge_base_id)
            
            # Step 7: Update configuration
            print("\n⚙️  Step 7: Updating configuration...")
            self.update_config_with_ids(knowledge_base_id, data_source_id)
            
            # Summary
            print("\n" + "=" * 60)
            print("🎉 KNOWLEDGE BASE CREATION COMPLETED!")
            print("=" * 60)
            
            results = {
                "knowledge_base_id": knowledge_base_id,
                "data_source_id": data_source_id,
                "ingestion_job_id": ingestion_job_id,
                "role_arn": role_arn,
                "collection_arn": collection_arn,
                "test_success": test_success
            }
            
            print(f"📊 Knowledge Base ID: {knowledge_base_id}")
            print(f"📁 Data Source ID: {data_source_id}")
            print(f"⚡ Ingestion Job ID: {ingestion_job_id}")
            print(f"🔐 IAM Role ARN: {role_arn}")
            print(f"🔍 OpenSearch Collection ARN: {collection_arn}")
            print(f"🧪 Test Status: {'✅ PASSED' if test_success else '❌ FAILED'}")
            
            return results
            
        except Exception as e:
            print(f"\n❌ Knowledge Base creation failed: {e}")
            raise


def main():
    """Main execution function."""
    print("Bedrock Knowledge Base Creator")
    print("=" * 40)
    
    try:
        creator = BedrockKnowledgeBaseCreator()
        results = creator.create_complete_knowledge_base()
        
        print(f"\n✅ Knowledge Base creation completed successfully!")
        print(f"Knowledge Base ID: {results['knowledge_base_id']}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())