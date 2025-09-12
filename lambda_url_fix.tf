# Terraform configuration to fix Lambda Function URL permissions

resource "aws_lambda_function_url" "query_handler_url" {
  function_name      = "bedrock-agent-query-handler"
  authorization_type = "NONE"
  
  cors {
    allow_credentials = false
    allow_headers     = ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"]
    allow_methods     = ["POST", "OPTIONS"]
    allow_origins     = ["https://localhost:8501", "https://*.streamlit.app", "https://*.herokuapp.com", "*"]
    max_age          = 300
  }
}

resource "aws_lambda_permission" "allow_function_url" {
  statement_id           = "AllowPublicFunctionUrlAccess"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = "bedrock-agent-query-handler"
  principal             = "*"
  function_url_auth_type = "NONE"
}

output "function_url" {
  value = aws_lambda_function_url.query_handler_url.function_url
}
