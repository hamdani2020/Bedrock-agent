#!/usr/bin/env python3
"""
Test the new Knowledge Base: knowledge-base-conveyor-inference
Discover its ID and integrate it with the Bedrock Agent system.
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from botocore.exceptions import ClientError

class NewKnowledgeBaseTester:
    """Test and integrate the new Knowledge Base."""
    
    def __init__(self):
        """Initialize the tester."""
        self.region = "us-west-2"
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        # Current agent configuration
        self.agent_id = "GMJGK6RO4S"
        self.agent_alias_id = "RUWFC5DRPQ"
        
        # New KB details
        self.new_kb_name = "knowledge-base-conveyor-inference"
        self.new_kb_id = None
        
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
    
    def discover_new_knowledge_base(self) -> Optional[str]:
        """Discover the new Knowledge Base and get its ID."""
        print("\n🔍 Discovering New Knowledge Base...")
        
        try:
            # List all knowledge bases
            response = self.bedrock_agent.list_knowledge_bases()
            knowledge_bases = response['knowledgeBaseSummaries']
            
            print(f"    Found {len(knowledge_bases)} Knowledge Bases:")
            
            for kb in knowledge_bases:
                kb_name = kb['name']
                kb_id = kb['knowledgeBaseId']
                kb_status = kb['status']
                
                print(f"      - {kb_name} ({kb_id}): {kb_status}")
                
                if kb_name == self.new_kb_name:
                    self.new_kb_id = kb_id
                    print(f"    ✅ Found new KB: {kb_name} -> {kb_id}")
            
            if self.new_kb_id:
                self.log_test("Knowledge Base Discovery", True, f"Found: {self.new_kb_id}")
                return self.new_kb_id
            else:
                self.log_test("Knowledge Base Discovery", False, f"KB '{self.new_kb_name}' not found")
                return None
                
        except Exception as e:
            self.log_test("Knowledge Base Discovery", False, str(e))
            return None
    
    def test_new_knowledge_base_status(self) -> bool:
        """Test the status of the new Knowledge Base."""
        print(f"\n📚 Testing New Knowledge Base Status...")
        
        if not self.new_kb_id:
            self.log_test("New KB Status", False, "KB ID not available")
            return False
        
        try:
            # Get knowledge base details
            kb_response = self.bedrock_agent.get_knowledge_base(knowledgeBaseId=self.new_kb_id)
            kb = kb_response['knowledgeBase']
            
            kb_name = kb['name']
            kb_status = kb['status']
            description = kb.get('description', 'No description')
            
            print(f"    Name: {kb_name}")
            print(f"    Status: {kb_status}")
            print(f"    Description: {description}")
            
            # Get data sources
            data_sources_response = self.bedrock_agent.list_data_sources(knowledgeBaseId=self.new_kb_id)
            data_sources = data_sources_response['dataSourceSummaries']
            
            print(f"    Data Sources: {len(data_sources)}")
            
            all_sources_ready = True
            source_details = []
            
            for ds in data_sources:
                try:
                    ds_detail = self.bedrock_agent.get_data_source(
                        knowledgeBaseId=self.new_kb_id,
                        dataSourceId=ds['dataSourceId']
                    )
                    ds_status = ds_detail['dataSource']['status']
                    ds_name = ds_detail['dataSource']['name']
                    
                    print(f"      - {ds_name}: {ds_status}")
                    source_details.append(f"{ds_name}: {ds_status}")
                    
                    if ds_status not in ['AVAILABLE']:
                        all_sources_ready = False
                except Exception as e:
                    print(f"      - {ds['dataSourceId']}: Error getting details - {str(e)}")
                    all_sources_ready = False
            
            success = kb_status == 'ACTIVE' and all_sources_ready
            details = f"Status: {kb_status}, Sources: {len(data_sources)}, Ready: {all_sources_ready}"
            
            self.log_test("New KB Status", success, details)
            return success
            
        except Exception as e:
            self.log_test("New KB Status", False, str(e))
            return False
    
    def test_knowledge_base_query(self) -> bool:
        """Test querying the new Knowledge Base directly."""
        print(f"\n🔍 Testing Knowledge Base Query...")
        
        if not self.new_kb_id:
            self.log_test("KB Query Test", False, "KB ID not available")
            return False
        
        try:
            # Test query using retrieve API
            test_query = "What information do you have about conveyor systems and maintenance?"
            
            print(f"    Query: {test_query}")
            
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.new_kb_id,
                retrievalQuery={'text': test_query}
            )
            
            results = response.get('retrievalResults', [])
            
            print(f"    Retrieved {len(results)} results")
            
            if results:
                for i, result in enumerate(results[:3], 1):  # Show first 3 results
                    content = result.get('content', {}).get('text', 'No content')
                    score = result.get('score', 0)
                    
                    print(f"      Result {i} (Score: {score:.3f}): {content[:100]}...")
                
                success = True
                details = f"Retrieved {len(results)} results"
            else:
                success = False
                details = "No results retrieved"
            
            self.log_test("KB Query Test", success, details)
            return success
            
        except Exception as e:
            self.log_test("KB Query Test", False, str(e))
            return False
    
    def test_agent_with_new_kb(self) -> bool:
        """Test if the agent can use the new Knowledge Base."""
        print(f"\n🤖 Testing Agent with New Knowledge Base...")
        
        try:
            # Test queries that should use the new KB
            test_queries = [
                "What do you know about conveyor inference and maintenance?",
                "Tell me about conveyor system analysis",
                "What maintenance data is available for conveyor systems?"
            ]
            
            successful_queries = 0
            
            for i, query in enumerate(test_queries, 1):
                print(f"    Query {i}: {query}")
                
                try:
                    response = self.bedrock_agent_runtime.invoke_agent(
                        agentId=self.agent_id,
                        agentAliasId=self.agent_alias_id,
                        sessionId=f'new-kb-test-{i}-{int(time.time())}',
                        inputText=query
                    )
                    
                    # Process streaming response
                    full_response = ""
                    for event in response['completion']:
                        if 'chunk' in event:
                            chunk = event['chunk']
                            if 'bytes' in chunk:
                                chunk_text = chunk['bytes'].decode('utf-8')
                                full_response += chunk_text
                    
                    if full_response and len(full_response) > 20:
                        successful_queries += 1
                        print(f"      ✅ Response: {full_response[:80]}...")
                    else:
                        print(f"      ❌ No meaningful response")
                        
                except Exception as e:
                    print(f"      ❌ Error: {str(e)}")
            
            success_rate = successful_queries / len(test_queries)
            success = success_rate >= 0.5
            
            details = f"Success: {successful_queries}/{len(test_queries)} ({success_rate:.0%})"
            
            self.log_test("Agent with New KB", success, details)
            return success
            
        except Exception as e:
            self.log_test("Agent with New KB", False, str(e))
            return False
    
    def update_config_with_new_kb(self) -> bool:
        """Update the AWS config with the new Knowledge Base ID."""
        print(f"\n🔧 Updating Configuration...")
        
        if not self.new_kb_id:
            self.log_test("Config Update", False, "No KB ID to update")
            return False
        
        try:
            # Read current config
            with open('config/aws_config.json', 'r') as f:
                config = json.load(f)
            
            # Add new KB ID
            config['new_knowledge_base_id'] = self.new_kb_id
            config['new_knowledge_base_name'] = self.new_kb_name
            
            # Update lambda environment variables to include new KB
            if 'lambda_functions' in config and 'query_handler' in config['lambda_functions']:
                env_vars = config['lambda_functions']['query_handler']['environment_variables']
                env_vars['NEW_KNOWLEDGE_BASE_ID'] = self.new_kb_id
            
            # Write updated config
            with open('config/aws_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            self.log_test("Config Update", True, f"Added KB ID: {self.new_kb_id}")
            return True
            
        except Exception as e:
            self.log_test("Config Update", False, str(e))
            return False
    
    def generate_integration_script(self):
        """Generate script to integrate new KB with the agent."""
        print(f"\n📝 Generating Integration Script...")
        
        if not self.new_kb_id:
            print("    ⚠️  No KB ID available for integration script")
            return
        
        integration_script = f'''#!/usr/bin/env python3
"""
Integrate the new Knowledge Base with the Bedrock Agent.
KB ID: {self.new_kb_id}
KB Name: {self.new_kb_name}
"""

import boto3
import json

def integrate_new_knowledge_base():
    """Integrate the new Knowledge Base with the existing agent."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    agent_id = "{self.agent_id}"
    new_kb_id = "{self.new_kb_id}"
    
    try:
        # Get current agent configuration
        agent_response = bedrock_agent.get_agent(agentId=agent_id)
        agent = agent_response['agent']
        
        print(f"Current agent: {{agent['agentName']}}")
        
        # Check if agent already has knowledge bases associated
        try:
            kb_response = bedrock_agent.list_agent_knowledge_bases(agentId=agent_id)
            current_kbs = kb_response['agentKnowledgeBaseSummaries']
            
            print(f"Current Knowledge Bases: {{len(current_kbs)}}")
            for kb in current_kbs:
                print(f"  - {{kb['knowledgeBaseId']}}: {{kb.get('description', 'No description')}}")
            
            # Check if new KB is already associated
            kb_ids = [kb['knowledgeBaseId'] for kb in current_kbs]
            if new_kb_id in kb_ids:
                print(f"✅ Knowledge Base {{new_kb_id}} is already associated with the agent")
                return True
            
        except Exception as e:
            print(f"No existing knowledge bases or error: {{e}}")
            current_kbs = []
        
        # Associate new knowledge base with agent
        print(f"🔗 Associating Knowledge Base {{new_kb_id}} with agent...")
        
        bedrock_agent.associate_agent_knowledge_base(
            agentId=agent_id,
            knowledgeBaseId=new_kb_id,
            description="Conveyor inference and maintenance knowledge base",
            knowledgeBaseState="ENABLED"
        )
        
        print("✅ Knowledge Base associated successfully!")
        
        # Prepare agent (create new version)
        print("🔄 Preparing agent with new knowledge base...")
        
        prepare_response = bedrock_agent.prepare_agent(agentId=agent_id)
        
        print("✅ Agent prepared successfully!")
        print(f"Agent status: {{prepare_response['agentStatus']}}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error integrating knowledge base: {{str(e)}}")
        return False

