#!/usr/bin/env python3
"""
Cleanup OpenSearch Resources

This script cleans up existing OpenSearch Serverless resources to allow recreation.
"""

import json
import boto3
import sys
from botocore.exceptions import ClientError

def cleanup_opensearch_resources():
    """Clean up existing OpenSearch resources"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    project_name = config["project_name"]
    
    # Initialize client
    opensearch_client = boto3.client('opensearchserverless', region_name=region)
    
    # Collection name
    collection_name = f"{project_name[:20]}-kb"
    
    try:
        print(f"🧹 Cleaning up OpenSearch resources for: {collection_name}")
        
        # Delete collection
        try:
            print(f"🗑️  Deleting collection: {collection_name}")
            opensearch_client.delete_collection(id=collection_name)
            print(f"✅ Collection deletion initiated")
        except ClientError as e:
            if "ResourceNotFoundException" in str(e):
                print(f"ℹ️  Collection {collection_name} not found")
            else:
                print(f"⚠️  Failed to delete collection: {e}")
        
        # Delete policies
        policy_names = [
            f"{collection_name[:20]}-enc",
            f"{collection_name[:20]}-net", 
            f"{collection_name[:20]}-access"
        ]
        
        for policy_name in policy_names:
            try:
                # Try encryption policy
                try:
                    opensearch_client.delete_security_policy(
                        name=policy_name,
                        type="encryption"
                    )
                    print(f"✅ Deleted encryption policy: {policy_name}")
                except ClientError:
                    pass
                
                # Try network policy
                try:
                    opensearch_client.delete_security_policy(
                        name=policy_name,
                        type="network"
                    )
                    print(f"✅ Deleted network policy: {policy_name}")
                except ClientError:
                    pass
                
                # Try access policy
                try:
                    opensearch_client.delete_access_policy(
                        name=policy_name,
                        type="data"
                    )
                    print(f"✅ Deleted access policy: {policy_name}")
                except ClientError:
                    pass
                    
            except ClientError as e:
                if "ResourceNotFoundException" not in str(e):
                    print(f"⚠️  Failed to delete policy {policy_name}: {e}")
        
        print(f"🎉 Cleanup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Main execution function"""
    try:
        success = cleanup_opensearch_resources()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())