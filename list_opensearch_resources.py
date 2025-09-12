#!/usr/bin/env python3
"""
List OpenSearch Resources

This script lists existing OpenSearch Serverless resources.
"""

import json
import boto3
from botocore.exceptions import ClientError

def list_opensearch_resources():
    """List existing OpenSearch resources"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Initialize client
    opensearch_client = boto3.client('opensearchserverless', region_name=region)
    
    try:
        print("📋 Listing OpenSearch Serverless Resources")
        print("=" * 50)
        
        # List collections
        print("\n🗂️  Collections:")
        collections = opensearch_client.list_collections()
        for collection in collections.get('collectionSummaries', []):
            print(f"   Name: {collection['name']}")
            print(f"   ID: {collection['id']}")
            print(f"   Status: {collection['status']}")
            print(f"   ARN: {collection['arn']}")
            print()
        
        # List security policies
        print("🔒 Security Policies:")
        
        # Encryption policies
        enc_policies = opensearch_client.list_security_policies(type="encryption")
        print(f"   Encryption policies: {len(enc_policies.get('securityPolicySummaries', []))}")
        for policy in enc_policies.get('securityPolicySummaries', []):
            print(f"     - {policy['name']}")
        
        # Network policies
        net_policies = opensearch_client.list_security_policies(type="network")
        print(f"   Network policies: {len(net_policies.get('securityPolicySummaries', []))}")
        for policy in net_policies.get('securityPolicySummaries', []):
            print(f"     - {policy['name']}")
        
        # Access policies
        access_policies = opensearch_client.list_access_policies(type="data")
        print(f"   Access policies: {len(access_policies.get('accessPolicySummaries', []))}")
        for policy in access_policies.get('accessPolicySummaries', []):
            print(f"     - {policy['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to list resources: {e}")
        return False

def main():
    """Main execution function"""
    try:
        success = list_opensearch_resources()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())