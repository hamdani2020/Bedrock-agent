#!/usr/bin/env python3
"""
Create S3 Data Retrieval Function

This script creates a Lambda function that the Bedrock Agent can call to retrieve
data directly from S3, bypassing the need for a Knowledge Base.
"""

import json
import boto3
import zipfile
import io
from botocore.exceptions import ClientError

def create_s3_data_function():
    """Create Lambda function for S3 data retrieval"""
    
    # Load config
    with open("config/aws_config.json", 'r') as f:
        config = json.load(f)
    
    region = config["region"]
    
    # Initialize clients
    lambda_client = boto3.client('lambda', region_name=region)
    iam_client = boto3.client('iam', region_name=region)
    sts_client = boto3.client('sts', region_name=region)
    
    account_id = sts_client.get_caller_identity()['Account']
    
    # Function code
    function_code = '''
import json
import boto3
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Retrieve maintenance data from S3 based on query parameters
    """
    try:
        # Parse the input
        query = event.get('query', '').lower()
        date_range = event.get('date_range', 7)  # Default 7 days
        
        # S3 configuration
        bucket_name = 'relu-quicksight'
        prefix = 'bedrock-recommendations/analytics/'
        
        s3_client = boto3.client('s3')
        
        # Get recent data files
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range)
        
        relevant_data = []
        
        # List objects in the date range
        for i in range(date_range):
            current_date = start_date + timedelta(days=i)
            date_prefix = f"{prefix}{current_date.strftime('%Y/%m/%d')}/"
            
            try:
                response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=date_prefix,
                    MaxKeys=10  # Limit to avoid timeout
                )
                
                for obj in response.get('Contents', []):
                    # Get object content
                    try:
                        obj_response = s3_client.get_object(
                            Bucket=bucket_name,
                            Key=obj['Key']
                        )
                        
                        content = obj_response['Body'].read().decode('utf-8')
                        data = json.loads(content)
                        
                        # Filter data based on query
                        if is_relevant_data(data, query):
                            relevant_data.append({
                                'file': obj['Key'],
                                'date': obj['LastModified'].isoformat(),
                                'data': data
                            })
                            
                    except Exception as e:
                        logger.warning(f"Failed to process {obj['Key']}: {e}")
                        continue
                        
            except ClientError as e:
                logger.warning(f"Failed to list objects for {date_prefix}: {e}")
                continue
        
        # Format response
        return {
            'statusCode': 200,
            'body': {
                'query': query,
                'results_count': len(relevant_data),
                'data': relevant_data[:5],  # Limit results
                'summary': generate_summary(relevant_data, query)
            }
        }
        
    except Exception as e:
        logger.error(f"Function error: {e}")
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }

def is_relevant_data(data, query):
    """Check if data is relevant to the query"""
    if not query:
        return True
    
    # Convert data to string for searching
    data_str = json.dumps(data).lower()
    
    # Common maintenance keywords
    maintenance_keywords = [
        'fault', 'failure', 'bearing', 'pump', 'temperature', 
        'vibration', 'pressure', 'maintenance', 'repair', 'critical'
    ]
    
    # Check if query matches data content
    if query in data_str:
        return True
    
    # Check for maintenance-related content
    for keyword in maintenance_keywords:
        if keyword in query and keyword in data_str:
            return True
    
    return False

def generate_summary(data, query):
    """Generate a summary of the retrieved data"""
    if not data:
        return "No relevant maintenance data found for the specified query."
    
    summary = f"Found {len(data)} relevant maintenance records"
    if query:
        summary += f" related to '{query}'"
    
    # Add basic statistics
    dates = [item['date'] for item in data]
    if dates:
        summary += f". Data spans from recent maintenance activities."
    
    return summary
'''
    
    try:
        # Create IAM role for Lambda function
        role_name = "s3-data-retrieval-role"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:{region}:*:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::relu-quicksight",
                        "arn:aws:s3:::relu-quicksight/*"
                    ]
                }
            ]
        }
        
        # Create role
        try:
            role_response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for S3 data retrieval Lambda function"
            )
            role_arn = role_response['Role']['Arn']
            print(f"✅ Created IAM role: {role_arn}")
        except ClientError as e:
            if 'EntityAlreadyExists' in str(e):
                role = iam_client.get_role(RoleName=role_name)
                role_arn = role['Role']['Arn']
                print(f"✅ Using existing IAM role: {role_arn}")
            else:
                raise
        
        # Attach policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{role_name}-policy",
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        # Create deployment package
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_function.py', function_code)
        
        zip_buffer.seek(0)
        
        # Create Lambda function
        function_name = "s3-maintenance-data-retrieval"
        
        try:
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_buffer.read()},
                Description='Retrieve maintenance data from S3 for Bedrock Agent',
                Timeout=60,
                MemorySize=256,
                Environment={
                    'Variables': {
                        'S3_BUCKET': 'relu-quicksight',
                        'S3_PREFIX': 'bedrock-recommendations/analytics/'
                    }
                }
            )
            
            function_arn = response['FunctionArn']
            print(f"✅ Created Lambda function: {function_arn}")
            
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                # Function already exists, update it
                lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_buffer.read()
                )
                
                response = lambda_client.get_function(FunctionName=function_name)
                function_arn = response['Configuration']['FunctionArn']
                print(f"✅ Updated existing Lambda function: {function_arn}")
            else:
                raise
        
        # Test the function
        print("🧪 Testing Lambda function...")
        test_payload = {
            'query': 'bearing fault',
            'date_range': 7
        }
        
        test_response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(test_response['Payload'].read())
        print(f"✅ Test result: {result}")
        
        return function_arn
        
    except Exception as e:
        print(f"❌ Failed to create S3 data function: {e}")
        return None

def main():
    """Main execution function"""
    try:
        function_arn = create_s3_data_function()
        
        if function_arn:
            print(f"\n🎉 S3 Data Retrieval Function created successfully!")
            print(f"Function ARN: {function_arn}")
            print(f"\nThis function can be called by the Bedrock Agent to retrieve")
            print(f"maintenance data directly from S3 without needing a Knowledge Base.")
            return 0
        else:
            print(f"\n❌ Failed to create S3 data function")
            return 1
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())