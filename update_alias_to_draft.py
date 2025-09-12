#!/usr/bin/env python3
"""
Update agent alias to use DRAFT version with KB association
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

def update_alias_to_draft():
    """Update agent alias to use DRAFT version"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        print(f"🔄 Updating Agent Alias to use DRAFT version...")
        print(f"   Agent ID: {agent_id}")
        print(f"   Alias ID: {alias_id}")
        
        response = bedrock_agent.update_agent_alias(
            agentId=agent_id,
            agentAliasId=alias_id,
            agentAliasName='production',
            description='Production alias for maintenance expert agent with KB access',
            routingConfiguration=[
                {
                    'agentVersion': 'DRAFT'
                }
            ]
        )
        
        alias_status = response['agentAlias']['agentAliasStatus']
        print(f"   ✅ Alias updated (Status: {alias_status})")
        
        # Wait for alias to be prepared
        if alias_status == 'UPDATING':
            print("   ⏳ Waiting for alias to be prepared...")
            
            max_wait = 120  # 2 minutes
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
                    print("   ✅ Alias is now prepared!")
                    return True
                elif current_status == 'FAILED':
                    print("   ❌ Alias update failed!")
                    return False
            
            print("   ⚠️  Alias taking longer than expected to prepare")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error updating alias: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_agent_with_kb_after_update():
    """Test agent after alias update"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        agent_alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        # Test a specific query that should use the KB
        test_query = "What are the daily inspection procedures for industrial equipment?"
        
        print(f"\n🧪 Testing Agent with updated alias...")
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
                                    for ref in retrieved_refs[:2]:
                                        location = ref.get('location', {})
                                        if 's3Location' in location:
                                            s3_uri = location['s3Location'].get('uri', 'unknown')
                                            filename = s3_uri.split('/')[-1] if '/' in s3_uri else s3_uri
                                            print(f"      📄 {filename}")
        
        if full_response.strip():
            print(f"   ✅ Response received ({len(full_response)} chars)")
            print(f"   📝 Preview: {full_response[:200]}...")
            
            if kb_used:
                print("   🎉 SUCCESS: Agent is now using the Knowledge Base!")
                return True
            else:
                print("   ⚠️  Agent responded but didn't use KB")
                return False
        else:
            print("   ❌ No response received")
            return False
        
    except ClientError as e:
        print(f"❌ Error testing agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Updating Agent Alias to use DRAFT version with KB access...\n")
    
    if update_alias_to_draft():
        print("\n" + "="*50)
        test_agent_with_kb_after_update()
    
    print("\n" + "="*50)
    print("✅ Alias update complete!")

if __name__ == "__main__":
    main()