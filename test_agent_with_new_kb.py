#!/usr/bin/env python3
"""
Test the Bedrock Agent with the newly integrated Knowledge Base.
Verify it can access conveyor inference data.
"""

import boto3
import time
from datetime import datetime
from typing import Dict, List

class AgentNewKBTester:
    """Test agent with the new Knowledge Base integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.region = "us-west-2"
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        self.agent_id = "GMJGK6RO4S"
        self.agent_alias_id = "RUWFC5DRPQ"
        self.new_kb_id = "ZECQSVPQJZ"
        
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
    
    def invoke_agent(self, query: str, session_id: str) -> str:
        """Invoke the agent with a query."""
        try:
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
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
            
            return full_response.strip()
            
        except Exception as e:
            print(f"    Error invoking agent: {str(e)}")
            return ""
    
    def test_conveyor_specific_queries(self) -> bool:
        """Test queries specific to conveyor systems."""
        print("\n🔧 Testing Conveyor-Specific Queries...")
        
        conveyor_queries = [
            {
                'query': 'What is the status of conveyor_motor_001?',
                'description': 'Specific conveyor motor query',
                'expected_keywords': ['conveyor_motor_001', 'motor', 'status']
            },
            {
                'query': 'Show me the operating conditions for the conveyor system',
                'description': 'Operating conditions query',
                'expected_keywords': ['operating', 'conditions', 'conveyor']
            },
            {
                'query': 'What maintenance data do you have for conveyor systems?',
                'description': 'Maintenance data query',
                'expected_keywords': ['maintenance', 'conveyor', 'data']
            },
            {
                'query': 'Are there any alerts or issues with the conveyor motor?',
                'description': 'Alert and issues query',
                'expected_keywords': ['alert', 'issue', 'motor', 'conveyor']
            }
        ]
        
        successful_queries = 0
        
        for i, test_case in enumerate(conveyor_queries, 1):
            print(f"\n  Query {i}: {test_case['description']}")
            print(f"    Question: {test_case['query']}")
            
            session_id = f'conveyor-test-{i}-{int(time.time())}'
            response = self.invoke_agent(test_case['query'], session_id)
            
            if response:
                print(f"    Response: {response[:150]}...")
                
                # Check if response contains expected keywords
                response_lower = response.lower()
                keyword_matches = sum(1 for keyword in test_case['expected_keywords'] 
                                    if keyword.lower() in response_lower)
                
                # Check if response seems to use specific data (not just general advice)
                specific_indicators = [
                    'device id', 'timestamp', 'operating condition', 
                    'conveyor_motor_001', 'device report', 'sensor'
                ]
                
                has_specific_data = any(indicator in response_lower for indicator in specific_indicators)
                
                if keyword_matches >= 2 or has_specific_data:
                    successful_queries += 1
                    print(f"    ✅ Good response (Keywords: {keyword_matches}, Specific: {has_specific_data})")
                else:
                    print(f"    ⚠️  Generic response (Keywords: {keyword_matches}, Specific: {has_specific_data})")
            else:
                print(f"    ❌ No response received")
        
        success_rate = successful_queries / len(conveyor_queries)
        success = success_rate >= 0.5
        
        details = f"Success: {successful_queries}/{len(conveyor_queries)} ({success_rate:.0%})"
        self.log_test("Conveyor-Specific Queries", success, details)
        return success
    
    def test_knowledge_base_citations(self) -> bool:
        """Test if the agent provides citations from the new Knowledge Base."""
        print("\n📚 Testing Knowledge Base Citations...")
        
        citation_queries = [
            "What specific data do you have about conveyor motor 001?",
            "Show me the latest device reports for conveyor systems",
            "What are the current operating conditions based on your data?"
        ]
        
        citations_found = 0
        
        for i, query in enumerate(citation_queries, 1):
            print(f"\n  Citation Test {i}: {query}")
            
            session_id = f'citation-test-{i}-{int(time.time())}'
            response = self.invoke_agent(query, session_id)
            
            if response:
                print(f"    Response: {response[:150]}...")
                
                # Look for citation indicators
                citation_indicators = [
                    'based on', 'according to', 'from the data', 'device report',
                    'timestamp', 'device id', 'source', 'data shows'
                ]
                
                has_citations = any(indicator in response.lower() for indicator in citation_indicators)
                
                if has_citations:
                    citations_found += 1
                    print(f"    ✅ Contains citations/references")
                else:
                    print(f"    ⚠️  No clear citations found")
            else:
                print(f"    ❌ No response received")
        
        success_rate = citations_found / len(citation_queries)
        success = success_rate >= 0.5
        
        details = f"Citations: {citations_found}/{len(citation_queries)} ({success_rate:.0%})"
        self.log_test("Knowledge Base Citations", success, details)
        return success
    
    def test_data_freshness(self) -> bool:
        """Test if the agent can access recent data from the new KB."""
        print("\n🕒 Testing Data Freshness...")
        
        freshness_queries = [
            "What is the most recent data you have about conveyor systems?",
            "Show me the latest timestamp in your conveyor data",
            "What recent device reports do you have?"
        ]
        
        fresh_data_found = 0
        
        for i, query in enumerate(freshness_queries, 1):
            print(f"\n  Freshness Test {i}: {query}")
            
            session_id = f'freshness-test-{i}-{int(time.time())}'
            response = self.invoke_agent(query, session_id)
            
            if response:
                print(f"    Response: {response[:150]}...")
                
                # Look for recent timestamps or fresh data indicators
                freshness_indicators = [
                    '2025-09', '2025-08', 'recent', 'latest', 'current',
                    'timestamp', 'today', 'yesterday'
                ]
                
                has_fresh_data = any(indicator in response.lower() for indicator in freshness_indicators)
                
                if has_fresh_data:
                    fresh_data_found += 1
                    print(f"    ✅ Contains fresh/recent data references")
                else:
                    print(f"    ⚠️  No clear fresh data indicators")
            else:
                print(f"    ❌ No response received")
        
        success_rate = fresh_data_found / len(freshness_queries)
        success = success_rate >= 0.33  # Lower threshold for freshness
        
        details = f"Fresh data: {fresh_data_found}/{len(freshness_queries)} ({success_rate:.0%})"
        self.log_test("Data Freshness", success, details)
        return success
    
    def test_comparative_analysis(self) -> bool:
        """Test if agent can compare data from both knowledge bases."""
        print("\n🔄 Testing Comparative Analysis...")
        
        comparative_queries = [
            "Compare the conveyor data with general maintenance recommendations",
            "How does the conveyor motor data relate to fault prediction patterns?",
            "What insights can you provide by combining conveyor data with maintenance analytics?"
        ]
        
        comparative_responses = 0
        
        for i, query in enumerate(comparative_queries, 1):
            print(f"\n  Comparative Test {i}: {query}")
            
            session_id = f'comparative-test-{i}-{int(time.time())}'
            response = self.invoke_agent(query, session_id)
            
            if response:
                print(f"    Response: {response[:150]}...")
                
                # Look for comparative analysis indicators
                comparative_indicators = [
                    'compare', 'comparison', 'both', 'combined', 'together',
                    'analysis', 'pattern', 'correlation', 'relationship'
                ]
                
                has_comparative = any(indicator in response.lower() for indicator in comparative_indicators)
                
                if has_comparative and len(response) > 100:
                    comparative_responses += 1
                    print(f"    ✅ Contains comparative analysis")
                else:
                    print(f"    ⚠️  Limited comparative analysis")
            else:
                print(f"    ❌ No response received")
        
        success_rate = comparative_responses / len(comparative_queries)
        success = success_rate >= 0.33  # Lower threshold for comparative analysis
        
        details = f"Comparative: {comparative_responses}/{len(comparative_queries)} ({success_rate:.0%})"
        self.log_test("Comparative Analysis", success, details)
        return success
    
    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive testing of agent with new KB."""
        print("🤖 Testing Bedrock Agent with New Knowledge Base")
        print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🆔 Agent ID: {self.agent_id}")
        print(f"📚 New KB ID: {self.new_kb_id}")
        print("=" * 70)
        
        # Wait a moment for agent preparation to complete
        print("⏳ Waiting for agent preparation to complete...")
        time.sleep(10)
        
        # Run tests
        tests_passed = 0
        total_tests = 0
        
        total_tests += 1
        if self.test_conveyor_specific_queries():
            tests_passed += 1
        
        total_tests += 1
        if self.test_knowledge_base_citations():
            tests_passed += 1
        
        total_tests += 1
        if self.test_data_freshness():
            tests_passed += 1
        
        total_tests += 1
        if self.test_comparative_analysis():
            tests_passed += 1
        
        # Generate summary
        success_rate = tests_passed / total_tests
        overall_success = success_rate >= 0.75
        
        summary = {
            'success': overall_success,
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'agent_id': self.agent_id,
            'new_kb_id': self.new_kb_id,
            'test_results': self.test_results
        }
        
        self.print_summary(summary)
        return summary
    
    def print_summary(self, summary: Dict):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📊 AGENT + NEW KNOWLEDGE BASE TEST SUMMARY")
        print("=" * 70)
        
        overall_status = "✅ SUCCESS" if summary['success'] else "⚠️  PARTIAL SUCCESS"
        print(f"Overall Status: {overall_status}")
        print(f"Tests Passed: {summary['tests_passed']}/{summary['total_tests']} ({summary['success_rate']:.0%})")
        print(f"Agent ID: {summary['agent_id']}")
        print(f"New KB ID: {summary['new_kb_id']}")
        
        print("\n📋 Test Results:")
        for result in summary['test_results']:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 Integration Status:")
        if summary['success']:
            print("✅ New Knowledge Base successfully integrated!")
            print("📝 Agent can now access:")
            print("   • Conveyor-specific device data")
            print("   • Operating conditions and status")
            print("   • Device reports with timestamps")
            print("   • Combined analysis from multiple KBs")
        else:
            print("⚠️  Knowledge Base integration needs attention:")
            print("   • Agent may still be preparing (try again in a few minutes)")
            print("   • Some queries may not be accessing new data")
            print("   • Consider checking agent preparation status")
        
        print("\n🚀 Next Steps:")
        print("   1. Test the updated agent via Lambda Function URL")
        print("   2. Update Streamlit app to leverage new conveyor data")
        print("   3. Monitor agent performance with dual KB setup")
        print("   4. Consider optimizing queries for better KB utilization")
        
        print("\n" + "=" * 70)

def main():
    """Main function."""
    tester = AgentNewKBTester()
    results = tester.run_comprehensive_test()
    
    import sys
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()