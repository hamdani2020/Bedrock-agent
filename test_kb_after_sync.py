#!/usr/bin/env python3
"""
Test Knowledge Base after syncing complete maintenance data
"""

import boto3
import json
import time
import uuid
from botocore.exceptions import ClientError

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def wait_for_ingestion():
    """Wait for the latest ingestion job to complete"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        ds_id = config['data_source_id']
        
        print(f"⏳ Waiting for ingestion to complete...")
        
        max_wait = 300  # 5 minutes
        wait_interval = 20
        elapsed = 0
        
        while elapsed < max_wait:
            time.sleep(wait_interval)
            elapsed += wait_interval
            
            # Check latest job status
            response = bedrock_agent.list_ingestion_jobs(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                maxResults=1
            )
            
            jobs = response.get('ingestionJobSummaries', [])
            if jobs:
                latest_job = jobs[0]
                status = latest_job['status']
                
                print(f"   Status after {elapsed}s: {status}")
                
                if status == 'COMPLETE':
                    print("   ✅ Ingestion completed!")
                    
                    # Get job details
                    job_id = latest_job['ingestionJobId']
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
                        print(f"   ⚠️  Could not get job details: {e}")
                    
                    return True
                    
                elif status == 'FAILED':
                    print("   ❌ Ingestion failed!")
                    return False
        
        print("   ⚠️  Ingestion taking longer than expected")
        return False
        
    except ClientError as e:
        print(f"❌ Error waiting for ingestion: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_comprehensive_kb_queries():
    """Test comprehensive queries against the updated knowledge base"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        
        # Comprehensive test queries based on the new data
        test_queries = [
            "What is the current status of the industrial conveyor?",
            "What fault was detected in the equipment?",
            "What are the current sensor readings for temperature and vibration?",
            "What maintenance actions are recommended?",
            "Is the equipment in normal operation?",
            "What is the risk level of the detected fault?",
            "What are the ball bearing issues found?",
            "What preventive maintenance procedures should be followed?",
            "What are the current RPM and load readings?",
            "Does the equipment require immediate action?"
        ]
        
        print(f"\n🧪 Testing Knowledge Base with comprehensive queries...")
        print(f"   Knowledge Base ID: {kb_id}")
        print("="*60)
        
        successful_queries = 0
        high_confidence_results = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Query {i}: {query}")
            print("-" * 50)
            
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
                    
                    if score > 0.7:
                        high_confidence_results += 1
                        confidence_indicator = "🎯 HIGH"
                    elif score > 0.5:
                        confidence_indicator = "✅ GOOD"
                    else:
                        confidence_indicator = "⚠️  LOW"
                    
                    print(f"   📊 Best match ({confidence_indicator} confidence: {score:.3f}):")
                    
                    # Show relevant excerpt
                    if len(content) > 200:
                        # Try to find the most relevant part
                        query_words = query.lower().split()
                        content_lower = content.lower()
                        
                        best_start = 0
                        best_score = 0
                        
                        for start in range(0, len(content) - 200, 50):
                            excerpt = content_lower[start:start + 200]
                            word_matches = sum(1 for word in query_words if word in excerpt)
                            if word_matches > best_score:
                                best_score = word_matches
                                best_start = start
                        
                        excerpt = content[best_start:best_start + 200]
                        print(f"   📄 {excerpt}...")
                    else:
                        print(f"   📄 {content}")
                    
                    location = best_result.get('location', {})
                    if location and 's3Location' in location:
                        s3_uri = location['s3Location'].get('uri', 'unknown')
                        filename = s3_uri.split('/')[-1] if '/' in s3_uri else s3_uri
                        print(f"   📁 Source: {filename}")
                else:
                    print("   ⚠️  No results found")
                
            except ClientError as e:
                print(f"   ❌ Query failed: {e}")
        
        print("\n" + "="*60)
        print("📊 KNOWLEDGE BASE TEST RESULTS:")
        print(f"   Successful Queries: {successful_queries}/{len(test_queries)}")
        print(f"   High Confidence Results: {high_confidence_results}/{len(test_queries)}")
        
        success_rate = (successful_queries / len(test_queries)) * 100
        confidence_rate = (high_confidence_results / len(test_queries)) * 100
        
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   High Confidence Rate: {confidence_rate:.1f}%")
        
        if success_rate >= 90 and confidence_rate >= 50:
            print("   🎉 EXCELLENT: Knowledge Base is working perfectly!")
        elif success_rate >= 80:
            print("   ✅ GOOD: Knowledge Base is working well")
        else:
            print("   ⚠️  NEEDS IMPROVEMENT: Some queries not working as expected")
        
        return success_rate >= 80
        
    except ClientError as e:
        print(f"❌ Error testing KB: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_agent_integration():
    """Test agent integration with the updated knowledge base"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        agent_alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        # Test query that should definitely use the KB
        test_query = "Based on the maintenance analytics data, what is the current condition of the industrial conveyor and what actions should I take?"
        
        print(f"\n🤖 Testing Agent Integration...")
        print(f"   Query: {test_query}")
        print("-" * 60)
        
        session_id = str(uuid.uuid4())
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=test_query
        )
        
        # Process response
        full_response = ""
        kb_used = False
        kb_sources = []
        
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    full_response += chunk_text
            
            elif 'trace' in event:
                trace = event['trace']
                if 'trace' in trace:
                    trace_data = trace['trace']
                    
                    # Check for knowledge base retrieval
                    if 'orchestrationTrace' in trace_data:
                        orch_trace = trace_data['orchestrationTrace']
                        if 'observation' in orch_trace:
                            obs = orch_trace['observation']
                            if 'knowledgeBaseLookupOutput' in obs:
                                kb_output = obs['knowledgeBaseLookupOutput']
                                retrieved_refs = kb_output.get('retrievedReferences', [])
                                if retrieved_refs:
                                    kb_used = True
                                    for ref in retrieved_refs:
                                        location = ref.get('location', {})
                                        if 's3Location' in location:
                                            s3_uri = location['s3Location'].get('uri', 'unknown')
                                            filename = s3_uri.split('/')[-1] if '/' in s3_uri else s3_uri
                                            kb_sources.append(filename)
        
        print(f"   ✅ Response Length: {len(full_response)} characters")
        
        if kb_used:
            print(f"   🎉 SUCCESS: Agent used Knowledge Base!")
            print(f"   📚 Sources: {len(set(kb_sources))} unique documents")
            for source in set(kb_sources)[:3]:
                print(f"      📄 {source}")
            
            print(f"\n   📝 Agent Response:")
            print(f"      {full_response[:400]}...")
            
            return True
        else:
            print(f"   ⚠️  Agent did not use Knowledge Base")
            print(f"   📝 Response: {full_response[:200]}...")
            return False
        
    except ClientError as e:
        print(f"❌ Error testing agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🎯 COMPREHENSIVE KNOWLEDGE BASE TEST AFTER DATA SYNC")
    print("="*60)
    
    # Wait for ingestion to complete
    if wait_for_ingestion():
        print("\n" + "="*60)
        # Test KB queries
        kb_success = test_comprehensive_kb_queries()
        
        if kb_success:
            print("\n" + "="*60)
            # Test agent integration
            test_agent_integration()
    
    print("\n" + "="*60)
    print("✅ COMPREHENSIVE TEST COMPLETE!")

if __name__ == "__main__":
    main()