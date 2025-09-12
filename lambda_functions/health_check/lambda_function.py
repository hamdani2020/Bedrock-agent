"""
Lambda function for system health monitoring.
Provides health check endpoint for monitoring system status.
"""
import json
import boto3
import logging
import os
from typing import Dict, Any
from datetime import datetime, timezone

# Add shared utilities to path
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.s3_utils import create_s3_reader

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
bedrock_agent = boto3.client('bedrock-agent')
s3_reader = create_s3_reader()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for health checks.
    
    Args:
        event: Lambda event
        context: Lambda context object
        
    Returns:
        Dict containing health status
    """
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0',
            'services': {}
        }
        
        # Check S3 data access
        try:
            s3_access = s3_reader.verify_bucket_access()
            health_status['services']['s3_access'] = {
                'status': 'healthy' if s3_access else 'unhealthy',
                'message': 'S3 bucket access verified' if s3_access else 'S3 bucket access failed'
            }
        except Exception as e:
            health_status['services']['s3_access'] = {
                'status': 'unhealthy',
                'message': f'S3 access check failed: {str(e)}'
            }
        
        # Check data availability
        try:
            files = s3_reader.list_fault_data_files(max_keys=1)
            health_status['services']['data_availability'] = {
                'status': 'healthy' if files else 'warning',
                'message': f'Found {len(files)} data files' if files else 'No data files found'
            }
        except Exception as e:
            health_status['services']['data_availability'] = {
                'status': 'unhealthy',
                'message': f'Data availability check failed: {str(e)}'
            }
        
        # Check Bedrock Agent
        try:
            agent_id = os.getenv('BEDROCK_AGENT_ID')
            if agent_id:
                agent_response = bedrock_agent.get_agent(agentId=agent_id)
                agent_status = agent_response['agent']['agentStatus']
                
                health_status['services']['bedrock_agent'] = {
                    'status': 'healthy' if agent_status == 'PREPARED' else 'warning',
                    'message': f'Agent status: {agent_status}',
                    'agent_id': agent_id
                }
            else:
                health_status['services']['bedrock_agent'] = {
                    'status': 'warning',
                    'message': 'Bedrock Agent ID not configured'
                }
        except Exception as e:
            health_status['services']['bedrock_agent'] = {
                'status': 'unhealthy',
                'message': f'Bedrock Agent check failed: {str(e)}'
            }
        
        # Check Knowledge Base
        try:
            kb_id = os.getenv('KNOWLEDGE_BASE_ID')
            if kb_id:
                kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
                kb_status = kb_response['knowledgeBase']['status']
                
                health_status['services']['knowledge_base'] = {
                    'status': 'healthy' if kb_status == 'ACTIVE' else 'warning',
                    'message': f'Knowledge Base status: {kb_status}',
                    'kb_id': kb_id
                }
            else:
                health_status['services']['knowledge_base'] = {
                    'status': 'warning',
                    'message': 'Knowledge Base ID not configured'
                }
        except Exception as e:
            health_status['services']['knowledge_base'] = {
                'status': 'unhealthy',
                'message': f'Knowledge Base check failed: {str(e)}'
            }
        
        # Overall status based on checks
        unhealthy_services = [svc for svc in health_status['services'].values() 
                             if svc['status'] == 'unhealthy']
        
        if unhealthy_services:
            health_status['status'] = 'unhealthy'
        elif any(svc['status'] == 'warning' for svc in health_status['services'].values()):
            health_status['status'] = 'warning'
        
        status_code = 200 if health_status['status'] in ['healthy', 'warning'] else 503
        
        logger.info(f"Health check completed with status: {health_status['status']}")
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(health_status)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }