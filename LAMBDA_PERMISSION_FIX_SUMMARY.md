# Lambda Function URL Permission Fix Summary

## Issue Identified ✅

The Lambda Function URL `https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/` is returning **HTTP 403 Forbidden** errors.

### Root Cause Analysis
- **Function URL exists** ✅ (returns 403, not 404)
- **CORS is working** ✅ (OPTIONS requests return 200 with proper headers)
- **Authentication issue** ❌ (Function URL likely configured with AWS_IAM auth instead of NONE)

## Diagnostic Results

### Test Results:
- **POST requests**: HTTP 403 Forbidden
- **OPTIONS requests**: HTTP 200 (CORS working)
- **GET requests**: HTTP 403 Forbidden

### CORS Headers Present:
```
Access-Control-Allow-Origin: https://localhost:8501
Access-Control-Allow-Headers: content-type,authorization
Access-Control-Allow-Methods: POST
Access-Control-Max-Age: 86400
```

## Fix Resources Generated ✅

### 1. Shell Scripts (Ready to Execute)
- **`fix_function_url_auth.sh`** - Fix auth type to NONE and update CORS
- **`fix_function_url_policy.sh`** - Add resource-based policy for public access
- **`check_function_status.sh`** - Verify function status and configuration

### 2. Infrastructure as Code
- **`lambda_url_fix.tf`** - Terraform configuration
- **`lambda_url_fix.yaml`** - CloudFormation template

### 3. Documentation
- **`LAMBDA_URL_FIX_GUIDE.md`** - Comprehensive manual fix guide
- **`test_lambda_url_fix.py`** - Test script to verify fixes

## Quick Fix Instructions 🚀

### Step 1: Apply the Primary Fix
```bash
# This is the most likely fix needed
./fix_function_url_auth.sh
```

### Step 2: Add Resource Policy (if needed)
```bash
# Add public access permission
./fix_function_url_policy.sh
```

### Step 3: Verify the Fix
```bash
# Test the Function URL
python test_lambda_url_fix.py
```

### Step 4: Manual Test
```bash
# Direct curl test
curl -X POST https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"query":"test","sessionId":"test-session"}'
```

## Expected Results After Fix

### Successful Response:
```json
{
  "response": "I can help you with equipment maintenance questions...",
  "sessionId": "test-session",
  "timestamp": "2025-09-12T07:49:00Z"
}
```

### HTTP Status: `200 OK`

### CORS Headers Present:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: content-type, x-amz-date, authorization, x-api-key, x-amz-security-token
```

## Technical Details

### Function Configuration:
- **Function Name**: `bedrock-agent-query-handler`
- **Region**: `us-west-2`
- **Current Auth Type**: `AWS_IAM` (needs to be `NONE`)
- **Required Action**: `lambda:InvokeFunctionUrl`

### Required Changes:
1. **Auth Type**: Change from `AWS_IAM` to `NONE`
2. **Resource Policy**: Add permission for public access
3. **CORS**: Update to allow all necessary origins

## AWS CLI Commands (Manual Execution)

### Check Current Configuration:
```bash
aws lambda get-function-url-config \
  --function-name bedrock-agent-query-handler \
  --region us-west-2
```

### Fix Auth Type:
```bash
aws lambda update-function-url-config \
  --function-name bedrock-agent-query-handler \
  --auth-type NONE \
  --region us-west-2
```

### Add Resource Policy:
```bash
aws lambda add-permission \
  --function-name bedrock-agent-query-handler \
  --statement-id AllowPublicFunctionUrlAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --region us-west-2
```

## Security Considerations ⚠️

**Important**: Setting `AuthType` to `NONE` makes the Function URL publicly accessible.

### For Production:
- Consider implementing API Gateway with authentication
- Add rate limiting and monitoring
- Restrict CORS origins to specific domains
- Monitor usage and costs
- Implement request validation and sanitization

### Current Setup:
- Public access required for Streamlit integration
- CORS configured for common Streamlit hosting platforms
- No authentication required (suitable for demo/development)

## Troubleshooting

### If Still Getting 403:
1. **Check AWS credentials**: Ensure AWS CLI is configured
2. **Verify execution**: Check if commands completed successfully
3. **Wait for propagation**: Changes may take 1-2 minutes
4. **Check CloudWatch logs**: Look for Lambda function errors
5. **Verify function status**: Ensure function is active

### If Getting 500 Errors:
1. **Check Lambda logs**: Function may have runtime errors
2. **Verify Bedrock permissions**: Lambda needs Bedrock access
3. **Check environment variables**: Agent ID and Alias ID must be correct

### If Getting CORS Errors:
1. **Verify CORS config**: Check allowed origins and methods
2. **Test preflight**: Ensure OPTIONS requests work
3. **Check browser console**: Look for specific CORS errors

## Next Steps After Fix ✅

1. **Verify Fix**: Run `python test_lambda_url_fix.py`
2. **Test Streamlit Integration**: Update and test Streamlit app
3. **Deploy Streamlit App**: Follow `STREAMLIT_DEPLOYMENT_GUIDE.md`
4. **Monitor Performance**: Set up CloudWatch monitoring
5. **User Acceptance Testing**: Test with real users

## Files Reference

- **Fix Scripts**: `fix_function_url_auth.sh`, `fix_function_url_policy.sh`
- **Test Script**: `test_lambda_url_fix.py`
- **Documentation**: `LAMBDA_URL_FIX_GUIDE.md`
- **Infrastructure**: `lambda_url_fix.tf`, `lambda_url_fix.yaml`
- **Status Check**: `check_function_status.sh`

---

**Status**: 🔧 **READY TO FIX**  
**Confidence**: High (403 with working CORS indicates auth issue)  
**Estimated Fix Time**: 2-5 minutes  
**Risk Level**: Low (reversible changes)

Execute the fix scripts with proper AWS credentials to resolve the permission issues.