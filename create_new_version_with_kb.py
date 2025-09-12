#!/usr/bin/env python3
"""
Create a new agent version that includes the KB association
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

def prepare_agent_to_create_new_version():
    """Prepare agent to create a new version with KB association"""
    config = load_config()
    if not config:
        return None
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        
        print(f"🔄 Preparing agent to create new version with KB association...")
        print(f"   Agent ID: {agent_id}")
        
        # Prepare the agent (this will create a new version with current DRAFT state)
        response = bedrock_agent.prepare_agent(agentId=agent_id)
        status = response['agentStatus']
        
        print(f"   Initial status: {status}")
        
        if status == 'PREPARING':
            print("   ⏳ Waiting for agent preparation to complete...")
            
            max_wait = 300  # 5 minutes
            wait_interval = 15
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                
                check_response = bedrock_agent.get_agent(agentId=agent_id)
                current_status = check_response['agent']['agentStatus']
                
                print(f"   Status after {elapsed}s: {current_status}")
                
                if current_status == 'PREPARED':
                    print("   ✅ Agent preparation completed!")
                    break
                elif current_status == 'FAILED':
                    print("   ❌ Agent preparation failed!")
                    return None
        
        # Wait a moment for the new version to be created
        time.sleep(10)
        
        # List versions to find the new one
        print("\n📋 Checking for new agent version...")
        versions_response = bedrock_agent.list_agent_versions(agentId=agent_id)
        versions = versions_response.get('agentVersionSummaries', [])
        
        # Find the highest numbered version (excluding DRAFT)
        latest_version = None
        for version in versions:
            version_num = version['agentVersion']
            status = version['agentStatus']
            
            print(f"   Version {version_num}: {status}")
            
            if status == 'PREPARED' and version_num != 'DRAFT':
                if latest_version is None or int(version_num) > int(latest_version):
                    latest_version = version_num
        
        if latest_version:
            print(f"   ✅ New version created: {latest_version}")
            return latest_version
        else:
            print("   ⚠️  No new version found")
            return None
        
    except ClientError as e:
        print(f"❌ Error preparing agent: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def update_alias_to_new_version(version):
    """Update alias to use the new version"""
    config = load_config()
    if not config or not version:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        print(f"\n🔄 Updating alias to use new version {version}...")
        
        response = bedrock_agent.update_agent_alias(
            agentId=agent_id,
            agentAliasId=alias_id,
            agentAliasName='production',
            description=f'Production alias using version {version} with Knowledge Base integration',
            routingConfiguration=[
                {
                    'agentVersion': version
                }
            ]
        )
        
        alias_status = response['agentAlias']['agentAliasStatus']
        print(f"   ✅ Alias updated to version {version} (Status: {alias_status})")
        
        # Wait for alias to be ready
        if alias_status == 'UPDATING':
            print("   ⏳ Waiting for alias to be prepared...")
            
            max_wait = 120
            wait_interval = 10
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                
                check_response = bedrock_agent.get_agent_alias(
                    agentId=agent_id,
                    agentAliasId=alias_id
                )
                
                current_status = check_response['agentAlias']['agentAliasStatus']
                print(f"   Status after {elapsed}s: {current_status}")
                
                if current_status == 'PREPARED':
                    print("   ✅ Alias is ready!")
                    return True
                elif current_status == 'FAILED':
                    print("   ❌ Alias update failed!")
                    return False
        
        return True
        
    except ClientError as e:
        print(f"❌ Error updating alias: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_agent_with_new_version():
    """Test agent with the new version that includes KB"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        agent_alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        # Test queries that should definitely use the KB
        test_queries = [
            "What is the current condition of the industrial conveyor according to the maintenance data?",
            "What specific fault was detected in the equipment and what is the risk level?",
            "What are the current sensor readings for the conveyor system?"
        ]
        
        print(f"\n🧪 Testing Agent with New Version (KB Integration)")
        print("="*60)
        
        successful_kb_queries = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("-" * 50)
            
            try:
                import uuid
                session_id = str(uuid.uuid4())
                
                response = bedrock_agent_runtime.invoke_agent(
                    agentId=agent_id,
                    agentAliasId=agent_alias_id,
                    sessionId=session_id,
                    inputText=query
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
                    successful_kb_queries += 1
                    print(f"   🎉 SUCCESS: Knowledge Base was used!")
                    print(f"   📚 Sources: {len(set(kb_sources))} unique documents")
                    for source in set(kb_sources)[:2]:
                        print(f"      📄 {source}")
                    
                    print(f"   📝 Response Preview:")
                    print(f"      {full_response[:250]}...")
                else:
                    print(f"   ⚠️  Knowledge Base was not used")
                    print(f"   📝 Response: {full_response[:150]}...")
                
            except ClientError as e:
                print(f"   ❌ Query failed: {e}")
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
        
        print(f"\n" + "="*60)
        print(f"📊 FINAL RESULTS:")
        print(f"   KB Integration Success: {successful_kb_queries}/{len(test_queries)} queries")
        
        if successful_kb_queries == len(test_queries):
            print(f"   🎉 PERFECT: Agent is fully integrated with Knowledge Base!")
            return True
        elif successful_kb_queries > 0:
            print(f"   ✅ PARTIAL: Agent sometimes uses Knowledge Base")
            return True
        else:
            print(f"   ❌ FAILED: Agent is not using Knowledge Base")
            return False
        
    except ClientError as e:
        print(f"❌ Error testing agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Creating New Agent Version with Knowledge Base Integration...\n")
    
    # Create new version with KB association
    new_version = prepare_agent_to_create_new_version()
    
    if new_version:
        # Update alias to use new version
        if update_alias_to_new_version(new_version):
            # Test the integration
            test_agent_with_new_version()
    
    print("\n" + "="*60)
    print("✅ Agent version creation and testing complete!")

if __name__ == "__main__":
    main()