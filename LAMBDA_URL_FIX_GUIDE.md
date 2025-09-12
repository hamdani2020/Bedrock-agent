# Lambda Function URL Permission Fix Guide

## Problem
The Lambda Function URL `https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/` is returning HTTP 403 Forbidden errors.

## Root Cause Analysis
The 403 error typically indicates one of these issues:
1. Function URL AuthType is set to AWS_IAM instead of NONE
2. Missing resource-based policy for public access
3. CORS configuration blocking requests
4. Function is not active or has deployment issues

## Solution Steps

### Step 1: Check Current Configuration
```bash
# Check function URL configuration
aws lambda get-function-url-config \
  --function-name bedrock-agent-query-handler \
  --region us-west-2

# Check function status
aws lambda get-function \
  --function-name bedrock-agent-query-handler \
  --region us-west-2
```

### Step 2: Fix Auth Type (Most Likely Issue)
```bash
# Update Function URL to allow public access
aws lambda update-function-url-config \
  --function-name bedrock-agent-query-handler \
  --auth-type NONE \
  --region us-west-2
```

### Step 3: Add Resource-Based Policy
```bash
# Add permission for public Function URL access
aws lambda add-permission \
  --function-name bedrock-agent-query-handler \
  --statement-id AllowPublicFunctionUrlAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --region us-west-2
```

### Step 4: Update CORS Configuration
```bash
# Update CORS to allow Streamlit origins
aws lambda update-function-url-config \
  --function-name bedrock-agent-query-handler \
  --cors '{
    "AllowCredentials": false,
    "AllowHeaders": ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"],
    "AllowMethods": ["POST", "OPTIONS"],
    "AllowOrigins": ["https://localhost:8501", "https://*.streamlit.app", "https://*.herokuapp.com", "*"],
    "MaxAge": 300
  }' \
  --region us-west-2
```

### Step 5: Test the Fix
```bash
# Test the Function URL
curl -X POST https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"query":"test","sessionId":"test-session"}'
```

## AWS Console Steps

### Via AWS Lambda Console:
1. Go to AWS Lambda Console
2. Find function: `bedrock-agent-query-handler`
3. Go to "Configuration" → "Function URL"
4. Edit the Function URL:
   - Set Auth type to "NONE"
   - Configure CORS as needed
5. Go to "Configuration" → "Permissions"
6. Add resource-based policy for Function URL access

### Expected Result:
- HTTP 200 response with JSON containing agent response
- CORS headers present in response
- No authentication required

## Verification Commands

```bash
# Verify Function URL configuration
aws lambda get-function-url-config --function-name bedrock-agent-query-handler --region us-west-2

# Verify resource policy
aws lambda get-policy --function-name bedrock-agent-query-handler --region us-west-2

# Test with curl
curl -v -X POST https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/ \
  -H "Content-Type: application/json" \
  -H "Origin: https://localhost:8501" \
  -d '{"query":"What is the equipment status?","sessionId":"test-123"}'
```

## Troubleshooting

### If still getting 403:
1. Check CloudWatch logs: `/aws/lambda/bedrock-agent-query-handler`
2. Verify function is active and not in error state
3. Check if there are any account-level restrictions
4. Ensure the Function URL exists and is properly configured

### If getting CORS errors:
1. Verify CORS configuration includes your domain
2. Check that preflight OPTIONS requests are handled
3. Ensure all required headers are allowed

### If getting timeout errors:
1. Check function timeout settings (should be 300 seconds)
2. Verify Bedrock Agent is accessible
3. Check function memory allocation

## Security Considerations

⚠️  **Important**: Setting AuthType to NONE makes the Function URL publicly accessible.

For production:
- Consider implementing API Gateway with authentication
- Add rate limiting and monitoring
- Restrict CORS origins to specific domains
- Monitor usage and costs

## Files Generated
- `fix_function_url_auth.sh` - Fix auth type script
- `fix_function_url_policy.sh` - Add policy script  
- `check_function_status.sh` - Status check script
- `lambda_url_fix.tf` - Terraform configuration
- `lambda_url_fix.yaml` - CloudFormation template

Run these scripts with appropriate AWS credentials and permissions.
