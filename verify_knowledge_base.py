#!/usr/bin/env python3
"""
Verify manually created Knowledge Base configuration and status
"""

import boto3
import json
from botocore.exceptions import ClientError

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def verify_knowledge_base():
    """Verify the manually created knowledge base"""
    config = load_config()
    if not config:
        return False
    
    try:
        # Initialize Bedrock Agent client
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        print("🔍 Searching for Knowledge Bases...")
        
        # List all knowledge bases
        response = bedrock_agent.list_knowledge_bases()
        knowledge_bases = response.get('knowledgeBaseSummaries', [])
        
        if not knowledge_bases:
            print("❌ No Knowledge Bases found")
            return False
        
        print(f"✅ Found {len(knowledge_bases)} Knowledge Base(s)")
        
        # Check each knowledge base
        for kb in knowledge_bases:
            kb_id = kb['knowledgeBaseId']
            kb_name = kb['name']
            kb_status = kb['status']
            
            print(f"\n📋 Knowledge Base: {kb_name}")
            print(f"   ID: {kb_id}")
            print(f"   Status: {kb_status}")
            print(f"   Created: {kb.get('createdAt', 'Unknown')}")
            print(f"   Updated: {kb.get('updatedAt', 'Unknown')}")
            
            # Get detailed information
            try:
                detail_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
                kb_detail = detail_response['knowledgeBase']
                
                print(f"   Description: {kb_detail.get('description', 'No description')}")
                print(f"   Role ARN: {kb_detail.get('roleArn', 'Not specified')}")
                
                # Check knowledge base configuration
                kb_config = kb_detail.get('knowledgeBaseConfiguration', {})
                if kb_config:
                    kb_type = kb_config.get('type', 'Unknown')
                    print(f"   Type: {kb_type}")
                    
                    if 'vectorKnowledgeBaseConfiguration' in kb_config:
                        vector_config = kb_config['vectorKnowledgeBaseConfiguration']
                        embedding_model = vector_config.get('embeddingModelArn', 'Not specified')
                        print(f"   Embedding Model: {embedding_model}")
                
                # Check storage configuration
                storage_config = kb_detail.get('storageConfiguration', {})
                if storage_config:
                    storage_type = storage_config.get('type', 'Unknown')
                    print(f"   Storage Type: {storage_type}")
                    
                    if storage_type == 'OPENSEARCH_SERVERLESS':
                        oss_config = storage_config.get('opensearchServerlessConfiguration', {})
                        collection_arn = oss_config.get('collectionArn', 'Not specified')
                        vector_index_name = oss_config.get('vectorIndexName', 'Not specified')
                        print(f"   Collection ARN: {collection_arn}")
                        print(f"   Vector Index: {vector_index_name}")
                    
                    elif storage_type == 'RDS':
                        rds_config = storage_config.get('rdsConfiguration', {})
                        print(f"   RDS Config: {rds_config}")
                
                # Check data sources
                try:
                    ds_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
                    data_sources = ds_response.get('dataSourceSummaries', [])
                    
                    if data_sources:
                        print(f"   Data Sources: {len(data_sources)}")
                        for ds in data_sources:
                            print(f"     - {ds['name']} (ID: {ds['dataSourceId']}, Status: {ds['status']})")
                    else:
                        print("   ⚠️  No data sources configured")
                        
                except ClientError as e:
                    print(f"   ⚠️  Could not list data sources: {e}")
                
                # Update config with KB ID if this looks like our KB
                if 'maintenance' in kb_name.lower() or 'expert' in kb_name.lower():
                    config['knowledge_base_id'] = kb_id
                    with open('config/aws_config.json', 'w') as f:
                        json.dump(config, f, indent=2)
                    print(f"   ✅ Updated config with Knowledge Base ID: {kb_id}")
                
            except ClientError as e:
                print(f"   ❌ Error getting KB details: {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error accessing Bedrock Agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_knowledge_base_query():
    """Test querying the knowledge base"""
    config = load_config()
    if not config or 'knowledge_base_id' not in config:
        print("❌ No Knowledge Base ID in config")
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        print(f"\n🧪 Testing Knowledge Base query (ID: {kb_id})...")
        
        # Test query
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': 'What is preventive maintenance?'
            }
        )
        
        results = response.get('retrievalResults', [])
        print(f"✅ Query successful! Retrieved {len(results)} results")
        
        if results:
            for i, result in enumerate(results[:2]):  # Show first 2 results
                print(f"\n   Result {i+1}:")
                print(f"   Score: {result.get('score', 'N/A')}")
                content = result.get('content', {}).get('text', 'No content')
                print(f"   Content: {content[:200]}...")
                
                location = result.get('location', {})
                if location:
                    print(f"   Source: {location}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ValidationException':
            print("❌ Knowledge Base not ready for queries yet")
        else:
            print(f"❌ Error querying Knowledge Base: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during query: {e}")
        return False

def main():
    """Main verification function"""
    print("🔍 Verifying manually created Knowledge Base...\n")
    
    if verify_knowledge_base():
        print("\n" + "="*50)
        test_knowledge_base_query()
    
    print("\n" + "="*50)
    print("✅ Knowledge Base verification complete!")

if __name__ == "__main__":
    main()