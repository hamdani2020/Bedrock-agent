#!/usr/bin/env python3
"""
Test Knowledge Base ingestion with text files
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

def trigger_ingestion():
    """Trigger new ingestion job for text files"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        ds_id = config['data_source_id']
        
        print(f"🚀 Starting new ingestion job for text files...")
        print(f"   Knowledge Base: {kb_id}")
        print(f"   Data Source: {ds_id}")
        
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            description="Ingestion of converted text files and maintenance documents"
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"   ✅ Started ingestion job: {job_id}")
        
        # Wait for ingestion to complete
        print("   ⏳ Waiting for ingestion to complete...")
        
        max_wait_time = 300  # 5 minutes
        wait_interval = 30   # 30 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(wait_interval)
            elapsed_time += wait_interval
            
            # Check job status
            jobs_response = bedrock_agent.list_ingestion_jobs(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                maxResults=1
            )
            
            jobs = jobs_response.get('ingestionJobSummaries', [])
            if jobs:
                latest_job = jobs[0]
                status = latest_job['status']
                
                print(f"   Status after {elapsed_time}s: {status}")
                
                if status == 'COMPLETE':
                    print("   ✅ Ingestion completed successfully!")
                    
                    # Get detailed statistics
                    try:
                        job_detail = bedrock_agent.get_ingestion_job(
                            knowledgeBaseId=kb_id,
                            dataSourceId=ds_id,
                            ingestionJobId=job_id
                        )
                        
                        job_info = job_detail['ingestionJob']
                        if 'statistics' in job_info:
                            stats = job_info['statistics']
                            print(f"   📊 Documents Scanned: {stats.get('numberOfDocumentsScanned', 0)}")
                            print(f"   📊 Documents Indexed: {stats.get('numberOfDocumentsIndexed', 0)}")
                            print(f"   📊 Documents Failed: {stats.get('numberOfDocumentsFailed', 0)}")
                    except Exception as e:
                        print(f"   ⚠️  Could not get detailed stats: {e}")
                    
                    return True
                    
                elif status == 'FAILED':
                    print("   ❌ Ingestion failed!")
                    return False
        
        print("   ⚠️  Ingestion taking longer than expected")
        return False
        
    except ClientError as e:
        print(f"❌ Error starting ingestion: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_text_queries():
    """Test queries against the text-based knowledge base"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        
        # Test queries specifically for text content
        test_queries = [
            "What are the preventive maintenance procedures?",
            "How do I diagnose equipment faults?",
            "What are the maintenance best practices?",
            "What sensor readings indicate potential problems?",
            "What are the fault prediction results?",
            "What maintenance recommendations are provided?",
            "How often should I perform equipment inspections?",
            "What are the safety procedures for maintenance?"
        ]
        
        print(f"\n🧪 Testing Knowledge Base with text queries...")
        print(f"   Knowledge Base ID: {kb_id}")
        
        successful_queries = 0
        
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
                    successful_queries += 1
                    
                    # Show best result
                    best_result = results[0]
                    score = best_result.get('score', 0)
                    content = best_result.get('content', {}).get('text', 'No content')
                    
                    print(f"   📊 Best match (score: {score:.3f}):")
                    print(f"   📄 {content[:200]}...")
                    
                    location = best_result.get('location', {})
                    if location and 's3Location' in location:
                        s3_uri = location['s3Location'].get('uri', 'unknown')
                        print(f"   📁 Source: {s3_uri}")
                else:
                    print("   ⚠️  No results found")
                
            except ClientError as e:
                print(f"   ❌ Query failed: {e}")
        
        print(f"\n📊 Summary: {successful_queries}/{len(test_queries)} queries returned results")
        return successful_queries > 0
        
    except ClientError as e:
        print(f"❌ Error testing queries: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Testing Knowledge Base with text files...\n")
    
    # Trigger ingestion of text files
    ingestion_success = trigger_ingestion()
    
    if ingestion_success:
        print("\n" + "="*50)
        # Test queries
        test_text_queries()
    else:
        print("\n⚠️  Ingestion may have failed, testing anyway...")
        test_text_queries()
    
    print("\n" + "="*50)
    print("✅ Text ingestion test complete!")

if __name__ == "__main__":
    main()