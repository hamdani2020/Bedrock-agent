#!/usr/bin/env python3
"""
Test Bedrock Agent with Knowledge Base integration
"""

import boto3
import json
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

def associate_kb_with_agent():
    """Associate the knowledge base with the agent"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        kb_id = config['knowledge_base_id']
        
        print(f"🔗 Associating KB {kb_id} with Agent {agent_id}...")
        
        # First, get current agent configuration
        agent_response = bedrock_agent.get_agent(agentId=agent_id)
        agent = agent_response['agent']
        
        print(f"   Agent: {agent['agentName']} (Status: {agent['agentStatus']})")
        
        # Check if KB is already associated
        try:
            kb_response = bedrock_agent.list_agent_knowledge_bases(
                agentId=agent_id,
                agentVersion='DRAFT'
            )
            existing_kbs = kb_response.get('agentKnowledgeBaseSummaries', [])
            
            kb_already_associated = any(kb['knowledgeBaseId'] == kb_id for kb in existing_kbs)
            
            if kb_already_associated:
                print("   ✅ Knowledge Base already associated with agent")
                return True
            
        except ClientError as e:
            print(f"   ⚠️  Could not check existing associations: {e}")
        
        # Associate the knowledge base
        try:
            associate_response = bedrock_agent.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion='DRAFT',
                knowledgeBaseId=kb_id,
                description="Maintenance fault prediction knowledge base",
                knowledgeBaseState='ENABLED'
            )
            
            print("   ✅ Successfully associated Knowledge Base with Agent")
            
            # Prepare and update the agent to apply changes
            print("   🔄 Preparing agent to apply KB association...")
            
            prepare_response = bedrock_agent.prepare_agent(agentId=agent_id)
            print(f"   ✅ Agent prepared (Status: {prepare_response['agentStatus']})")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConflictException':
                print("   ✅ Knowledge Base already associated (conflict)")
                return True
            else:
                print(f"   ❌ Failed to associate KB: {e}")
                return False
        
    except ClientError as e:
        print(f"❌ Error associating KB with agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_agent_with_kb():
    """Test the agent with knowledge base queries"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        agent_alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        # Test queries that should use the knowledge base
        test_queries = [
            "What maintenance issues were detected in the recent analytics data?",
            "Can you analyze the equipment fault predictions from the data?",
            "What are the current sensor readings showing?",
            "Based on the analytics data, what maintenance recommendations do you have?"
        ]
        
        print(f"\n🤖 Testing Agent with Knowledge Base...")
        print(f"   Agent ID: {agent_id}")
        print(f"   Alias ID: {agent_alias_id}")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query}")
            
            try:
                session_id = str(uuid.uuid4())
                
                response = bedrock_agent_runtime.invoke_agent(
                    agentId=agent_id,
                    agentAliasId=agent_alias_id,
                    sessionId=session_id,
                    inputText=query
                )
                
                # Process the streaming response
                full_response = ""
                citations = []
                
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
                                            print(f"   📚 Retrieved {len(retrieved_refs)} references from KB")
                                            for ref in retrieved_refs[:2]:  # Show first 2
                                                location = ref.get('location', {})
                                                if 's3Location' in location:
                                                    s3_uri = location['s3Location'].get('uri', 'unknown')
                                                    print(f"      - {s3_uri}")
                
                print(f"   ✅ Response ({len(full_response)} chars):")
                print(f"   {full_response[:300]}...")
                
                if not full_response.strip():
                    print("   ⚠️  Empty response received")
                
            except ClientError as e:
                print(f"   ❌ Query failed: {e}")
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error testing agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Testing Bedrock Agent with Knowledge Base integration...\n")
    
    # First associate KB with agent
    if associate_kb_with_agent():
        print("\n" + "="*50)
        # Then test the integration
        test_agent_with_kb()
    
    print("\n" + "="*50)
    print("✅ Agent-KB integration test complete!")

if __name__ == "__main__":
    main()