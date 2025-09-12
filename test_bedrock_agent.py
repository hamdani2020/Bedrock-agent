#!/usr/bin/env python3
"""
Bedrock Agent Testing Script

This script tests the created Bedrock Agent with various maintenance-related queries
to verify functionality and response quality.
"""

import json
import boto3
import time
import logging
from typing import Dict, Any, List
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BedrockAgentTester:
    """Test Bedrock Agent functionality"""
    
    def __init__(self, config_file: str = "config/aws_config.json"):
        """Initialize with configuration"""
        self.config = self._load_config(config_file)
        
        # Initialize AWS clients
        self.region = self.config.get('region', 'us-west-2')
        self.bedrock_runtime_client = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        # Get agent configuration
        self.agent_id = self.config['lambda_functions']['query_handler']['environment_variables'].get('BEDROCK_AGENT_ID')
        self.alias_id = self.config['lambda_functions']['query_handler']['environment_variables'].get('BEDROCK_AGENT_ALIAS_ID')
        
        if not self.agent_id or not self.alias_id:
            raise ValueError("Agent ID or Alias ID not found in configuration. Please run bedrock_agent_setup.py first.")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def invoke_agent(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Invoke the agent with a query"""
        if not session_id:
            session_id = f"test-session-{int(time.time())}"
        
        try:
            logger.info(f"Invoking agent with query: {query[:100]}...")
            
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.alias_id,
                sessionId=session_id,
                inputText=query
            )
            
            # Process streaming response
            response_text = ""
            citations = []
            trace_data = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
                elif 'trace' in event:
                    trace_data.append(event['trace'])
            
            return {
                'response': response_text.strip(),
                'citations': citations,
                'trace': trace_data,
                'session_id': session_id,
                'success': True
            }
            
        except ClientError as e:
            logger.error(f"Failed to invoke agent: {e}")
            return {
                'response': '',
                'error': str(e),
                'success': False
            }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        test_cases = [
            {
                'category': 'Fault Analysis',
                'queries': [
                    "What are the most common types of equipment faults in our historical data?",
                    "Can you analyze bearing wear patterns and their typical progression?",
                    "What sensor readings typically indicate impending pump failures?",
                    "Show me patterns for high-temperature equipment failures."
                ]
            },
            {
                'category': 'Maintenance Recommendations',
                'queries': [
                    "What preventive maintenance should be performed on equipment showing vibration anomalies?",
                    "Recommend maintenance schedules for pumps based on historical failure patterns.",
                    "What immediate actions should be taken for critical bearing faults?",
                    "Suggest inspection procedures for equipment with temperature warnings."
                ]
            },
            {
                'category': 'Pattern Recognition',
                'queries': [
                    "Are there seasonal patterns in equipment failures?",
                    "What correlations exist between sensor readings and fault occurrences?",
                    "Identify early warning indicators that precede equipment failures.",
                    "Compare fault patterns between different equipment types."
                ]
            },
            {
                'category': 'Risk Assessment',
                'queries': [
                    "Prioritize maintenance tasks based on equipment criticality and fault risk.",
                    "Estimate time-to-failure for equipment showing degrading performance.",
                    "What safety protocols should be followed for high-risk fault scenarios?",
                    "Assess the maintenance effectiveness based on historical data."
                ]
            }
        ]
        
        results = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'categories': {},
            'detailed_results': []
        }
        
        session_id = f"comprehensive-test-{int(time.time())}"
        
        for category_data in test_cases:
            category = category_data['category']
            queries = category_data['queries']
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing Category: {category}")
            logger.info(f"{'='*50}")
            
            category_results = {
                'total': len(queries),
                'successful': 0,
                'failed': 0,
                'tests': []
            }
            
            for i, query in enumerate(queries, 1):
                results['total_tests'] += 1
                
                logger.info(f"\nTest {i}/{len(queries)}: {query}")
                
                # Invoke agent
                result = self.invoke_agent(query, session_id)
                
                test_result = {
                    'query': query,
                    'category': category,
                    'success': result['success'],
                    'response_length': len(result.get('response', '')),
                    'has_citations': len(result.get('citations', [])) > 0,
                    'error': result.get('error', None)
                }
                
                if result['success'] and result['response']:
                    logger.info(f"✅ Success - Response: {len(result['response'])} characters")
                    logger.info(f"Response preview: {result['response'][:200]}...")
                    
                    results['successful_tests'] += 1
                    category_results['successful'] += 1
                    test_result['success'] = True
                else:
                    logger.error(f"❌ Failed - {result.get('error', 'No response')}")
                    results['failed_tests'] += 1
                    category_results['failed'] += 1
                    test_result['success'] = False
                
                category_results['tests'].append(test_result)
                results['detailed_results'].append(test_result)
                
                # Small delay between tests
                time.sleep(1)
            
            results['categories'][category] = category_results
            
            logger.info(f"\nCategory Summary: {category_results['successful']}/{category_results['total']} passed")
        
        return results
    
    def run_interactive_test(self):
        """Run interactive test session"""
        logger.info("Starting interactive test session...")
        logger.info("Type 'quit' to exit, 'help' for sample queries")
        
        session_id = f"interactive-{int(time.time())}"
        
        sample_queries = [
            "What are the most common equipment faults?",
            "Analyze bearing wear patterns",
            "Recommend maintenance for vibration issues",
            "Show temperature-related failure patterns",
            "Assess pump failure risks"
        ]
        
        while True:
            try:
                query = input("\nEnter your query: ").strip()
                
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'help':
                    print("\nSample queries:")
                    for i, sample in enumerate(sample_queries, 1):
                        print(f"{i}. {sample}")
                    continue
                elif not query:
                    continue
                
                result = self.invoke_agent(query, session_id)
                
                if result['success']:
                    print(f"\n{'='*60}")
                    print("AGENT RESPONSE:")
                    print(f"{'='*60}")
                    print(result['response'])
                    print(f"{'='*60}")
                else:
                    print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                
            except KeyboardInterrupt:
                print("\n\nExiting interactive session...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate a formatted test report"""
        report = []
        report.append("BEDROCK AGENT TEST REPORT")
        report.append("=" * 60)
        report.append(f"Total Tests: {results['total_tests']}")
        report.append(f"Successful: {results['successful_tests']}")
        report.append(f"Failed: {results['failed_tests']}")
        report.append(f"Success Rate: {(results['successful_tests']/results['total_tests']*100):.1f}%")
        report.append("")
        
        # Category breakdown
        report.append("CATEGORY BREAKDOWN:")
        report.append("-" * 30)
        for category, data in results['categories'].items():
            success_rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
            report.append(f"{category}: {data['successful']}/{data['total']} ({success_rate:.1f}%)")
        
        report.append("")
        
        # Failed tests details
        failed_tests = [test for test in results['detailed_results'] if not test['success']]
        if failed_tests:
            report.append("FAILED TESTS:")
            report.append("-" * 20)
            for test in failed_tests:
                report.append(f"• {test['category']}: {test['query'][:80]}...")
                if test['error']:
                    report.append(f"  Error: {test['error']}")
        
        return "\n".join(report)

def main():
    """Main execution function"""
    try:
        tester = BedrockAgentTester()
        
        print("Bedrock Agent Testing Suite")
        print("=" * 40)
        print("1. Run comprehensive tests")
        print("2. Run interactive test session")
        print("3. Exit")
        
        while True:
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == '1':
                print("\nRunning comprehensive test suite...")
                results = tester.run_comprehensive_tests()
                
                # Generate and display report
                report = tester.generate_test_report(results)
                print(f"\n{report}")
                
                # Save report to file
                with open('bedrock_agent_test_report.txt', 'w') as f:
                    f.write(report)
                print("\nTest report saved to: bedrock_agent_test_report.txt")
                
                break
                
            elif choice == '2':
                tester.run_interactive_test()
                break
                
            elif choice == '3':
                print("Exiting...")
                break
                
            else:
                print("Invalid choice. Please select 1, 2, or 3.")
    
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        print(f"❌ Testing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())