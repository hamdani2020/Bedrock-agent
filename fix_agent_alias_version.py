#!/usr/bin/env python3
"""
Fix the agent alias to point to the correct version with knowledge bases.
"""
import boto3
import json
import time

def fix_agent_alias():
    """Fix the agent alias to point to DRAFT version with knowledge bases."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    print("Fixing Agent Alias Configuration")
    print("=" * 50)
    
    try:
        # Get current alias configuration
        alias_response = bedrock_agent.get_agent_alias(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID
        )
        alias = alias_response['agentAlias']
        
        print(f"Current Alias Configuration:")
        print(f"  Name: {alias['agentAliasName']}")
        print(f"  Status: {alias['agentAliasStatus']}")
        print(f"  Current Version: {alias.get('agentVersion', 'DRAFT')}")
        
        current_version = alias.get('agentVersion', 'DRAFT')
        
        if current_version == 'DRAFT':
            print("\n✓ Alias is already pointing to DRAFT version")
            print("  This should have access to knowledge bases")
        else:
            print(f"\n⚠️  Alias is pointing to version {current_version}")
            print("  Need to update to DRAFT version which has knowledge bases")
            
            # Update alias to point to DRAFT
            print("\n🔄 Updating alias to point to DRAFT version...")
            
            update_response = bedrock_agent.update_agent_alias(
                agentId=AGENT_ID,
                agentAliasId=ALIAS_ID,
                agentAliasName=alias['agentAliasName'],
                description=alias.get('description', 'Production alias for maintenance expert agent'),
                agentVersion='DRAFT'
            )
            
            print("✅ Alias updated successfully!")
            
            # Wait for update to complete
            print("⏳ Waiting for alias update to complete...")
            time.sleep(10)
        
        # Verify the fix
        print("\n🔍 Verifying alias configuration...")
        
        updated_alias_response = bedrock_agent.get_agent_alias(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID
        )
        updated_alias = updated_alias_response['agentAlias']
        
        print(f"Updated Alias Configuration:")
        print(f"  Name: {updated_alias['agentAliasName']}")
        print(f"  Status: {updated_alias['agentAliasStatus']}")
        print(f"  Version: {updated_alias.get('agentVersion', 'DRAFT')}")
        
        # Check knowledge bases for the version
        version = updated_alias.get('agentVersion', 'DRAFT')
        kb_response = bedrock_agent.list_agent_knowledge_bases(
            agentId=AGENT_ID,
            agentVersion=version
        )
        
        knowledge_bases = kb_response.get('agentKnowledgeBaseSummaries', [])
        print(f"  Knowledge Bases: {len(knowledge_bases)}")
        
        for kb in knowledge_bases:
            print(f"    - {kb['knowledgeBaseId']} ({kb['knowledgeBaseState']})")
        
        if len(knowledge_bases) > 0:
            print("\n✅ Alias now has access to knowledge bases!")
            return True
        else:
            print("\n❌ Alias still doesn't have knowledge bases")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_fixed_agent():
    """Test the agent after fixing the alias."""
    
    print("\n" + "=" * 50)
    print("Testing Fixed Agent")
    print("=" * 50)
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    # Test with a specific query that should hit the knowledge base
    test_query = "What faults have been detected in conveyor_motor_001?"
    
    print(f"Test Query: {test_query}")
    
    try:
        response = bedrock_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId="test-fix-session",
            inputText=test_query
        )
        
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    full_response += chunk_text
        
        print(f"\nResponse ({len(full_response)} chars):")
        print(full_response)
        
        # Check if response contains specific data
        specific_indicators = [
            "conveyor_motor_001", "ball bearing fault", "belt slippage",
            "September 11", "RPM", "temperature", "vibration", "2025-09-11"
        ]
        
        has_specific = any(indicator.lower() in full_response.lower() for indicator in specific_indicators)
        
        if has_specific:
            print("\n✅ SUCCESS! Agent is now accessing knowledge base data!")
        else:
            print("\n⚠️  Still getting generic responses")
            
        return has_specific
        
    except Exception as e:
        print(f"Error testing agent: {e}")
        return False

def test_lambda_after_fix():
    """Test the Lambda function after fixing the agent."""
    
    print("\n" + "=" * 50)
    print("Testing Lambda Function After Fix")
    print("=" * 50)
    
    import requests
    import uuid
    
    lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    test_query = "What faults have been detected in conveyor_motor_001?"
    
    try:
        payload = {
            "query": test_query,
            "sessionId": str(uuid.uuid4())
        }
        
        response = requests.post(
            lambda_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            
            print(f"Lambda Response ({len(response_text)} chars):")
            print(response_text[:300] + "..." if len(response_text) > 300 else response_text)
            
            # Check for specific data
            specific_indicators = [
                "conveyor_motor_001", "ball bearing fault", "belt slippage",
                "September 11", "RPM", "temperature", "vibration"
            ]
            
            has_specific = any(indicator.lower() in response_text.lower() for indicator in specific_indicators)
            
            if has_specific:
                print("\n✅ SUCCESS! Lambda is now returning knowledge base data!")
            else:
                print("\n⚠️  Lambda still returning generic responses")
                
            return has_specific
        else:
            print(f"Lambda error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error testing Lambda: {e}")
        return False

if __name__ == "__main__":
    # Fix the alias
    if fix_agent_alias():
        # Test the agent directly
        agent_works = test_fixed_agent()
        
        if agent_works:
            # Test Lambda function
            lambda_works = test_lambda_after_fix()
            
            if lambda_works:
                print("\n🎉 COMPLETE SUCCESS!")
                print("Both agent and Lambda are now working correctly!")
                print("\nNext step: Update Streamlit app to test the fix")
            else:
                print("\n⚠️  Agent works but Lambda still has issues")
                print("May need to wait a few minutes for changes to propagate")
        else:
            print("\n❌ Agent still not working correctly")
            print("May need additional troubleshooting")
    else:
        print("\n❌ Failed to fix alias configuration")