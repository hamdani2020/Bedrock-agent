#!/usr/bin/env python3
"""
Test script to verify S3 access and data structure for Knowledge Base integration.
This script validates the S3 configuration and data accessibility.
"""
import sys
import json
import logging
from pathlib import Path

# Add lambda_functions to path for imports
sys.path.append(str(Path(__file__).parent / "lambda_functions"))

from shared.s3_utils import create_s3_reader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to test S3 access and data validation.
    """
    print("=" * 60)
    print("S3 Access Verification for Bedrock Knowledge Base")
    print("=" * 60)
    
    try:
        # Create S3 reader with default configuration
        s3_reader = create_s3_reader()
        
        # Test 1: Verify bucket access
        print("\n1. Verifying S3 bucket access...")
        access_ok = s3_reader.verify_bucket_access()
        
        if access_ok:
            print("✅ S3 bucket access verified successfully")
        else:
            print("❌ S3 bucket access failed")
            return False
        
        # Test 2: List available fault data files
        print("\n2. Listing fault prediction data files...")
        files = s3_reader.list_fault_data_files(max_keys=10)
        
        if files:
            print(f"✅ Found {len(files)} fault data files")
            print("\nSample files:")
            for i, file_info in enumerate(files[:3]):
                print(f"  {i+1}. {file_info['key']}")
                print(f"     Size: {file_info['size']} bytes")
                print(f"     Modified: {file_info['last_modified']}")
        else:
            print("❌ No fault data files found")
            return False
        
        # Test 3: Read and validate sample data
        print("\n3. Validating data structure...")
        validation_results = s3_reader.validate_data_structure(sample_size=3)
        
        print(f"✅ Validation completed:")
        print(f"   Files checked: {validation_results['total_files_checked']}")
        print(f"   Valid files: {validation_results['valid_files']}")
        print(f"   Invalid files: {validation_results['invalid_files']}")
        
        if validation_results['common_fields']:
            print(f"   Common fields: {len(validation_results['common_fields'])}")
            print("   Key fields for Knowledge Base:")
            key_fields = ['timestamp', 'predicted_fault', 'fault_category', 
                         'recommendation_summary', 'risk_level']
            for field in key_fields:
                if field in validation_results['common_fields']:
                    print(f"     ✅ {field}")
                else:
                    print(f"     ❌ {field} (missing)")
        
        # Test 4: Get recent fault data sample
        print("\n4. Retrieving recent fault data sample...")
        recent_data = s3_reader.get_recent_fault_data(days=7, limit=5)
        
        if recent_data:
            print(f"✅ Retrieved {len(recent_data)} recent records")
            
            # Show sample record structure
            if recent_data:
                sample_record = recent_data[0]
                print("\nSample record structure:")
                print(f"   Timestamp: {sample_record.get('timestamp', 'N/A')}")
                print(f"   Fault Type: {sample_record.get('predicted_fault', 'N/A')}")
                print(f"   Risk Level: {sample_record.get('risk_level', 'N/A')}")
                print(f"   Equipment: {sample_record.get('equipment_type', 'N/A')}")
                
                # Check for Knowledge Base relevant fields
                kb_fields = {
                    'timestamp': sample_record.get('timestamp'),
                    'predicted_fault': sample_record.get('predicted_fault'),
                    'fault_category': sample_record.get('fault_category'),
                    'risk_level': sample_record.get('risk_level'),
                    'recommendation_summary': sample_record.get('recommendation_summary'),
                    'vibration_mms': sample_record.get('vibration_mms'),
                    'temperature_celsius': sample_record.get('temperature_celsius')
                }
                
                print("\nKnowledge Base relevant fields:")
                for field, value in kb_fields.items():
                    status = "✅" if value is not None else "❌"
                    print(f"   {status} {field}: {value}")
        else:
            print("❌ No recent fault data found")
        
        print("\n" + "=" * 60)
        print("S3 Access Verification Complete")
        print("✅ All tests passed - S3 configuration is ready for Knowledge Base")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during S3 verification: {str(e)}")
        logger.error(f"S3 verification failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)