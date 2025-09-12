#!/bin/bash
# Fix Lambda Function URL Auth Type
echo "🔧 Fixing Function URL Auth Type..."

aws lambda update-function-url-config \
  --function-name bedrock-agent-query-handler \
  --auth-type NONE \
  --cors '{
    "AllowCredentials": false,
    "AllowHeaders": ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"],
    "AllowMethods": ["POST", "OPTIONS"],
    "AllowOrigins": ["*"],
    "MaxAge": 300
  }' \
  --region us-west-2

echo "✅ Function URL auth type updated"
