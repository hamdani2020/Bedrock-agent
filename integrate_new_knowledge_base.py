#!/usr/bin/env python3
"""
Integrate the new Knowledge Base with the Bedrock Agent.
KB ID: ZECQSVPQJZ
KB Name: knowledge-base-conveyor-inference
"""

import boto3
import json

def integrate_new_knowledge_base():
    """Integrate the new Knowledge Base with the existing agent."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    agent_id = "GMJGK6RO4S"
    new_kb_id = "ZECQSVPQJZ"
    
    try:
        # Get current agent configuration
        agent_response = bedrock_agent.get_agent(agentId=agent_id)
        agent = agent_response['agent']
        
        print(f"Current agent: {agent['agentName']}")
        
        # Check if agent already has knowledge bases associated
        try:
            kb_response = bedrock_agent.list_agent_knowledge_bases(
                agentId=agent_id,
                agentVersion="DRAFT"
            )
            current_kbs = kb_response['agentKnowledgeBaseSummaries']
            
            print(f"Current Knowledge Bases: {len(current_kbs)}")
            for kb in current_kbs:
                print(f"  - {kb['knowledgeBaseId']}: {kb.get('description', 'No description')}")
            
            # Check if new KB is already associated
            kb_ids = [kb['knowledgeBaseId'] for kb in current_kbs]
            if new_kb_id in kb_ids:
                print(f"✅ Knowledge Base {new_kb_id} is already associated with the agent")
                return True
            
        except Exception as e:
            print(f"No existing knowledge bases or error: {e}")
            current_kbs = []
        
        # Associate new knowledge base with agent
        print(f"🔗 Associating Knowledge Base {new_kb_id} with agent...")
        
        bedrock_agent.associate_agent_knowledge_base(
            agentId=agent_id,
            agentVersion="DRAFT",
            knowledgeBaseId=new_kb_id,
            description="Conveyor inference and maintenance knowledge base",
            knowledgeBaseState="ENABLED"
        )
        
        print("✅ Knowledge Base associated successfully!")
        
        # Prepare agent (create new version)
        print("🔄 Preparing agent with new knowledge base...")
        
        prepare_response = bedrock_agent.prepare_agent(agentId=agent_id)
        
        print("✅ Agent prepared successfully!")
        print(f"Agent status: {prepare_response['agentStatus']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error integrating knowledge base: {str(e)}")
        return False

if __name__ == "__main__":
    integrate_new_knowledge_base()
