#!/usr/bin/env python3
"""
Redeploy Lambda function with hardcoded environment variables.
"""
import boto3
import json
import zipfile
import os
from pathlib import Path

def create_lambda_deployment_package():
    """Create deployment package with updated Lambda function."""
    
    print("📦 Creating Lambda deployment package with hardcoded values...")
    
    # Create deployment directory
    deploy_dir = Path("lambda_deploy")
    deploy_dir.mkdir(exist_ok=True)
    
    zip_path = deploy_dir / "lambda_function.zip"
    
    # Remove existing zip if it exists
    if zip_path.exists():
        zip_path.unlink()
    
    # Create zip file with Lambda function
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the main Lambda function
        zip_file.write(
            'lambda_functions/query_handler/lambda_function.py', 
            'lambda_function.py'
        )
    
    print(f"✅ Created deployment package: {zip_path}")
    return zip_path

def deploy_updated_lambda():
    """Deploy the updated Lambda function."""
    
    print("\n🚀 Deploying updated Lambda function...")
    
    # Load configuration
    try:
        with open('config/aws_config.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    # Get Lambda configuration
    lambda_config = config['lambda_functions']['query_handler']
    function_name = lambda_config['function_name']
    region = config['region']
    
    print(f"Function Name: {function_name}")
    print(f"Region: {region}")
    
    # Create deployment package
    zip_path = create_lambda_deployment_package()
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # Read the zip file
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        print(f"📤 Uploading function code ({len(zip_content)} bytes)...")
        
        # Update function code
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function code updated successfully!")
        print(f"   Version: {response.get('Version', 'Unknown')}")
        print(f"   Last Modified: {response.get('LastModified', 'Unknown')}")
        print(f"   Code Size: {response.get('CodeSize', 0)} bytes")
        
        # Wait for update to complete
        print(f"⏳ Waiting for deployment to complete...")
        
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(
            FunctionName=function_name,
            WaiterConfig={
                'Delay': 2,
                'MaxAttempts': 30
            }
        )
        
        print(f"✅ Deployment completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error deploying Lambda function: {e}")
        return False
    
    finally:
        # Clean up deployment package
        if zip_path.exists():
            zip_path.unlink()
            print(f"🧹 Cleaned up deployment package")

def test_deployed_lambda():
    """Test the deployed Lambda function."""
    
    print("\n🧪 Testing deployed Lambda function...")
    
    import requests
    import uuid
    
    lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # Test queries
    test_queries = [
        "What faults have been detected in the equipment?",
        "Show me data for conveyor_motor_001",
        "What are the sensor readings for conveyor_motor_001 from September 11, 2025?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: {query}")
        print("-" * 50)
        
        try:
            payload = {
                "query": query,
                "sessionId": str(uuid.uuid4())
            }
            
            response = requests.post(
                lambda_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                print(f"Response Length: {len(response_text)} characters")
                print(f"Response Preview: {response_text[:200]}...")
                
                # Check for specific data indicators
                specific_indicators = [
                    "conveyor_motor_001", "ball bearing fault", "belt slippage",
                    "September 11", "2025-09-11", "RPM", "temperature", "vibration"
                ]
                
                error_indicators = [
                    "Service configuration error", "not properly configured",
                    "Missing required environment variables", "function call format"
                ]
                
                has_specific = any(indicator.lower() in response_text.lower() for indicator in specific_indicators)
                has_error = any(indicator.lower() in response_text.lower() for indicator in error_indicators)
                
                if has_error:
                    print("❌ Still has configuration errors")
                elif has_specific:
                    print("✅ Contains specific data - SUCCESS!")
                else:
                    print("⚠️  Generic response but no errors")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data}")
                except:
                    print(f"Error response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"❌ Request error: {e}")

def verify_hardcoded_values():
    """Verify the hardcoded values are correct."""
    
    print("🔍 Verifying hardcoded values in Lambda function...")
    
    # Read the Lambda function file
    try:
        with open('lambda_functions/query_handler/lambda_function.py', 'r') as f:
            content = f.read()
        
        # Check for hardcoded values
        if "BEDROCK_AGENT_ID = 'GMJGK6RO4S'" in content:
            print("✅ BEDROCK_AGENT_ID is hardcoded correctly")
        else:
            print("❌ BEDROCK_AGENT_ID not found or incorrect")
            return False
            
        if "BEDROCK_AGENT_ALIAS_ID = 'RUWFC5DRPQ'" in content:
            print("✅ BEDROCK_AGENT_ALIAS_ID is hardcoded correctly")
        else:
            print("❌ BEDROCK_AGENT_ALIAS_ID not found or incorrect")
            return False
        
        # Check that environment variable calls are removed
        if "os.environ.get('BEDROCK_AGENT_ID')" in content:
            print("⚠️  Still contains environment variable calls")
        else:
            print("✅ Environment variable calls removed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Lambda function: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Redeploying Lambda Function with Hardcoded Values")
    print("=" * 60)
    
    # Verify hardcoded values
    if not verify_hardcoded_values():
        print("❌ Hardcoded values verification failed")
        exit(1)
    
    # Deploy the updated function
    if deploy_updated_lambda():
        print("\n🎉 Lambda function redeployed successfully!")
        
        # Test the deployed function
        test_deployed_lambda()
        
        print("\n" + "=" * 60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("The Lambda function now has hardcoded agent configuration.")
        print("Test your Streamlit app to see if it now returns specific data.")
        print("\nTo test:")
        print("1. Run: python run_streamlit.py")
        print("2. Ask: 'What faults have been detected in the equipment?'")
        print("3. You should now see specific conveyor_motor_001 data!")
        
    else:
        print("\n❌ Deployment failed!")
        print("Please check AWS permissions and try again.")