if __name__ == "__main__":
    integrate_new_knowledge_base()
'''
        
        with open('integrate_new_knowledge_base.py', 'w') as f:
            f.write(integration_script)
        
        print("    ✅ Created: integrate_new_knowledge_base.py")
    
    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive testing of the new Knowledge Base."""
        print("🔍 Testing New Knowledge Base: knowledge-base-conveyor-inference")
        print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Discover the new KB
        kb_id = self.discover_new_knowledge_base()
        
        if not kb_id:
            print("❌ Cannot proceed without Knowledge Base ID")
            return {'success': False, 'error': 'Knowledge Base not found'}
        
        # Run tests
        tests_passed = 0
        total_tests = 0
        
        # Test KB status
        total_tests += 1
        if self.test_new_knowledge_base_status():
            tests_passed += 1
        
        # Test KB query
        total_tests += 1
        if self.test_knowledge_base_query():
            tests_passed += 1
        
        # Test agent integration
        total_tests += 1
        if self.test_agent_with_new_kb():
            tests_passed += 1
        
        # Update configuration
        total_tests += 1
        if self.update_config_with_new_kb():
            tests_passed += 1
        
        # Generate integration script
        self.generate_integration_script()
        
        # Generate summary
        success_rate = tests_passed / total_tests
        overall_success = success_rate >= 0.75
        
        summary = {
            'success': overall_success,
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'new_kb_id': self.new_kb_id,
            'new_kb_name': self.new_kb_name,
            'test_results': self.test_results
        }
        
        self.print_summary(summary)
        return summary
    
    def print_summary(self, summary: Dict):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📊 NEW KNOWLEDGE BASE TEST SUMMARY")
        print("=" * 70)
        
        overall_status = "✅ SUCCESS" if summary['success'] else "❌ NEEDS ATTENTION"
        print(f"Overall Status: {overall_status}")
        print(f"Tests Passed: {summary['tests_passed']}/{summary['total_tests']} ({summary['success_rate']:.0%})")
        print(f"Knowledge Base ID: {summary['new_kb_id']}")
        print(f"Knowledge Base Name: {summary['new_kb_name']}")
        
        print("\n📋 Test Results:")
        for result in summary['test_results']:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 Next Steps:")
        if summary['success']:
            print("✅ New Knowledge Base is ready for integration!")
            print("📝 Recommended actions:")
            print("   1. Run: python integrate_new_knowledge_base.py")
            print("   2. Test agent with new KB data")
            print("   3. Update Lambda function environment variables")
            print("   4. Deploy updated configuration")
        else:
            print("⚠️  Address the following issues:")
            failed_tests = [r for r in summary['test_results'] if not r['success']]
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        print("\n📁 Files Generated:")
        print("   • integrate_new_knowledge_base.py - Integration script")
        print("   • config/aws_config.json - Updated with new KB ID")
        
        print("\n" + "=" * 70)

def main():
    """Main function."""
    tester = NewKnowledgeBaseTester()
    results = tester.run_comprehensive_test()
    
    import sys
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()