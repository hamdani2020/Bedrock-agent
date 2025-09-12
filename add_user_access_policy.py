#!/usr/bin/env python3
"""
Add User Access Policy

This script adds access policy for the current user to manage OpenSearch indexes.
"""

import json
import boto3
from botocore.exceptions import ClientError

def add_user_access_policy():
    """Add access policy for current user"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    project_name = config["project_name"]
    
    # Initialize clients
    opensearch_client = boto3.client('opensearchserverless', region_name=region)
    sts = boto3.client('sts', region_name=region)
    
    # Get current user ARN
    identity = sts.get_caller_identity()
    user_arn = identity['Arn']
    account_id = identity['Account']
    
    # Collection name
    collection_name = f"{project_name[:20]}-kb"
    
    try:
        print(f"🔄 Adding user access policy for: {user_arn}")
        
        # Create data access policy for current user
        user_access_policy = [
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
                    user_arn,
                    f"arn:aws:iam::{account_id}:role/{config['iam']['knowledge_base_role']}"
                ]
            }
        ]
        
        # Create or update access policy
        policy_name = f"{collection_name[:15]}-user-access"
        
        try:
            opensearch_client.create_access_policy(
                name=policy_name,
                type="data",
                policy=json.dumps(user_access_policy)
            )
            print(f"✅ Created user access policy: {policy_name}")
        except ClientError as e:
            if "already exists" in str(e):
                # Update existing policy
                opensearch_client.update_access_policy(
                    name=policy_name,
                    type="data",
                    policy=json.dumps(user_access_policy)
                )
                print(f"✅ Updated user access policy: {policy_name}")
            else:
                raise
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add user access policy: {e}")
        return False

def main():
    """Main execution function"""
    try:
        success = add_user_access_policy()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())