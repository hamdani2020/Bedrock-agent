#!/usr/bin/env python3
"""
Check if the Bedrock agent has any action groups configured that might be causing issues.
"""
import boto3
import json

def check_agent_action_groups():
    """Check agent's action group configuration."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    print("Checking Agent Action Groups Configuration")
    print("=" * 50)
    
    try:
        # Get agent details
        agent_response = bedrock_agent.get_agent(agentId=AGENT_ID)
        agent = agent_response['agent']
        
        print(f"Agent: {agent['agentName']}")
        print(f"Status: {agent['agentStatus']}")
        
        # Get agent alias details to find the version
        alias_response = bedrock_agent.get_agent_alias(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID
        )
        alias = alias_response['agentAlias']
        agent_version = alias.get('agentVersion', 'DRAFT')
        
        print(f"Alias: {alias['agentAliasName']}")
        print(f"Agent Version: {agent_version}")
        
        # Check for action groups
        try:
            action_groups_response = bedrock_agent.list_agent_action_groups(
                agentId=AGENT_ID,
                agentVersion=agent_version
            )
            
            action_groups = action_groups_response.get('actionGroupSummaries', [])
            
            if action_groups:
                print(f"\n⚠️  Found {len(action_groups)} action group(s):")
                for ag in action_groups:
                    print(f"  - Name: {ag['actionGroupName']}")
                    print(f"    ID: {ag['actionGroupId']}")
                    print(f"    State: {ag['actionGroupState']}")
                    
                    # Get detailed action group info
                    try:
                        ag_details = bedrock_agent.get_agent_action_group(
                            agentId=AGENT_ID,
                            agentVersion=agent_version,
                            actionGroupId=ag['actionGroupId']
                        )
                        
                        ag_info = ag_details['agentActionGroup']
                        print(f"    Description: {ag_info.get('description', 'N/A')}")
                        
                        # Check if it has function schema
                        if 'functionSchema' in ag_info:
                            print(f"    Has Function Schema: Yes")
                            schema = ag_info['functionSchema']
                            if 'functions' in schema:
                                functions = schema['functions']
                                print(f"    Functions: {len(functions)}")
                                for func in functions:
                                    print(f"      - {func.get('name', 'Unknown')}")
                        
                        # Check if it has API schema
                        if 'apiSchema' in ag_info:
                            print(f"    Has API Schema: Yes")
                        
                        # Check parent action group signature
                        if 'parentActionGroupSignature' in ag_info:
                            print(f"    Parent Signature: {ag_info['parentActionGroupSignature']}")
                            
                    except Exception as e:
                        print(f"    Error getting details: {e}")
                    
                    print()
                    
                print("🔍 This might explain the 'function call format' errors!")
                print("The agent is trying to call functions but they may not be working correctly.")
                
            else:
                print("\n✓ No action groups found - agent should only use knowledge bases")
                
        except Exception as e:
            print(f"\nError checking action groups: {e}")
            
        # Check agent instructions
        print(f"\nAgent Instructions:")
        print("-" * 30)
        instructions = agent.get('instruction', 'No instructions found')
        print(instructions[:500] + "..." if len(instructions) > 500 else instructions)
        
    except Exception as e:
        print(f"Error: {e}")

def test_simple_query():
    """Test a simple query to see the exact error."""
    
    print("\n" + "=" * 50)
    print("Testing Simple Query")
    print("=" * 50)
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    try:
        response = bedrock_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId="test-session-123",
            inputText="What equipment data do you have?"
        )
        
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    full_response += chunk_text
        
        print(f"Response: {full_response}")
        
        # Check for function call errors
        if "function call" in full_response.lower() or "format" in full_response.lower():
            print("\n⚠️  Response contains function call or format errors!")
        
    except Exception as e:
        print(f"Error testing query: {e}")

if __name__ == "__main__":
    check_agent_action_groups()
    test_simple_query()