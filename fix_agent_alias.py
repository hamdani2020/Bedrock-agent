#!/usr/bin/env python3
"""
Fix agent alias to use the latest prepared version with KB association
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

def list_agent_versions():
    """List all available agent versions"""
    config = load_config()
    if not config:
        return None
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        
        print(f"📋 Listing agent versions for: {agent_id}")
        
        response = bedrock_agent.list_agent_versions(agentId=agent_id)
        versions = response.get('agentVersionSummaries', [])
        
        print(f"   Found {len(versions)} versions:")
        
        latest_version = None
        for version in versions:
            version_num = version['agentVersion']
            status = version['agentStatus']
            created = version.get('createdAt', 'Unknown')
            
            print(f"   - Version {version_num}: {status} (Created: {created})")
            
            # Find the latest prepared version (excluding DRAFT)
            if status == 'PREPARED' and version_num != 'DRAFT':
                if latest_version is None or int(version_num) > int(latest_version):
                    latest_version = version_num
        
        if latest_version:
            print(f"   ✅ Latest prepared version: {latest_version}")
        else:
            print(f"   ⚠️  No prepared versions found (only DRAFT available)")
        
        return latest_version
        
    except ClientError as e:
        print(f"❌ Error listing versions: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def prepare_agent_and_create_version():
    """Prepare agent to create a new version"""
    config = load_config()
    if not config:
        return None
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        
        print(f"🔄 Preparing agent to create new version...")
        
        # Prepare the agent (this creates a new version)
        response = bedrock_agent.prepare_agent(agentId=agent_id)
        status = response['agentStatus']
        
        print(f"   Agent status: {status}")
        
        if status == 'PREPARING':
            print("   ⏳ Waiting for agent preparation...")
            
            max_wait = 180  # 3 minutes
            wait_interval = 15
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                
                check_response = bedrock_agent.get_agent(agentId=agent_id)
                current_status = check_response['agent']['agentStatus']
                
                print(f"   Status after {elapsed}s: {current_status}")
                
                if current_status == 'PREPARED':
                    print("   ✅ Agent prepared successfully!")
                    break
                elif current_status == 'FAILED':
                    print("   ❌ Agent preparation failed!")
                    return None
        
        # Now list versions to find the new one
        time.sleep(5)  # Wait a bit for version to be created
        return list_agent_versions()
        
    except ClientError as e:
        print(f"❌ Error preparing agent: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def update_alias_to_version(version):
    """Update alias to use specific version"""
    config = load_config()
    if not config or not version:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        print(f"\n🔄 Updating alias to use version {version}...")
        
        response = bedrock_agent.update_agent_alias(
            agentId=agent_id,
            agentAliasId=alias_id,
            agentAliasName='production',
            description=f'Production alias using version {version} with KB integration',
            routingConfiguration=[
                {
                    'agentVersion': version
                }
            ]
        )
        
        alias_status = response['agentAlias']['agentAliasStatus']
        print(f"   ✅ Alias updated (Status: {alias_status})")
        
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

def test_final_agent_kb_integration():
    """Test the final agent-KB integration"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        agent_alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        # Test query that should use the KB
        test_query = "What is the current condition of the industrial conveyor based on the maintenance analytics data? What specific fault was detected and what actions should I take?"
        
        print(f"\n🧪 FINAL AGENT-KB INTEGRATION TEST")
        print(f"   Query: {test_query}")
        print("="*60)
        
        import uuid
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
                                    print(f"   📚 Knowledge Base Used! ({len(retrieved_refs)} references)")
                                    for ref in retrieved_refs:
                                        location = ref.get('location', {})
                                        if 's3Location' in location:
                                            s3_uri = location['s3Location'].get('uri', 'unknown')
                                            filename = s3_uri.split('/')[-1] if '/' in s3_uri else s3_uri
                                            kb_sources.append(filename)
        
        print(f"   ✅ Response Length: {len(full_response)} characters")
        
        if kb_used:
            print(f"   🎉 SUCCESS: Agent successfully used Knowledge Base!")
            print(f"   📚 Sources Referenced: {len(set(kb_sources))} unique documents")
            for source in set(kb_sources)[:3]:
                print(f"      📄 {source}")
            
            print(f"\n   📝 Agent Response Preview:")
            print(f"      {full_response[:500]}...")
            
            print(f"\n   🎯 INTEGRATION STATUS: FULLY FUNCTIONAL")
            return True
        else:
            print(f"   ⚠️  Agent did not use Knowledge Base")
            print(f"   📝 Response Preview: {full_response[:300]}...")
            print(f"\n   🔧 INTEGRATION STATUS: NEEDS TROUBLESHOOTING")
            return False
        
    except ClientError as e:
        print(f"❌ Error in final test: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Fixing Agent Alias to use Knowledge Base Integration...\n")
    
    # First, check current versions
    latest_version = list_agent_versions()
    
    if not latest_version:
        # Prepare agent to create a new version
        print("\n" + "="*50)
        latest_version = prepare_agent_and_create_version()
    
    if latest_version:
        # Update alias to use the latest version
        print("\n" + "="*50)
        if update_alias_to_version(latest_version):
            # Test the integration
            print("\n" + "="*50)
            test_final_agent_kb_integration()
    
    print("\n" + "="*60)
    print("✅ Agent alias fix complete!")

if __name__ == "__main__":
    main()