#!/usr/bin/env python3
"""
Create a new agent version with KB association and update alias
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

def create_agent_version():
    """Create a new agent version with KB association"""
    config = load_config()
    if not config:
        return None
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        
        print(f"📦 Creating new agent version with KB association...")
        print(f"   Agent ID: {agent_id}")
        
        # First, prepare the agent to ensure DRAFT is ready
        print("   🔄 Preparing agent...")
        prepare_response = bedrock_agent.prepare_agent(agentId=agent_id)
        print(f"   Agent status: {prepare_response['agentStatus']}")
        
        # Wait for agent to be prepared
        if prepare_response['agentStatus'] == 'PREPARING':
            print("   ⏳ Waiting for agent to be prepared...")
            
            max_wait = 120
            wait_interval = 10
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                
                check_response = bedrock_agent.get_agent(agentId=agent_id)
                current_status = check_response['agent']['agentStatus']
                print(f"   Status after {elapsed}s: {current_status}")
                
                if current_status == 'PREPARED':
                    break
                elif current_status == 'FAILED':
                    print("   ❌ Agent preparation failed!")
                    return None
        
        # Create new version
        print("   📦 Creating agent version...")
        version_response = bedrock_agent.create_agent_version(
            agentId=agent_id,
            description="Version with Knowledge Base integration for maintenance expert"
        )
        
        new_version = version_response['agentVersion']['version']
        version_status = version_response['agentVersion']['agentStatus']
        
        print(f"   ✅ Created version: {new_version} (Status: {version_status})")
        
        # Wait for version to be created
        if version_status == 'CREATING':
            print("   ⏳ Waiting for version to be ready...")
            
            max_wait = 180  # 3 minutes
            wait_interval = 15
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                
                try:
                    check_response = bedrock_agent.get_agent_version(
                        agentId=agent_id,
                        agentVersion=new_version
                    )
                    
                    current_status = check_response['agentVersion']['agentStatus']
                    print(f"   Status after {elapsed}s: {current_status}")
                    
                    if current_status == 'PREPARED':
                        print(f"   ✅ Version {new_version} is ready!")
                        return new_version
                    elif current_status == 'FAILED':
                        print(f"   ❌ Version creation failed!")
                        return None
                        
                except ClientError as e:
                    print(f"   ⚠️  Still creating... ({e})")
        
        return new_version
        
    except ClientError as e:
        print(f"❌ Error creating agent version: {e}")
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
        
        # Wait for alias to be updated
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

def test_final_integration():
    """Test the final agent-KB integration"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        agent_alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        # Test query that should definitely use the KB
        test_query = "What are the daily inspection procedures mentioned in the maintenance documentation?"
        
        print(f"\n🧪 Final Integration Test...")
        print(f"   Query: {test_query}")
        
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
                                    for ref in retrieved_refs:
                                        location = ref.get('location', {})
                                        if 's3Location' in location:
                                            s3_uri = location['s3Location'].get('uri', 'unknown')
                                            filename = s3_uri.split('/')[-1] if '/' in s3_uri else s3_uri
                                            kb_sources.append(filename)
        
        print(f"   ✅ Response Length: {len(full_response)} characters")
        
        if kb_used:
            print(f"   🎉 SUCCESS: Knowledge Base was used!")
            print(f"   📚 Sources: {len(set(kb_sources))} unique documents")
            for source in set(kb_sources)[:3]:
                print(f"      📄 {source}")
            
            print(f"\n   📝 Response Preview:")
            print(f"      {full_response[:300]}...")
            
            return True
        else:
            print(f"   ⚠️  Knowledge Base was not used")
            print(f"   📝 Response: {full_response[:200]}...")
            return False
        
    except ClientError as e:
        print(f"❌ Error in final test: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Creating Agent Version with Knowledge Base Integration...\n")
    
    # Create new agent version
    new_version = create_agent_version()
    
    if new_version:
        # Update alias to use new version
        if update_alias_to_new_version(new_version):
            # Test the integration
            test_final_integration()
    
    print("\n" + "="*60)
    print("✅ Agent version creation and testing complete!")

if __name__ == "__main__":
    main()