"""
S3 utilities for accessing fault prediction data.
Provides simple data reading utilities for Knowledge Base integration.
"""
import boto3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class S3DataReader:
    """
    Simple S3 data reader for fault prediction data.
    Handles access to existing data in the relu-quicksight bucket.
    """
    
    def __init__(self, bucket_name: str = "relu-quicksight", region: str = "us-west-2"):
        """
        Initialize S3 client with proper configuration.
        
        Args:
            bucket_name: S3 bucket containing fault data
            region: AWS region for S3 client
        """
        self.bucket_name = bucket_name
        self.region = region
        
        try:
            # Initialize S3 client with proper configuration
            self.s3_client = boto3.client('s3', region_name=region)
            logger.info(f"S3 client initialized for bucket: {bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    def verify_bucket_access(self) -> bool:
        """
        Verify access to the S3 bucket and fault data prefix.
        
        Returns:
            bool: True if access is successful, False otherwise
        """
        try:
            # Check bucket access by listing objects with the analytics prefix
            analytics_prefix = "bedrock-recommendations/analytics/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=analytics_prefix,
                MaxKeys=1
            )
            
            if 'Contents' in response:
                logger.info(f"Successfully verified access to {self.bucket_name}/{analytics_prefix}")
                logger.info(f"Found {response.get('KeyCount', 0)} objects with analytics prefix")
                return True
            else:
                logger.warning(f"No objects found with prefix {analytics_prefix}")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                logger.error(f"Bucket {self.bucket_name} does not exist")
            elif error_code == 'AccessDenied':
                logger.error(f"Access denied to bucket {self.bucket_name}")
            else:
                logger.error(f"Client error accessing bucket: {error_code}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error verifying bucket access: {str(e)}")
            return False
    
    def list_fault_data_files(self, prefix: str = "bedrock-recommendations/analytics/", 
                             max_keys: int = 100) -> List[Dict[str, Any]]:
        """
        List fault prediction data files in S3.
        
        Args:
            prefix: S3 prefix to search for data files
            max_keys: Maximum number of files to return
            
        Returns:
            List of dictionaries containing file metadata
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag'].strip('"')
                    })
            
            logger.info(f"Found {len(files)} fault data files with prefix {prefix}")
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files: {e.response['Error']['Code']}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing files: {str(e)}")
            return []
    
    def read_fault_data_file(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Read a single fault prediction data file from S3.
        
        Args:
            s3_key: S3 key of the file to read
            
        Returns:
            Dictionary containing the fault data, or None if error
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # Read and parse JSON content
            content = response['Body'].read().decode('utf-8')
            data = json.loads(content)
            
            logger.debug(f"Successfully read file: {s3_key}")
            return data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"File not found: {s3_key}")
            else:
                logger.error(f"Error reading file {s3_key}: {error_code}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {s3_key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading file {s3_key}: {str(e)}")
            return None
    
    def get_recent_fault_data(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent fault prediction data for Knowledge Base integration.
        
        Args:
            days: Number of recent days to search
            limit: Maximum number of records to return
            
        Returns:
            List of fault data records
        """
        try:
            # List recent files (S3 doesn't have native date filtering, so we'll use prefix patterns)
            current_date = datetime.now(timezone.utc)
            
            # Try to get files from recent dates by constructing prefixes
            fault_records = []
            
            # Get files from analytics prefix (these are optimized for analysis)
            files = self.list_fault_data_files(
                prefix="bedrock-recommendations/analytics/",
                max_keys=limit * 2  # Get more files to filter
            )
            
            # Sort by last modified date (most recent first)
            files.sort(key=lambda x: x['last_modified'], reverse=True)
            
            # Read the most recent files up to the limit
            for file_info in files[:limit]:
                data = self.read_fault_data_file(file_info['key'])
                if data:
                    # Add file metadata for tracking
                    data['_s3_metadata'] = {
                        'key': file_info['key'],
                        'size': file_info['size'],
                        'last_modified': file_info['last_modified']
                    }
                    fault_records.append(data)
            
            logger.info(f"Retrieved {len(fault_records)} recent fault data records")
            return fault_records
            
        except Exception as e:
            logger.error(f"Error getting recent fault data: {str(e)}")
            return []
    
    def validate_data_structure(self, sample_size: int = 5) -> Dict[str, Any]:
        """
        Validate the structure of fault prediction data for Knowledge Base compatibility.
        
        Args:
            sample_size: Number of files to sample for validation
            
        Returns:
            Dictionary containing validation results
        """
        try:
            files = self.list_fault_data_files(max_keys=sample_size)
            
            validation_results = {
                'total_files_checked': len(files),
                'valid_files': 0,
                'invalid_files': 0,
                'common_fields': set(),
                'sample_records': [],
                'errors': []
            }
            
            for file_info in files:
                data = self.read_fault_data_file(file_info['key'])
                
                if data:
                    validation_results['valid_files'] += 1
                    validation_results['sample_records'].append({
                        'file': file_info['key'],
                        'fields': list(data.keys()),
                        'record_type': data.get('record_type', 'unknown'),
                        'timestamp': data.get('timestamp'),
                        'fault_category': data.get('fault_category', data.get('predicted_fault'))
                    })
                    
                    # Track common fields across files
                    if validation_results['common_fields']:
                        validation_results['common_fields'] &= set(data.keys())
                    else:
                        validation_results['common_fields'] = set(data.keys())
                else:
                    validation_results['invalid_files'] += 1
                    validation_results['errors'].append(f"Failed to read: {file_info['key']}")
            
            # Convert set to list for JSON serialization
            validation_results['common_fields'] = list(validation_results['common_fields'])
            
            logger.info(f"Data validation completed: {validation_results['valid_files']} valid, "
                       f"{validation_results['invalid_files']} invalid files")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error during data validation: {str(e)}")
            return {
                'error': str(e),
                'total_files_checked': 0,
                'valid_files': 0,
                'invalid_files': 0
            }


def create_s3_reader(bucket_name: str = None, region: str = None) -> S3DataReader:
    """
    Factory function to create S3DataReader with default configuration.
    
    Args:
        bucket_name: Override default bucket name
        region: Override default region
        
    Returns:
        Configured S3DataReader instance
    """
    # Use defaults from config if not provided
    default_bucket = "relu-quicksight"
    default_region = "us-west-2"
    
    return S3DataReader(
        bucket_name=bucket_name or default_bucket,
        region=region or default_region
    )