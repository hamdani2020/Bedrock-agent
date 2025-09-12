#!/usr/bin/env python3
"""
Test script for Bedrock Knowledge Base functionality.

This script tests the created Knowledge Base with various queries
to ensure it's working correctly with the fault prediction data.
"""

import json
import boto3
import sys
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Any

class KnowledgeBaseTester:
    def __init__(self, config_file: str = "config/aws_config.json"):
        """Initialize the Knowledge Base tester."""
        self.config = self._load_config(config_file)
        self.region = self.config["region"]
        
        try:
            self.bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=self.region)
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please configure your AWS credentials.")
            sys.exit(1)
        
        # Get Knowledge Base ID from config
        self.knowledge_base_id = self.config["lambda_functions"]["data_sync"]["environment_variables"].get("KNOWLEDGE_BASE_ID")
        if not self.knowledge_base_id:
            print("❌ Knowledge Base ID not found in configuration. Please run create_knowledge_base.py first.")
            sys.exit(1)
        
        print(f"✅ Initialized tester for Knowledge Base: {self.knowledge_base_id}")

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file {config_file} not found")
            sys.exit(1)

    def test_query(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Test a single query against the Knowledge Base."""
        try:
            print(f"\n🔍 Testing query: '{query}'")
            
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = response.get('retrievalResults', [])
            print(f"📊 Retrieved {len(results)} results")
            
            # Display results
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                content = result.get('content', {}).get('text', '')
                location = result.get('location', {})
                
                print(f"\n   Result {i} (Score: {score:.3f}):")
                print(f"   Content: {content[:200]}...")
                if location:
                    print(f"   Source: {location.get('s3Location', {}).get('uri', 'Unknown')}")
            
            return {
                'query': query,
                'result_count': len(results),
                'results': results,
                'success': True
            }
            
        except ClientError as e:
            print(f"❌ Query failed: {e}")
            return {
                'query': query,
                'result_count': 0,
                'results': [],
                'success': False,
                'error': str(e)
            }

    def run_comprehensive_tests(self) -> List[Dict[str, Any]]:
        """Run a comprehensive set of test queries."""
        test_queries = [
            # Basic fault queries
            "What are the most common types of equipment faults?",
            "Show me recent bearing failures",
            "What causes ball bearing faults?",
            
            # Sensor-based queries
            "What sensor readings indicate critical faults?",
            "When does vibration indicate a problem?",
            "What temperature readings are dangerous?",
            
            # Maintenance queries
            "What immediate actions are needed for critical faults?",
            "How do I prevent bearing failures?",
            "What maintenance is recommended for high vibration?",
            
            # Risk and safety queries
            "What are high risk fault conditions?",
            "Which faults require immediate shutdown?",
            "What safety protocols should be followed?",
            
            # Pattern analysis queries
            "What patterns indicate equipment degradation?",
            "How do sensor readings correlate with faults?",
            "What are early warning signs of failure?"
        ]
        
        print("🧪 Running comprehensive Knowledge Base tests...")
        print("=" * 60)
        
        results = []
        successful_queries = 0
        
        for query in test_queries:
            result = self.test_query(query)
            results.append(result)
            
            if result['success'] and result['result_count'] > 0:
                successful_queries += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total queries tested: {len(test_queries)}")
        print(f"Successful queries: {successful_queries}")
        print(f"Success rate: {(successful_queries/len(test_queries)*100):.1f}%")
        
        if successful_queries == len(test_queries):
            print("✅ All tests passed! Knowledge Base is working correctly.")
        elif successful_queries > len(test_queries) * 0.8:
            print("⚠️  Most tests passed. Knowledge Base is mostly functional.")
        else:
            print("❌ Many tests failed. Knowledge Base may need attention.")
        
        return results

    def test_specific_fault_types(self) -> Dict[str, Any]:
        """Test queries for specific fault types found in the data."""
        fault_specific_queries = [
            "Ball Bearing Fault analysis",
            "Normal Operation status",
            "Critical fault conditions",
            "High vibration readings",
            "Temperature anomalies"
        ]
        
        print("\n🔧 Testing fault-specific queries...")
        results = {}
        
        for query in fault_specific_queries:
            result = self.test_query(query, max_results=3)
            results[query] = result
        
        return results

    def validate_data_ingestion(self) -> bool:
        """Validate that data has been properly ingested."""
        print("\n📋 Validating data ingestion...")
        
        # Test with a very general query that should return results
        general_query = "equipment sensor data"
        result = self.test_query(general_query, max_results=10)
        
        if result['success'] and result['result_count'] > 0:
            print("✅ Data ingestion validation passed")
            return True
        else:
            print("❌ Data ingestion validation failed - no results found")
            return False


def main():
    """Main execution function."""
    print("Bedrock Knowledge Base Tester")
    print("=" * 40)
    
    try:
        tester = KnowledgeBaseTester()
        
        # Validate data ingestion first
        if not tester.validate_data_ingestion():
            print("❌ Data ingestion validation failed. Exiting.")
            return 1
        
        # Run comprehensive tests
        results = tester.run_comprehensive_tests()
        
        # Test fault-specific queries
        fault_results = tester.test_specific_fault_types()
        
        # Save results to file
        test_results = {
            'comprehensive_tests': results,
            'fault_specific_tests': fault_results,
            'timestamp': str(boto3.Session().region_name)
        }
        
        with open('knowledge_base_test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n📄 Test results saved to knowledge_base_test_results.json")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())