#!/bin/bash
# Add Resource-Based Policy for Function URL
echo "🔧 Adding Function URL permission..."

aws lambda add-permission \
  --function-name bedrock-agent-query-handler \
  --statement-id AllowPublicFunctionUrlAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region us-west-2

echo "✅ Function URL permission added"
