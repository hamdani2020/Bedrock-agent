#!/usr/bin/env python3
"""
Check if the Bedrock agent is properly connected to the knowledge base
and if the knowledge base contains the expected device data.
"""
import boto3
import json
from botocore.exceptions import ClientError

def check_agent_kb_connection():
    """Check agent's knowledge base configuration."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    bedrock_kb = boto3.client('bedrock-agent', region_name='us-west-2')
    
    AGENT_ID = "GMJGK6RO4S"
    ALIAS_ID = "RUWFC5DRPQ"
    
    print("Checking Agent Knowledge Base Configuration")
    print("=" * 50)
    
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
        print(f"Status: {alias['agentAliasStatus']}")
        
        # Check if agent has knowledge bases associated
        try:
            # List agent knowledge bases
            kb_response = bedrock_agent.list_agent_knowledge_bases(
                agentId=AGENT_ID,
                agentVersion=alias.get('agentVersion', 'DRAFT')
            )
            
            knowledge_bases = kb_response.get('agentKnowledgeBaseSummaries', [])
            
            if knowledge_bases:
                print(f"\n✓ Agent has {len(knowledge_bases)} knowledge base(s) associated:")
                for kb in knowledge_bases:
                    print(f"  - KB ID: {kb['knowledgeBaseId']}")
                    print(f"    Status: {kb['knowledgeBaseState']}")
                    print(f"    Description: {kb.get('description', 'N/A')}")
                    
                    # Check knowledge base details
                    try:
                        kb_details = bedrock_kb.get_knowledge_base(
                            knowledgeBaseId=kb['knowledgeBaseId']
                        )
                        kb_info = kb_details['knowledgeBase']
                        print(f"    Name: {kb_info['name']}")
                        print(f"    Status: {kb_info['status']}")
                        
                        # Check data sources
                        ds_response = bedrock_kb.list_data_sources(
                            knowledgeBaseId=kb['knowledgeBaseId']
                        )
                        
                        data_sources = ds_response.get('dataSourceSummaries', [])
                        print(f"    Data Sources: {len(data_sources)}")
                        
                        for ds in data_sources:
                            print(f"      - {ds['name']} (Status: {ds['status']})")
                            
                            # Get data source details
                            ds_details = bedrock_kb.get_data_source(
                                knowledgeBaseId=kb['knowledgeBaseId'],
                                dataSourceId=ds['dataSourceId']
                            )
                            
                            ds_config = ds_details['dataSource']['dataSourceConfiguration']
                            if 's3Configuration' in ds_config:
                                s3_config = ds_config['s3Configuration']
                                print(f"        S3 Bucket: {s3_config['bucketArn']}")
                                if 'inclusionPrefixes' in s3_config:
                                    print(f"        Prefixes: {s3_config['inclusionPrefixes']}")
                        
                    except Exception as e:
                        print(f"    Error getting KB details: {e}")
            else:
                print("\n✗ No knowledge bases associated with this agent!")
                print("This explains why you're getting generic responses.")
                
        except Exception as e:
            print(f"\nError checking knowledge bases: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

def check_knowledge_base_data():
    """Check if knowledge bases contain the expected data."""
    
    print("\n" + "=" * 50)
    print("Checking Knowledge Base Data")
    print("=" * 50)
    
    # Check both knowledge bases from config
    kb_ids = ["ZRE5Y0KEVD", "ZECQSVPQJZ"]  # From your config
    
    bedrock_kb = boto3.client('bedrock-agent', region_name='us-west-2')
    s3 = boto3.client('s3', region_name='us-west-2')
    
    for kb_id in kb_ids:
        try:
            print(f"\nChecking Knowledge Base: {kb_id}")
            
            kb_response = bedrock_kb.get_knowledge_base(knowledgeBaseId=kb_id)
            kb = kb_response['knowledgeBase']
            
            print(f"Name: {kb['name']}")
            print(f"Status: {kb['status']}")
            
            # Check data sources
            ds_response = bedrock_kb.list_data_sources(knowledgeBaseId=kb_id)
            data_sources = ds_response.get('dataSourceSummaries', [])
            
            for ds in data_sources:
                print(f"\nData Source: {ds['name']}")
                print(f"Status: {ds['status']}")
                
                # Get S3 configuration
                ds_details = bedrock_kb.get_data_source(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds['dataSourceId']
                )
                
                ds_config = ds_details['dataSource']['dataSourceConfiguration']
                if 's3Configuration' in ds_config:
                    s3_config = ds_config['s3Configuration']
                    bucket_arn = s3_config['bucketArn']
                    bucket_name = bucket_arn.split(':')[-1]
                    
                    print(f"S3 Bucket: {bucket_name}")
                    
                    # Check if bucket has data
                    try:
                        prefixes = s3_config.get('inclusionPrefixes', [''])
                        for prefix in prefixes:
                            print(f"Checking prefix: {prefix}")
                            
                            response = s3.list_objects_v2(
                                Bucket=bucket_name,
                                Prefix=prefix,
                                MaxKeys=10
                            )
                            
                            objects = response.get('Contents', [])
                            print(f"  Found {len(objects)} objects")
                            
                            for obj in objects[:3]:  # Show first 3
                                print(f"    - {obj['Key']} ({obj['Size']} bytes)")
                                
                                # Try to read a sample file
                                if obj['Key'].endswith('.json'):
                                    try:
                                        obj_response = s3.get_object(
                                            Bucket=bucket_name,
                                            Key=obj['Key']
                                        )
                                        content = obj_response['Body'].read().decode('utf-8')
                                        data = json.loads(content)
                                        
                                        print(f"      Sample data keys: {list(data.keys())}")
                                        
                                        # Look for device/conveyor data
                                        if 'device_id' in data or 'conveyor' in str(data).lower():
                                            print(f"      ✓ Contains device/conveyor data")
                                        else:
                                            print(f"      ? Data type unclear")
                                            
                                    except Exception as e:
                                        print(f"      Error reading file: {e}")
                                        
                    except Exception as e:
                        print(f"  Error checking S3 data: {e}")
                        
        except Exception as e:
            print(f"Error checking KB {kb_id}: {e}")

if __name__ == "__main__":
    check_agent_kb_connection()
    check_knowledge_base_data()