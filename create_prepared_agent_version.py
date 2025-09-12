#!/usr/bin/env python3
"""
Create a properly prepared agent version with knowledge bases.
"""
import boto3
import time
from botocore.exceptions import ClientError

def create_prepared_agent_version():
    """Create a new prepared agent version and update the alias."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    print("Creating Prepared Agent Version")
    print("=" * 40)
    
    try:
        # First, prepare the agent (this ensures all configurations are ready)
        print("1. Preparing agent...")
        prepare_response = bedrock_agent.prepare_agent(agentId=AGENT_ID)
        print(f"Agent preparation status: {prepare_response['agentStatus']}")
        
        # Wait for preparation to complete
        print("2. Waiting for agent preparation to complete...")
        max_wait = 120  # 2 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            agent_response = bedrock_agent.get_agent(agentId=AGENT_ID)
            status = agent_response['agent']['agentStatus']
            print(f"   Status: {status} (waited {wait_time}s)")
            
            if status == 'PREPARED':
                break
            elif status == 'FAILED':
                print("❌ Agent preparation failed")
                return False
            
            time.sleep(10)
            wait_time += 10
        
        if wait_time >= max_wait:
            print("⚠️ Preparation taking longer than expected, continuing...")
        
        # Check available versions
        print("3. Checking available agent versions...")
        versions_response = bedrock_agent.list_agent_versions(agentId=AGENT_ID)
        versions = versions_response.get('agentVersionSummaries', [])
        
        print(f"Available versions: {len(versions)}")
        for version in versions:
            print(f"  Version {version['agentVersion']}: {version['agentStatus']}")
        
        # Use the latest prepared version or DRAFT
        if versions:
            # Find the latest prepared version
            prepared_versions = [v for v in versions if v['agentStatus'] == 'PREPARED']
            if prepared_versions:
                latest_version = max(prepared_versions, key=lambda x: x['agentVersion'])
                target_version = latest_version['agentVersion']
                print(f"Using prepared version: {target_version}")
            else:
                target_version = 'DRAFT'
                print("No prepared versions found, using DRAFT")
        else:
            target_version = 'DRAFT'
            print("No versions found, using DRAFT")
        
        # Update the alias to point to the target version
        print(f"4. Updating alias to point to version {target_version}...")
        
        update_response = bedrock_agent.update_agent_alias(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            agentAliasName="production",
            agentVersion=target_version,
            description="Production alias with knowledge base integration"
        )
        
        print(f"✅ Alias updated successfully")
        
        # Verify the update
        alias_response = bedrock_agent.get_agent_alias(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID
        )
        
        alias = alias_response['agentAlias']
        print(f"Alias now points to version: {alias.get('agentVersion')}")
        print(f"Alias status: {alias['agentAliasStatus']}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_updated_agent():
    """Test the agent with the new version."""
    
    print("\n" + "=" * 40)
    print("Testing Updated Agent")
    print("=" * 40)
    
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    # Test with a specific query that should hit the knowledge base
    test_queries = [
        "Show me data for conveyor_motor_001",
        "What sensor readings do you have for September 11, 2025?",
        "Show me analytics data with fault predictions"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: {query}")
        
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            response = bedrock_agent_runtime.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=ALIAS_ID,
                sessionId=session_id,
                inputText=query,
                enableTrace=True
            )
            
            full_response = ""
            kb_queries = 0
            kb_results = 0
            
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
                        
                        if 'orchestrationTrace' in trace_data:
                            orch_trace = trace_data['orchestrationTrace']
                            
                            if 'invocationInput' in orch_trace:
                                inv_input = orch_trace['invocationInput']
                                if 'knowledgeBaseLookupInput' in inv_input:
                                    kb_queries += 1
                                    kb_input = inv_input['knowledgeBaseLookupInput']
                                    print(f"   KB Query: {kb_input.get('text', 'N/A')}")
                            
                            if 'observation' in orch_trace:
                                obs = orch_trace['observation']
                                if 'knowledgeBaseLookupOutput' in obs:
                                    kb_output = obs['knowledgeBaseLookupOutput']
                                    references = kb_output.get('retrievedReferences', [])
                                    kb_results += len(references)
                                    print(f"   KB Results: {len(references)} references found")
                                    
                                    # Show first reference
                                    if references:
                                        first_ref = references[0]
                                        content = first_ref.get('content', {}).get('text', '')
                                        print(f"   Sample content: {content[:100]}...")
            
            print(f"Response: {full_response[:150]}...")
            print(f"KB Queries: {kb_queries}, Results: {kb_results}")
            
            if kb_queries > 0 and kb_results > 0:
                print("✅ SUCCESS: Agent is using knowledge bases!")
            elif kb_queries > 0:
                print("⚠️ Agent querying KB but no results")
            else:
                print("❌ Agent not using knowledge bases")
                
        except Exception as e:
            print(f"Test error: {e}")

if __name__ == "__main__":
    success = create_prepared_agent_version()
    
    if success:
        print("\nWaiting for changes to propagate...")
        time.sleep(20)
        test_updated_agent()
    else:
        print("Failed to create prepared version")