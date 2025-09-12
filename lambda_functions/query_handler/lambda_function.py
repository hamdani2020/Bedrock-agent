"""
Lambda function for handling Bedrock Agent queries.
Processes incoming queries and manages agent interactions.
"""
import json
import boto3
import logging
import os
import uuid
from typing import Dict, Any
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Hardcoded configuration (more reliable than environment variables)
BEDROCK_AGENT_ID = 'GMJGK6RO4S'
BEDROCK_AGENT_ALIAS_ID = 'RUWFC5DRPQ'

def invoke_bedrock_agent(query: str, session_id: str) -> str:
    """
    Invoke Bedrock Agent with the given query.
    
    Args:
        query: User query string
        session_id: Session identifier
        
    Returns:
        Agent response text
    """
    try:
        logger.info(f"Invoking Bedrock Agent - Agent ID: {BEDROCK_AGENT_ID}, Alias: {BEDROCK_AGENT_ALIAS_ID}")
        logger.info(f"Query length: {len(query)} characters, Session: {session_id}")
        
        # Validate input parameters
        if not query.strip():
            logger.warning("Empty query received")
            return "Please provide a valid question about equipment maintenance."
        
        if len(query) > 10000:  # Reasonable limit
            logger.warning(f"Query too long: {len(query)} characters")
            return "Your question is too long. Please keep it under 10,000 characters."
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=query
        )
        
        # Process the streaming response with timeout handling
        full_response = ""
        chunk_count = 0
        
        for event in response['completion']:
            chunk_count += 1
            
            # Prevent infinite loops
            if chunk_count > 1000:
                logger.warning("Too many response chunks, truncating")
                break
                
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    full_response += chunk_text
                    
                    # Prevent extremely long responses
                    if len(full_response) > 50000:
                        logger.warning("Response too long, truncating")
                        full_response += "\n\n[Response truncated due to length]"
                        break
        
        logger.info(f"Agent response: {len(full_response)} characters, {chunk_count} chunks")
        
        if full_response.strip():
            return full_response.strip()
        else:
            logger.warning("Empty response from Bedrock Agent")
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question or check if the maintenance system is available."
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        logger.error(f"AWS ClientError: {error_code} - {error_message}")
        
        if error_code == 'ValidationException':
            return "There was an issue with your request format. Please try again."
        elif error_code == 'AccessDeniedException':
            return "I don't have permission to access the maintenance system. Please contact support."
        elif error_code == 'ThrottlingException':
            return "The system is currently busy. Please wait a moment and try again."
        elif error_code == 'ResourceNotFoundException':
            return "The maintenance system is temporarily unavailable. Please try again later."
        else:
            return "I encountered a technical issue. Please try again in a few moments."
            
    except Exception as e:
        logger.error(f"Unexpected error invoking Bedrock Agent: {str(e)}", exc_info=True)
        return "I'm sorry, but I encountered an unexpected error. Please try again later."

def validate_request_origin(event: Dict[str, Any]) -> bool:
    """Validate request origin for security."""
    allowed_origins = [
        'https://localhost:8501',
        'https://*.streamlit.app',
        'https://*.herokuapp.com'
    ]
    
    origin = event.get('headers', {}).get('origin', '')
    if not origin:
        return True  # Allow requests without origin header (direct API calls)
    
    # Simple origin validation (in production, use more sophisticated matching)
    for allowed in allowed_origins:
        if allowed == '*' or origin == allowed or (allowed.startswith('https://*.') and origin.endswith(allowed[9:])):
            return True
    
    return False

def get_cors_headers(event: Dict[str, Any]) -> Dict[str, str]:
    """Get appropriate CORS headers based on request origin."""
    origin = event.get('headers', {}).get('origin', '')
    
    # Validate origin and set appropriate CORS headers
    if validate_request_origin(event):
        allowed_origin = origin if origin else 'https://localhost:8501'
    else:
        allowed_origin = 'null'  # Reject invalid origins
    
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': allowed_origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key',
        'Access-Control-Expose-Headers': 'X-Amz-Request-Id',
        'Access-Control-Max-Age': '300',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing Bedrock Agent queries.
    
    Args:
        event: Lambda event containing query data
        context: Lambda context object
        
    Returns:
        Dict containing response data
    """
    # Get secure CORS headers
    cors_headers = get_cors_headers(event)
    
    try:
        # Log request details for debugging
        logger.info(f"Lambda invocation - Request ID: {context.aws_request_id}")
        logger.info(f"Event keys: {list(event.keys())}")
        
        # Handle CORS preflight requests
        if event.get('httpMethod') == 'OPTIONS' or event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Validate request origin for security
        if not validate_request_origin(event):
            logger.warning(f"Invalid origin: {event.get('headers', {}).get('origin', 'unknown')}")
            return {
                'statusCode': 403,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Forbidden',
                    'message': 'Invalid request origin'
                })
            }
        
        # Validate required environment variables early
        if not BEDROCK_AGENT_ID or not BEDROCK_AGENT_ALIAS_ID:
            logger.error("Missing required environment variables")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Service configuration error',
                    'message': 'The maintenance system is not properly configured. Please contact support.'
                })
            }
        
        # Parse request body with error handling
        try:
            body_str = event.get('body', '{}')
            if isinstance(body_str, str):
                body = json.loads(body_str)
            else:
                body = body_str
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {e}")
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Invalid request format',
                    'message': 'Request body must be valid JSON'
                })
            }
        
        # Extract and validate parameters
        query = body.get('query', '').strip()
        session_id = body.get('sessionId', '').strip()
        
        if not query:
            logger.warning("Empty query received")
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Missing query parameter',
                    'message': 'Please provide a question about equipment maintenance'
                })
            }
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session ID: {session_id}")
        
        logger.info(f"Processing query: {query[:100]}... (Session: {session_id})")
        
        # Check remaining execution time
        remaining_time = context.get_remaining_time_in_millis()
        if remaining_time < 10000:  # Less than 10 seconds
            logger.warning(f"Low remaining time: {remaining_time}ms")
            return {
                'statusCode': 503,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Service timeout',
                    'message': 'The request is taking too long. Please try again.'
                })
            }
        
        # Invoke Bedrock Agent
        response_text = invoke_bedrock_agent(query, session_id)
        
        # Log successful response
        logger.info(f"Successfully processed query - Response length: {len(response_text)}")
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'response': response_text,
                'sessionId': session_id,
                'timestamp': context.aws_request_id
            })
        }
        
    except json.JSONEncodeError as e:
        logger.error(f"Error encoding response JSON: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Response encoding error',
                'message': 'Unable to format response properly'
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred. Please try again later.'
            })
        }