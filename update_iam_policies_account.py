#!/usr/bin/env python3
"""
Update IAM policies with correct account ID to remove wildcards.
"""
import json
import boto3
from botocore.exceptions import ClientError

def get_account_id():
    """Get the current AWS account ID."""
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        return response['Account']
    except ClientError as e:
        print(f"❌ Error getting account ID: {e}")
        return None

def update_policies_with_account_id(account_id: str):
    """Update IAM policies with the correct account ID."""
    
    # Load current policies
    try:
        with open('config/iam_policies.json', 'r') as f:
            policies = json.load(f)
    except FileNotFoundError:
        print("❌ IAM policies file not found")
        return False
    
    # Update policies with specific account ID
    updated_policies = {
        "lambda_execution_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-query-handler",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-query-handler:*",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-session-manager",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-session-manager:*",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-health-check",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-health-check:*",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-data-sync",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-data-sync:*"
                    ],
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": "us-west-2"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent"
                    ],
                    "Resource": f"arn:aws:bedrock:us-west-2:{account_id}:agent/GMJGK6RO4S",
                    "Condition": {
                        "StringEquals": {
                            "bedrock:knowledgeBaseId": "ZRE5Y0KEVD"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve"
                    ],
                    "Resource": f"arn:aws:bedrock:us-west-2:{account_id}:knowledge-base/ZRE5Y0KEVD",
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": "us-west-2"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query"
                    ],
                    "Resource": f"arn:aws:dynamodb:us-west-2:{account_id}:table/bedrock-agent-sessions",
                    "Condition": {
                        "ForAllValues:StringEquals": {
                            "dynamodb:Attributes": [
                                "sessionId",
                                "userId",
                                "createdAt",
                                "lastActivity",
                                "conversationHistory"
                            ]
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject"
                    ],
                    "Resource": "arn:aws:s3:::relu-quicksight/bedrock-recommendations/analytics/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:ExistingObjectTag/Environment": "production"
                        },
                        "DateGreaterThan": {
                            "s3:ExistingObjectTag/CreatedDate": "2024-01-01"
                        }
                    }
                }
            ]
        },
        "bedrock_agent_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve"
                    ],
                    "Resource": f"arn:aws:bedrock:us-west-2:{account_id}:knowledge-base/ZRE5Y0KEVD",
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": "us-west-2"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel"
                    ],
                    "Resource": "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": "us-west-2"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/bedrock/agents/GMJGK6RO4S",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/bedrock/agents/GMJGK6RO4S:*"
                    ]
                }
            ]
        },
        "knowledge_base_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject"
                    ],
                    "Resource": "arn:aws:s3:::relu-quicksight/bedrock-recommendations/analytics/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:ExistingObjectTag/Environment": "production"
                        },
                        "IpAddress": {
                            "aws:SourceIp": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListBucket"
                    ],
                    "Resource": "arn:aws:s3:::relu-quicksight",
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": "bedrock-recommendations/analytics/*"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "aoss:APIAccessAll"
                    ],
                    "Resource": f"arn:aws:aoss:us-west-2:{account_id}:collection/bedrock-knowledge-base-default-collection/*",
                    "Condition": {
                        "StringEquals": {
                            "aoss:collection-name": "bedrock-knowledge-base-default-collection"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel"
                    ],
                    "Resource": "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v1",
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": "us-west-2"
                        }
                    }
                }
            ]
        },
        "session_manager_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-session-manager",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-session-manager:*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query"
                    ],
                    "Resource": f"arn:aws:dynamodb:us-west-2:{account_id}:table/bedrock-agent-sessions",
                    "Condition": {
                        "ForAllValues:StringEquals": {
                            "dynamodb:LeadingKeys": ["${aws:userid}"]
                        }
                    }
                }
            ]
        },
        "health_check_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-health-check",
                        f"arn:aws:logs:us-west-2:{account_id}:log-group:/aws/lambda/bedrock-agent-health-check:*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:GetAgent",
                        "bedrock:GetKnowledgeBase"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:us-west-2:{account_id}:agent/GMJGK6RO4S",
                        f"arn:aws:bedrock:us-west-2:{account_id}:knowledge-base/ZRE5Y0KEVD"
                    ],
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": "us-west-2"
                        }
                    }
                }
            ]
        }
    }
    
    # Save updated policies
    with open('config/iam_policies.json', 'w') as f:
        json.dump(updated_policies, f, indent=2)
    
    print(f"✅ Updated IAM policies with account ID: {account_id}")
    return True

def main():
    """Main function."""
    print("🔧 Updating IAM Policies with Account ID")
    print("=" * 40)
    
    # Use the provided account ID
    account_id = "315990007223"
    
    print(f"Using account ID: {account_id}")
    
    if update_policies_with_account_id(account_id):
        print("✅ IAM policies updated successfully")
        print("Note: Replace '123456789012' with your actual AWS account ID")
    else:
        print("❌ Failed to update IAM policies")

if __name__ == "__main__":
    main()