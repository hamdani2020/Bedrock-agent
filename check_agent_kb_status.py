#!/usr/bin/env python3
"""
Check agent and knowledge base association status
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

def check_agent_status():
    """Check agent preparation status"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        
        print(f"🤖 Checking Agent status: {agent_id}")
        
        response = bedrock_agent.get_agent(agentId=agent_id)
        agent = response['agent']
        
        print(f"   Name: {agent['agentName']}")
        print(f"   Status: {agent['agentStatus']}")
        print(f"   Created: {agent.get('createdAt', 'Unknown')}")
        print(f"   Updated: {agent.get('updatedAt', 'Unknown')}")
        
        # If agent is still preparing, wait
        if agent['agentStatus'] == 'PREPARING':
            print("   ⏳ Agent is still preparing, waiting 30 seconds...")
            time.sleep(30)
            
            response = bedrock_agent.get_agent(agentId=agent_id)
            agent = response['agent']
            print(f"   Updated Status: {agent['agentStatus']}")
        
        return agent['agentStatus'] == 'PREPARED'
        
    except ClientError as e:
        print(f"❌ Error checking agent: {e}")
        return False

def check_kb_association():
    """Check knowledge base association with agent"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        kb_id = config['knowledge_base_id']
        
        print(f"\n🔗 Checking KB association for Agent: {agent_id}")
        
        response = bedrock_agent.list_agent_knowledge_bases(
            agentId=agent_id,
            agentVersion='DRAFT'
        )
        
        kb_associations = response.get('agentKnowledgeBaseSummaries', [])
        
        if not kb_associations:
            print("   ❌ No knowledge bases associated with agent")
            return False
        
        print(f"   ✅ Found {len(kb_associations)} associated KB(s)")
        
        for kb in kb_associations:
            kb_assoc_id = kb['knowledgeBaseId']
            kb_state = kb['knowledgeBaseState']
            
            print(f"   📚 KB ID: {kb_assoc_id}")
            print(f"      State: {kb_state}")
            print(f"      Description: {kb.get('description', 'No description')}")
            print(f"      Created: {kb.get('createdAt', 'Unknown')}")
            print(f"      Updated: {kb.get('updatedAt', 'Unknown')}")
            
            if kb_assoc_id == kb_id:
                print(f"   ✅ Target KB {kb_id} is properly associated")
                return kb_state == 'ENABLED'
        
        print(f"   ⚠️  Target KB {kb_id} not found in associations")
        return False
        
    except ClientError as e:
        print(f"❌ Error checking KB association: {e}")
        return False

def check_agent_alias():
    """Check agent alias status"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        print(f"\n🏷️  Checking Agent Alias: {alias_id}")
        
        response = bedrock_agent.get_agent_alias(
            agentId=agent_id,
            agentAliasId=alias_id
        )
        
        alias = response['agentAlias']
        
        print(f"   Name: {alias['agentAliasName']}")
        print(f"   Status: {alias['agentAliasStatus']}")
        print(f"   Created: {alias.get('createdAt', 'Unknown')}")
        print(f"   Updated: {alias.get('updatedAt', 'Unknown')}")
        
        # Check routing configuration
        routing_config = alias.get('routingConfiguration', [])
        if routing_config:
            for route in routing_config:
                agent_version = route.get('agentVersion', 'Unknown')
                print(f"   Routes to Agent Version: {agent_version}")
        
        return alias['agentAliasStatus'] == 'PREPARED'
        
    except ClientError as e:
        print(f"❌ Error checking agent alias: {e}")
        return False

def update_agent_alias():
    """Update agent alias to use latest version"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        agent_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ID']
        alias_id = config['lambda_functions']['query_handler']['environment_variables']['BEDROCK_AGENT_ALIAS_ID']
        
        print(f"\n🔄 Updating Agent Alias to use DRAFT version...")
        
        response = bedrock_agent.update_agent_alias(
            agentId=agent_id,
            agentAliasId=alias_id,
            agentAliasName='production',
            description='Production alias for maintenance expert agent',
            routingConfiguration=[
                {
                    'agentVersion': 'DRAFT'
                }
            ]
        )
        
        print(f"   ✅ Alias updated (Status: {response['agentAlias']['agentAliasStatus']})")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error updating agent alias: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Checking Agent and Knowledge Base integration status...\n")
    
    agent_ready = check_agent_status()
    kb_associated = check_kb_association()
    alias_ready = check_agent_alias()
    
    if agent_ready and kb_associated and not alias_ready:
        print("\n🔄 Agent and KB are ready, updating alias...")
        update_agent_alias()
    
    print("\n" + "="*50)
    print("✅ Status check complete!")
    
    if agent_ready and kb_associated:
        print("🎉 Agent and Knowledge Base are properly integrated!")
    else:
        print("⚠️  Some components may need attention")

if __name__ == "__main__":
    main()