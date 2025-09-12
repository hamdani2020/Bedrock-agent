#!/usr/bin/env python3
"""
Monitor ingestion job progress and test knowledge base
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def monitor_ingestion():
    """Monitor the latest ingestion job"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        ds_id = config['data_source_id']
        
        print(f"🔄 Monitoring ingestion for KB {kb_id}...")
        
        # Get latest ingestion job
        response = bedrock_agent.list_ingestion_jobs(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            maxResults=1
        )
        
        jobs = response.get('ingestionJobSummaries', [])
        if not jobs:
            print("❌ No ingestion jobs found")
            return False
        
        latest_job = jobs[0]
        job_id = latest_job['ingestionJobId']
        status = latest_job['status']
        
        print(f"📋 Latest Job: {job_id}")
        print(f"   Status: {status}")
        print(f"   Started: {latest_job.get('startedAt', 'Unknown')}")
        
        # If job is still running, wait a bit
        if status == 'IN_PROGRESS':
            print("⏳ Job is in progress, waiting 30 seconds...")
            time.sleep(30)
            
            # Check again
            response = bedrock_agent.list_ingestion_jobs(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                maxResults=1
            )
            jobs = response.get('ingestionJobSummaries', [])
            if jobs:
                latest_job = jobs[0]
                status = latest_job['status']
                print(f"   Updated Status: {status}")
        
        # Get detailed job info
        try:
            job_detail = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job_id
            )
            
            job_info = job_detail['ingestionJob']
            if 'statistics' in job_info:
                stats = job_info['statistics']
                print(f"   Documents Scanned: {stats.get('numberOfDocumentsScanned', 0)}")
                print(f"   Documents Indexed: {stats.get('numberOfDocumentsIndexed', 0)}")
                print(f"   Documents Failed: {stats.get('numberOfDocumentsFailed', 0)}")
            
            if 'failureReasons' in job_info and job_info['failureReasons']:
                print(f"   ⚠️  Failure Reasons: {job_info['failureReasons']}")
                
        except ClientError as e:
            print(f"   ⚠️  Could not get job details: {e}")
        
        return status == 'COMPLETE'
        
    except ClientError as e:
        print(f"❌ Error monitoring ingestion: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_knowledge_base_queries():
    """Test various queries against the knowledge base"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        
        # Test queries
        test_queries = [
            "What maintenance data is available?",
            "Show me equipment information",
            "What are the analytics results?",
            "Tell me about fault predictions"
        ]
        
        print(f"\n🧪 Testing Knowledge Base queries (ID: {kb_id})...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query}")
            
            try:
                response = bedrock_agent_runtime.retrieve(
                    knowledgeBaseId=kb_id,
                    retrievalQuery={'text': query}
                )
                
                results = response.get('retrievalResults', [])
                print(f"   ✅ Retrieved {len(results)} results")
                
                if results:
                    # Show best result
                    best_result = results[0]
                    score = best_result.get('score', 0)
                    content = best_result.get('content', {}).get('text', 'No content')
                    
                    print(f"   Best match (score: {score:.3f}):")
                    print(f"   {content[:150]}...")
                    
                    location = best_result.get('location', {})
                    if location and 's3Location' in location:
                        s3_loc = location['s3Location']
                        print(f"   Source: s3://{s3_loc.get('uri', 'unknown')}")
                
            except ClientError as e:
                print(f"   ❌ Query failed: {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error testing queries: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Monitoring Knowledge Base ingestion and testing...\n")
    
    ingestion_complete = monitor_ingestion()
    
    if ingestion_complete:
        print("\n✅ Ingestion completed successfully!")
        test_knowledge_base_queries()
    else:
        print("\n⚠️  Ingestion may still be in progress or failed")
        print("   Testing queries anyway...")
        test_knowledge_base_queries()
    
    print("\n" + "="*50)
    print("✅ Knowledge Base monitoring complete!")

if __name__ == "__main__":
    main()