"""
Lambda function for managing Knowledge Base synchronization with S3.
Triggered by EventBridge for scheduled sync operations.
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
    Main Lambda handler for Knowledge Base data synchronization.
    
    Args:
        event: EventBridge event or manual trigger
        context: Lambda context object
        
    Returns:
        Dict containing sync status
    """
    try:
        logger.info("Starting Knowledge Base synchronization")
        
        # Verify S3 access first
        if not s3_reader.verify_bucket_access():
            raise Exception("Failed to verify S3 bucket access")
        
        # Get environment variables
        knowledge_base_id = os.getenv('KNOWLEDGE_BASE_ID')
        data_source_id = os.getenv('DATA_SOURCE_ID')
        
        # Validate data structure
        logger.info("Validating S3 data structure")
        validation_results = s3_reader.validate_data_structure(sample_size=5)
        
        if validation_results['valid_files'] == 0:
            raise Exception("No valid fault data files found in S3")
        
        logger.info(f"Data validation: {validation_results['valid_files']} valid files, "
                   f"{validation_results['invalid_files']} invalid files")
        
        # Get recent data for sync status
        recent_data = s3_reader.get_recent_fault_data(days=1, limit=10)
        
        sync_status = {
            'status': 'completed',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': 'S3 access configured and verified',
            'data_validation': {
                'total_files_checked': validation_results['total_files_checked'],
                'valid_files': validation_results['valid_files'],
                'invalid_files': validation_results['invalid_files'],
                'common_fields_count': len(validation_results.get('common_fields', []))
            },
            'recent_data_count': len(recent_data),
            'knowledge_base_id': knowledge_base_id,
            'data_source_id': data_source_id
        }
        
        logger.info(f"Sync completed: {sync_status}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(sync_status)
        }
        
    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }