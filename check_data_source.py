#!/usr/bin/env python3
"""
Check data source status and trigger ingestion if needed
"""

import boto3
import json
from botocore.exceptions import ClientError

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def check_data_source():
    """Check data source status and ingestion jobs"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        ds_id = config['data_source_id']
        
        print(f"🔍 Checking data source {ds_id} in KB {kb_id}...")
        
        # Get data source details
        response = bedrock_agent.get_data_source(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        
        data_source = response['dataSource']
        print(f"✅ Data Source: {data_source['name']}")
        print(f"   Status: {data_source['status']}")
        print(f"   Created: {data_source.get('createdAt', 'Unknown')}")
        print(f"   Updated: {data_source.get('updatedAt', 'Unknown')}")
        
        # Check data source configuration
        ds_config = data_source.get('dataSourceConfiguration', {})
        if ds_config:
            ds_type = ds_config.get('type', 'Unknown')
            print(f"   Type: {ds_type}")
            
            if ds_type == 'S3':
                s3_config = ds_config.get('s3Configuration', {})
                bucket_arn = s3_config.get('bucketArn', 'Not specified')
                print(f"   S3 Bucket ARN: {bucket_arn}")
                
                inclusion_prefixes = s3_config.get('inclusionPrefixes', [])
                if inclusion_prefixes:
                    print(f"   Inclusion Prefixes: {inclusion_prefixes}")
        
        # Check ingestion jobs
        print(f"\n🔄 Checking ingestion jobs...")
        jobs_response = bedrock_agent.list_ingestion_jobs(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            maxResults=10
        )
        
        jobs = jobs_response.get('ingestionJobSummaries', [])
        if jobs:
            print(f"✅ Found {len(jobs)} ingestion job(s)")
            for job in jobs:
                print(f"   Job ID: {job['ingestionJobId']}")
                print(f"   Status: {job['status']}")
                print(f"   Started: {job.get('startedAt', 'Unknown')}")
                print(f"   Updated: {job.get('updatedAt', 'Unknown')}")
                
                if 'statistics' in job:
                    stats = job['statistics']
                    print(f"   Documents: {stats.get('numberOfDocumentsScanned', 0)} scanned, "
                          f"{stats.get('numberOfDocumentsIndexed', 0)} indexed")
        else:
            print("⚠️  No ingestion jobs found")
            
            # Trigger ingestion
            print("\n🚀 Starting ingestion job...")
            try:
                ingestion_response = bedrock_agent.start_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id,
                    description="Manual ingestion trigger"
                )
                
                job_id = ingestion_response['ingestionJob']['ingestionJobId']
                print(f"✅ Started ingestion job: {job_id}")
                
            except ClientError as e:
                print(f"❌ Failed to start ingestion: {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error checking data source: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_s3_data():
    """Check if there's data in the S3 bucket"""
    config = load_config()
    if not config:
        return False
    
    try:
        s3 = boto3.client('s3', region_name=config['region'])
        
        bucket_name = config['s3']['data_bucket']['name']
        prefix = config['s3']['data_bucket']['data_structure']['base_prefix']
        
        print(f"\n📁 Checking S3 data in bucket: {bucket_name}")
        print(f"   Prefix: {prefix}")
        
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            MaxKeys=10
        )
        
        objects = response.get('Contents', [])
        if objects:
            print(f"✅ Found {len(objects)} objects (showing first 10)")
            for obj in objects[:5]:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("⚠️  No objects found with this prefix")
            
            # Check if bucket exists and list some contents
            try:
                response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
                all_objects = response.get('Contents', [])
                if all_objects:
                    print(f"   But bucket has {len(all_objects)} total objects:")
                    for obj in all_objects[:5]:
                        print(f"   - {obj['Key']}")
                else:
                    print("   Bucket is empty")
            except ClientError as e:
                print(f"   ❌ Cannot access bucket: {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error checking S3: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Checking Knowledge Base data source...\n")
    
    check_data_source()
    check_s3_data()
    
    print("\n" + "="*50)
    print("✅ Data source check complete!")

if __name__ == "__main__":
    main()