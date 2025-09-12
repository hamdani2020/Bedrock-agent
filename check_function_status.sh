#!/bin/bash
# Check Lambda Function Status
echo "🔍 Checking function status..."

echo "Function Configuration:"
aws lambda get-function --function-name bedrock-agent-query-handler --region us-west-2

echo "\nFunction URL Configuration:"
aws lambda get-function-url-config --function-name bedrock-agent-query-handler --region us-west-2

echo "\nFunction Policy:"
aws lambda get-policy --function-name bedrock-agent-query-handler --region us-west-2 || echo "No resource policy found"

echo "\nRecent Logs:"
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/bedrock-agent-query-handler" --region us-west-2
