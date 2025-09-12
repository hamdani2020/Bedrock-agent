#!/usr/bin/env python3
"""
Diagnose why the agent isn't accessing knowledge base data properly.
"""
import boto3
import json

def diagnose_agent_kb_issue():
    """Diagnose agent knowledge base access issues."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    print("Diagnosing Agent Knowledge Base Access Issues")
    print("=" * 60)
    
    try:
        # Get agent details
        agent_response = bedrock_agent.get_agent(agentId=AGENT_ID)
        agent = agent_response['agent']
        
        print(f"Agent: {agent['agentName']}")
        print(f"Status: {agent['agentStatus']}")
        print(f"Foundation Model: {agent['foundationModel']}")
        
        # Get agent alias details
        alias_response = bedrock_agent.get_agent_alias(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID
        )
        alias = alias_response['agentAlias']
        
        print(f"\nAlias: {alias['agentAliasName']}")
        print(f"Alias Status: {alias['agentAliasStatus']}")
        print(f"Agent Version: {alias.get('agentVersion', 'DRAFT')}")
        
        agent_version = alias.get('agentVersion', 'DRAFT')
        
        # Check knowledge base associations for this specific version
        print(f"\nChecking Knowledge Base associations for version: {agent_version}")
        print("-" * 40)
        
        kb_response = bedrock_agent.list_agent_knowledge_bases(
            agentId=AGENT_ID,
            agentVersion=agent_version
        )
        
        knowledge_bases = kb_response.get('agentKnowledgeBaseSummaries', [])
        
        if knowledge_bases:
            print(f"✓ Found {len(knowledge_bases)} knowledge base(s) for version {agent_version}:")
            
            for i, kb in enumerate(knowledge_bases, 1):
                print(f"\n{i}. Knowledge Base:")
                print(f"   ID: {kb['knowledgeBaseId']}")
                print(f"   State: {kb['knowledgeBaseState']}")
                print(f"   Description: {kb.get('description', 'N/A')}")
                
                # Get detailed KB info
                try:
                    kb_details = bedrock_agent.get_knowledge_base(
                        knowledgeBaseId=kb['knowledgeBaseId']
                    )
                    kb_info = kb_details['knowledgeBase']
                    print(f"   Name: {kb_info['name']}")
                    print(f"   Status: {kb_info['status']}")
                    
                    # Check if KB is ready
                    if kb_info['status'] != 'ACTIVE':
                        print(f"   ⚠️  KB Status is {kb_info['status']} - should be ACTIVE")
                    
                    if kb['knowledgeBaseState'] != 'ENABLED':
                        print(f"   ⚠️  KB State is {kb['knowledgeBaseState']} - should be ENABLED")
                        
                except Exception as e:
                    print(f"   Error getting KB details: {e}")
        else:
            print(f"❌ No knowledge bases found for agent version {agent_version}!")
            
            # Check if there are KBs associated with DRAFT version
            if agent_version != 'DRAFT':
                print(f"\nChecking DRAFT version for comparison...")
                try:
                    draft_kb_response = bedrock_agent.list_agent_knowledge_bases(
                        agentId=AGENT_ID,
                        agentVersion='DRAFT'
                    )
                    
                    draft_kbs = draft_kb_response.get('agentKnowledgeBaseSummaries', [])
                    if draft_kbs:
                        print(f"✓ Found {len(draft_kbs)} KB(s) in DRAFT version:")
                        for kb in draft_kbs:
                            print(f"   - {kb['knowledgeBaseId']} ({kb['knowledgeBaseState']})")
                        print(f"\n🔧 Issue: Alias points to version {agent_version} but KBs are in DRAFT!")
                    else:
                        print("❌ No KBs found in DRAFT version either")
                        
                except Exception as e:
                    print(f"Error checking DRAFT version: {e}")
        
        # Check agent versions
        print(f"\nChecking available agent versions:")
        print("-" * 40)
        
        try:
            versions_response = bedrock_agent.list_agent_versions(agentId=AGENT_ID)
            versions = versions_response.get('agentVersionSummaries', [])
            
            for version in versions:
                version_num = version['agentVersion']
                status = version['agentStatus']
                print(f"   Version {version_num}: {status}")
                
                # Check if this version has KBs
                try:
                    version_kb_response = bedrock_agent.list_agent_knowledge_bases(
                        agentId=AGENT_ID,
                        agentVersion=version_num
                    )
                    version_kbs = version_kb_response.get('agentKnowledgeBaseSummaries', [])
                    print(f"     Knowledge Bases: {len(version_kbs)}")
                    
                    for kb in version_kbs:
                        print(f"       - {kb['knowledgeBaseId']} ({kb['knowledgeBaseState']})")
                        
                except Exception as e:
                    print(f"     Error checking KBs: {e}")
                    
        except Exception as e:
            print(f"Error listing versions: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_kb_retrieval_directly():
    """Test knowledge base retrieval directly."""
    
    print("\n" + "=" * 60)
    print("Testing Knowledge Base Retrieval Directly")
    print("=" * 60)
    
    bedrock_kb = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    # Test both knowledge bases
    kb_ids = ["ZECQSVPQJZ", "ZRE5Y0KEVD"]
    
    for kb_id in kb_ids:
        print(f"\nTesting KB: {kb_id}")
        print("-" * 30)
        
        try:
            response = bedrock_kb.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={
                    'text': 'conveyor_motor_001 fault data sensor readings'
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5
                    }
                }
            )
            
            results = response.get('retrievalResults', [])
            print(f"Retrieved {len(results)} results")
            
            for i, result in enumerate(results, 1):
                content = result.get('content', {}).get('text', '')
                score = result.get('score', 0)
                location = result.get('location', {})
                
                print(f"\n{i}. Score: {score:.3f}")
                print(f"   Content: {content[:200]}...")
                
                if 's3Location' in location:
                    s3_loc = location['s3Location']
                    print(f"   Source: s3://{s3_loc.get('uri', 'unknown')}")
                    
        except Exception as e:
            print(f"Error testing KB {kb_id}: {e}")

if __name__ == "__main__":
    diagnose_agent_kb_issue()
    test_kb_retrieval_directly()