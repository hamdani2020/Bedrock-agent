#!/usr/bin/env python3
"""
Test specific queries to see what data the agent can actually retrieve.
"""
import boto3
import json
import uuid

def test_agent_queries():
    """Test different query variations to see what works."""
    
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    # Different query variations to test
    queries = [
        "Show me data for conveyor_motor_001",
        "What are the latest reports for conveyor motor 001?",
        "Show me device data from September 11, 2025",
        "What maintenance data do you have for conveyor systems?",
        "Show me analytics data for equipment with timestamps",
        "What fault predictions do you have for conveyor motors?",
        "Show me the most recent equipment reports",
        "What device reports are available with RPM and temperature data?",
        "Show me maintenance recommendations for conveyor_motor_001",
        "What equipment data do you have from today?"
    ]
    
    print("Testing Different Query Variations")
    print("=" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 40)
        
        try:
            session_id = str(uuid.uuid4())
            
            response = bedrock_agent_runtime.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=ALIAS_ID,
                sessionId=session_id,
                inputText=query,
                enableTrace=True  # Enable trace to see knowledge base queries
            )
            
            full_response = ""
            kb_queries = []
            kb_results = []
            
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
                        
                        # Check for knowledge base queries
                        if 'orchestrationTrace' in trace_data:
                            orch_trace = trace_data['orchestrationTrace']
                            
                            if 'invocationInput' in orch_trace:
                                inv_input = orch_trace['invocationInput']
                                if 'knowledgeBaseLookupInput' in inv_input:
                                    kb_input = inv_input['knowledgeBaseLookupInput']
                                    kb_queries.append(kb_input.get('text', 'N/A'))
                            
                            if 'observation' in orch_trace:
                                obs = orch_trace['observation']
                                if 'knowledgeBaseLookupOutput' in obs:
                                    kb_output = obs['knowledgeBaseLookupOutput']
                                    references = kb_output.get('retrievedReferences', [])
                                    kb_results.append(len(references))
            
            print(f"Response ({len(full_response)} chars): {full_response[:200]}...")
            
            if kb_queries:
                print(f"KB Queries: {len(kb_queries)}")
                for j, kb_query in enumerate(kb_queries):
                    print(f"  {j+1}. {kb_query}")
                    if j < len(kb_results):
                        print(f"     -> {kb_results[j]} results")
            else:
                print("No knowledge base queries detected")
                
        except Exception as e:
            print(f"Error: {e}")
        
        print()

def check_sample_data():
    """Check what's actually in the S3 data files."""
    
    print("\n" + "=" * 60)
    print("Sample Data from S3")
    print("=" * 60)
    
    s3 = boto3.client('s3', region_name='us-west-2')
    bucket = 'relu-quicksight'
    
    # Check conveyor motor data
    print("\nConveyor Motor Data:")
    try:
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix='knowledge/2025/09/11/',
            MaxKeys=3
        )
        
        for obj in response.get('Contents', []):
            print(f"\nFile: {obj['Key']}")
            
            obj_response = s3.get_object(Bucket=bucket, Key=obj['Key'])
            content = obj_response['Body'].read().decode('utf-8')
            
            print(f"Content preview: {content[:300]}...")
            
    except Exception as e:
        print(f"Error reading conveyor data: {e}")
    
    # Check analytics data
    print("\nAnalytics Data:")
    try:
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix='bedrock-recommendations/analytics/2025/09/11/',
            MaxKeys=2
        )
        
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('.json'):
                print(f"\nFile: {obj['Key']}")
                
                obj_response = s3.get_object(Bucket=bucket, Key=obj['Key'])
                content = obj_response['Body'].read().decode('utf-8')
                
                try:
                    data = json.loads(content)
                    print(f"JSON keys: {list(data.keys())}")
                    
                    # Show relevant fields
                    relevant_fields = ['timestamp', 'equipment_type', 'inference_id', 'predicted_fault', 
                                     'speed_rpm', 'temperature_celsius', 'vibration_mms']
                    
                    for field in relevant_fields:
                        if field in data:
                            print(f"  {field}: {data[field]}")
                            
                except json.JSONDecodeError:
                    print(f"Content preview: {content[:300]}...")
                    
    except Exception as e:
        print(f"Error reading analytics data: {e}")

if __name__ == "__main__":
    test_agent_queries()
    check_sample_data()