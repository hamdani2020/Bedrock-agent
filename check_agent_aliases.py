#!/usr/bin/env python3
"""
Check which agent alias has Knowledge Base access.
"""
import boto3

def check_aliases():
    """Check agent aliases and their Knowledge Base connections."""
    try:
        bedrock_agent = boto3.client('bedrock-agent')
        
        agent_id = 'GMJGK6RO4S'
        
        # List aliases
        response = bedrock_agent.list_agent_aliases(agentId=agent_id)
        
        print("🔍 Agent Aliases:")
        for alias in response['agentAliasSummaries']:
            alias_id = alias['agentAliasId']
            alias_name = alias['agentAliasName']
            
            print(f"\nAlias: {alias_name} (ID: {alias_id})")
            
            # Get alias details
            try:
                alias_details = bedrock_agent.get_agent_alias(
                    agentId=agent_id,
                    agentAliasId=alias_id
                )
                
                # Check for Knowledge Base associations
                routing_config = alias_details['agentAlias'].get('routingConfiguration', [])
                
                if routing_config:
                    for config in routing_config:
                        agent_version = config.get('agentVersion', 'Unknown')
                        print(f"  Agent Version: {agent_version}")
                        
                        # Get agent version details to check KB
                        if agent_version != 'DRAFT':
                            try:
                                version_details = bedrock_agent.get_agent_version(
                                    agentId=agent_id,
                                    agentVersion=agent_version
                                )
                                
                                kb_configs = version_details['agentVersion'].get('knowledgeBaseConfigurations', [])
                                if kb_configs:
                                    print(f"  ✅ Has Knowledge Base: {len(kb_configs)} KB(s)")
                                    for kb in kb_configs:
                                        print(f"    KB ID: {kb.get('knowledgeBaseId', 'Unknown')}")
                                else:
                                    print(f"  ❌ No Knowledge Base")
                            except:
                                print(f"  ⚠️ Cannot check version {agent_version}")
                else:
                    print(f"  ❌ No routing configuration")
                    
            except Exception as e:
                print(f"  ❌ Error getting alias details: {str(e)}")
        
        print(f"\n💡 Try using alias with Knowledge Base in your Lambda function")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_aliases()