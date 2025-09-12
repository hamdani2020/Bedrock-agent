#!/usr/bin/env python3
"""
Fix the agent alias to ensure it's properly connected to knowledge bases.
"""
import boto3
import json
from botocore.exceptions import ClientError

def fix_agent_alias_kb_connection():
    """Fix the agent alias knowledge base connection."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    print("Fixing Agent Alias Knowledge Base Connection")
    print("=" * 50)
    
    try:
        # First, get the current alias configuration
        print("1. Getting current alias configuration...")
        alias_response = bedrock_agent.get_agent_alias(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID
        )
        
        alias = alias_response['agentAlias']
        print(f"Current alias: {alias['agentAliasName']}")
        print(f"Status: {alias['agentAliasStatus']}")
        print(f"Agent Version: {alias.get('agentVersion', 'DRAFT')}")
        
        # Check what knowledge bases are available
        print("\n2. Checking available knowledge bases...")
        
        # Get the agent version that the alias points to
        agent_version = alias.get('agentVersion', 'DRAFT')
        
        try:
            kb_response = bedrock_agent.list_agent_knowledge_bases(
                agentId=AGENT_ID,
                agentVersion=agent_version
            )
            
            current_kbs = kb_response.get('agentKnowledgeBaseSummaries', [])
            print(f"Knowledge bases associated with version {agent_version}: {len(current_kbs)}")
            
            for kb in current_kbs:
                print(f"  - {kb['knowledgeBaseId']}: {kb['knowledgeBaseState']}")
                
        except Exception as e:
            print(f"Error getting knowledge bases for version {agent_version}: {e}")
            
            # Try with DRAFT version
            if agent_version != 'DRAFT':
                print("Trying with DRAFT version...")
                try:
                    kb_response = bedrock_agent.list_agent_knowledge_bases(
                        agentId=AGENT_ID,
                        agentVersion='DRAFT'
                    )
                    
                    draft_kbs = kb_response.get('agentKnowledgeBaseSummaries', [])
                    print(f"Knowledge bases in DRAFT: {len(draft_kbs)}")
                    
                    if draft_kbs:
                        print("Found knowledge bases in DRAFT version. Need to create new agent version.")
                        return create_new_agent_version_and_alias(AGENT_ID, ALIAS_ID, draft_kbs)
                        
                except Exception as e2:
                    print(f"Error getting DRAFT knowledge bases: {e2}")
        
        # If we have knowledge bases but they're not working, check their status
        if current_kbs:
            print("\n3. Checking knowledge base status...")
            for kb in current_kbs:
                kb_id = kb['knowledgeBaseId']
                try:
                    kb_details = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
                    kb_info = kb_details['knowledgeBase']
                    print(f"  KB {kb_id}: {kb_info['status']}")
                    
                    # Check data sources
                    ds_response = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
                    data_sources = ds_response.get('dataSourceSummaries', [])
                    
                    for ds in data_sources:
                        print(f"    Data Source {ds['name']}: {ds['status']}")
                        
                        # If data source is not available, try to sync it
                        if ds['status'] != 'AVAILABLE':
                            print(f"    Syncing data source {ds['dataSourceId']}...")
                            try:
                                sync_response = bedrock_agent.start_ingestion_job(
                                    knowledgeBaseId=kb_id,
                                    dataSourceId=ds['dataSourceId']
                                )
                                print(f"    Sync started: {sync_response['ingestionJob']['status']}")
                            except Exception as sync_error:
                                print(f"    Sync failed: {sync_error}")
                                
                except Exception as kb_error:
                    print(f"  Error checking KB {kb_id}: {kb_error}")
        else:
            print("No knowledge bases found. Need to associate knowledge bases with the agent.")
            return associate_knowledge_bases_with_agent(AGENT_ID, ALIAS_ID)
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def create_new_agent_version_and_alias(agent_id, alias_id, knowledge_bases):
    """Create a new agent version with knowledge bases and update alias."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    print("\n4. Creating new agent version with knowledge bases...")
    
    try:
        # Create a new version of the agent
        version_response = bedrock_agent.create_agent_version(
            agentId=agent_id,
            description="Version with knowledge base integration for maintenance data"
        )
        
        new_version = version_response['agentVersion']['version']
        print(f"Created agent version: {new_version}")
        
        # Wait for version to be ready
        print("Waiting for version to be ready...")
        import time
        time.sleep(10)
        
        # Update the alias to point to the new version
        print(f"Updating alias {alias_id} to point to version {new_version}...")
        
        update_response = bedrock_agent.update_agent_alias(
            agentId=agent_id,
            agentAliasId=alias_id,
            agentAliasName="production",
            agentVersion=new_version,
            description="Production alias with knowledge base integration"
        )
        
        print(f"Alias updated successfully")
        print(f"New configuration: Version {new_version}")
        
        return True
        
    except Exception as e:
        print(f"Error creating version and updating alias: {e}")
        return False

def associate_knowledge_bases_with_agent(agent_id, alias_id):
    """Associate knowledge bases with the agent."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    # Knowledge base IDs from your config
    kb_ids = ["ZRE5Y0KEVD", "ZECQSVPQJZ"]
    
    print(f"\n4. Associating knowledge bases with agent...")
    
    try:
        for kb_id in kb_ids:
            print(f"Associating KB {kb_id}...")
            
            try:
                associate_response = bedrock_agent.associate_agent_knowledge_base(
                    agentId=agent_id,
                    agentVersion='DRAFT',
                    knowledgeBaseId=kb_id,
                    description=f"Knowledge base {kb_id} for maintenance data",
                    knowledgeBaseState='ENABLED'
                )
                
                print(f"  Successfully associated KB {kb_id}")
                
            except Exception as e:
                if "already associated" in str(e).lower():
                    print(f"  KB {kb_id} already associated")
                else:
                    print(f"  Error associating KB {kb_id}: {e}")
        
        # Now create a new version and update alias
        print("\nCreating new agent version...")
        return create_new_agent_version_and_alias(agent_id, alias_id, [])
        
    except Exception as e:
        print(f"Error associating knowledge bases: {e}")
        return False

def test_agent_after_fix():
    """Test the agent after fixing the configuration."""
    
    print("\n" + "=" * 50)
    print("Testing Agent After Fix")
    print("=" * 50)
    
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    test_query = "Show me data for conveyor_motor_001 from September 11, 2025"
    
    try:
        import uuid
        session_id = str(uuid.uuid4())
        
        print(f"Testing query: {test_query}")
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId=session_id,
            inputText=test_query,
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
                        
                        if 'observation' in orch_trace:
                            obs = orch_trace['observation']
                            if 'knowledgeBaseLookupOutput' in obs:
                                kb_output = obs['knowledgeBaseLookupOutput']
                                references = kb_output.get('retrievedReferences', [])
                                kb_results += len(references)
        
        print(f"Response: {full_response[:200]}...")
        print(f"Knowledge Base Queries: {kb_queries}")
        print(f"Knowledge Base Results: {kb_results}")
        
        if kb_queries > 0 and kb_results > 0:
            print("✅ Agent is now successfully using knowledge bases!")
        elif kb_queries > 0:
            print("⚠️ Agent is querying knowledge bases but getting no results")
        else:
            print("❌ Agent is still not using knowledge bases")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    success = fix_agent_alias_kb_connection()
    if success:
        # Wait a bit for changes to propagate
        print("\nWaiting for changes to propagate...")
        import time
        time.sleep(15)
        
        test_agent_after_fix()
    else:
        print("Fix failed. Please check the error messages above.")