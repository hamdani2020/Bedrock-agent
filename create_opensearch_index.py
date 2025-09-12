#!/usr/bin/env python3
"""
Create OpenSearch Index

This script creates the required index in the OpenSearch Serverless collection.
"""

import json
import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.exceptions import ClientError

def create_opensearch_index():
    """Create index in OpenSearch Serverless collection"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Get collection endpoint
    opensearch_client = boto3.client('opensearchserverless', region_name=region)
    collections = opensearch_client.list_collections()
    
    collection_endpoint = None
    for collection in collections.get('collectionSummaries', []):
        if 'bedrock-agent-mainte-kb' in collection['name']:
            # Get collection details to find endpoint
            collection_details = opensearch_client.batch_get_collection(
                names=[collection['name']]
            )
            if collection_details['collectionDetails']:
                collection_endpoint = collection_details['collectionDetails'][0]['collectionEndpoint']
                break
    
    if not collection_endpoint:
        print("❌ No OpenSearch collection endpoint found")
        return False
    
    print(f"✅ Using collection endpoint: {collection_endpoint}")
    
    try:
        # Create index mapping for Bedrock Knowledge Base
        index_name = "bedrock-knowledge-base-default-index"
        
        index_mapping = {
            "mappings": {
                "properties": {
                    "bedrock-knowledge-base-default-vector": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "faiss"
                        }
                    },
                    "AMAZON_BEDROCK_TEXT_CHUNK": {
                        "type": "text"
                    },
                    "AMAZON_BEDROCK_METADATA": {
                        "type": "object"
                    }
                }
            }
        }
        
        # Create signed request
        session = boto3.Session()
        credentials = session.get_credentials()
        
        url = f"{collection_endpoint}/{index_name}"
        
        # Create AWS request
        request = AWSRequest(
            method='PUT',
            url=url,
            data=json.dumps(index_mapping),
            headers={'Content-Type': 'application/json'}
        )
        
        # Sign the request
        SigV4Auth(credentials, 'aoss', region).add_auth(request)
        
        # Send request
        response = requests.put(
            url,
            data=json.dumps(index_mapping),
            headers=dict(request.headers)
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Created index: {index_name}")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"❌ Failed to create index: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Failed to create index: {e}")
        return False

def main():
    """Main execution function"""
    try:
        success = create_opensearch_index()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())