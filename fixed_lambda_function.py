import json
import boto3
import logging
import uuid
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

BEDROCK_AGENT_ID = 'GMJGK6RO4S'
BEDROCK_AGENT_ALIAS_ID = 'RUWFC5DRPQ'

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '').strip()
        session_id = body.get('sessionId', str(uuid.uuid4()))
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing query'})
            }
        
        logger.info(f"Invoking agent with query: {query[:100]}")
        
        # Invoke Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=query
        )
        
        # Process streaming response
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event and 'bytes' in event['chunk']:
                chunk_text = event['chunk']['bytes'].decode('utf-8')
                full_response += chunk_text
        
        logger.info(f"Agent response length: {len(full_response)}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'response': full_response,
                'sessionId': session_id
            })
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"Bedrock error: {error_code} - {e.response['Error']['Message']}")
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'error': f'Bedrock error: {error_code}',
                'message': e.response['Error']['Message']
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'error': 'Internal error',
                'message': str(e)
            })
        }