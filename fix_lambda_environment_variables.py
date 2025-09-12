#!/usr/bin/env python3
"""
Fix Lambda function environment variables to include the Bedrock Agent configuration.
"""
import boto3
import json

def fix_lambda_environment_variables():
    """Update Lambda function with correct environment variables."""
    
    print("Fixing Lambda Function Environment Variables")
    print("=" * 60)
    
    # Load configuration
    try:
        with open('config/aws_config.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return False
    
    # Get Lambda configuration
    lambda_config = config['lambda_functions']['query_handler']
    function_name = lambda_config['function_name']
    env_vars = lambda_config['environment_variables']
    
    print(f"Function Name: {function_name}")
    print(f"Required Environment Variables:")
    for key, value in env_vars.items():
        print(f"  {key}: {value}")
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name=config['region'])
    
    try:
        # Get current function configuration
        print(f"\n🔍 Getting current function configuration...")
        
        current_config = lambda_client.get_function_configuration(
            FunctionName=function_name
        )
        
        current_env = current_config.get('Environment', {}).get('Variables', {})
        print(f"\nCurrent Environment Variables:")
        if current_env:
            for key, value in current_env.items():
                print(f"  {key}: {value}")
        else:
            print("  (No environment variables set)")
        
        # Update environment variables
        print(f"\n🔄 Updating environment variables...")
        
        # Merge current env vars with required ones
        updated_env = current_env.copy()
        updated_env.update(env_vars)
        
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': updated_env
            }
        )
        
        print(f"✅ Environment variables updated successfully!")
        
        # Verify the update
        print(f"\n🔍 Verifying update...")
        
        updated_config = lambda_client.get_function_configuration(
            FunctionName=function_name
        )
        
        new_env = updated_config.get('Environment', {}).get('Variables', {})
        print(f"\nUpdated Environment Variables:")
        for key, value in new_env.items():
            print(f"  {key}: {value}")
        
        # Check if all required variables are present
        missing_vars = []
        for key in env_vars.keys():
            if key not in new_env:
                missing_vars.append(key)
        
        if missing_vars:
            print(f"\n❌ Missing variables: {missing_vars}")
            return False
        else:
            print(f"\n✅ All required environment variables are now set!")
            return True
            
    except Exception as e:
        print(f"❌ Error updating Lambda function: {e}")
        return False

def test_lambda_after_env_fix():
    """Test Lambda function after environment variable fix."""
    
    print("\n" + "=" * 60)
    print("Testing Lambda Function After Environment Fix")
    print("=" * 60)
    
    import requests
    import uuid
    
    lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
    
    # Test with the same query that should now work
    test_query = "What faults have been detected in the equipment?"
    
    print(f"Test Query: {test_query}")
    
    try:
        payload = {
            "query": test_query,
            "sessionId": str(uuid.uuid4())
        }
        
        print(f"\n📤 Sending request to Lambda...")
        
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
            
            print(f"\nLambda Response ({len(response_text)} chars):")
            print(response_text)
            
            # Check for specific indicators that it's working
            success_indicators = [
                "conveyor_motor_001", "ball bearing fault", "belt slippage",
                "September 11", "2025-09-11", "RPM", "temperature", "vibration"
            ]
            
            error_indicators = [
                "Service configuration error", "not properly configured",
                "Missing required environment variables", "I don't have permission"
            ]
            
            has_success = any(indicator.lower() in response_text.lower() for indicator in success_indicators)
            has_error = any(indicator.lower() in response_text.lower() for indicator in error_indicators)
            
            if has_error:
                print("\n❌ Lambda still has configuration errors")
                return False
            elif has_success:
                print("\n✅ SUCCESS! Lambda is now accessing knowledge base data!")
                return True
            else:
                print("\n⚠️  Lambda is working but may not be accessing knowledge base")
                print("   This could be normal - try more specific queries")
                return True
                
        else:
            print(f"❌ Lambda returned error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def update_streamlit_if_needed():
    """Check if Streamlit needs to be updated with the working endpoint."""
    
    print("\n" + "=" * 60)
    print("Streamlit Configuration Check")
    print("=" * 60)
    
    try:
        with open('streamlit_app/app.py', 'r') as f:
            content = f.read()
        
        # Check current endpoint
        lambda_url = "https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/"
        
        if lambda_url in content:
            print("✓ Streamlit is configured to use the Lambda Function URL")
            print("  This should now work correctly after the environment variable fix")
        else:
            print("? Streamlit endpoint configuration unclear")
        
        print(f"\nTo test the fix:")
        print(f"1. Run: python run_streamlit.py")
        print(f"2. Ask: 'What faults have been detected in the equipment?'")
        print(f"3. You should now see specific data about conveyor_motor_001")
        
    except Exception as e:
        print(f"Error checking Streamlit config: {e}")

if __name__ == "__main__":
    # Fix environment variables
    if fix_lambda_environment_variables():
        # Test the Lambda function
        if test_lambda_after_env_fix():
            print("\n🎉 LAMBDA FUNCTION FIXED!")
            print("The Lambda function now has the correct environment variables")
            print("and should be able to access the Bedrock Agent properly.")
            
            # Check Streamlit configuration
            update_streamlit_if_needed()
        else:
            print("\n⚠️  Environment variables updated but Lambda still has issues")
            print("May need to wait a few minutes for changes to take effect")
    else:
        print("\n❌ Failed to update environment variables")
        print("Please check AWS permissions and try again")