#!/usr/bin/env python3
"""
Test Lambda function directly using boto3
"""

import boto3
import json

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def test_lambda_direct():
    """Test Lambda function directly"""
    config = load_config()
    if not config:
        return False
    
    try:
        lambda_client = boto3.client('lambda', region_name=config['region'])
        
        function_name = config['lambda_functions']['query_handler']['function_name']
        
        print(f"🧪 Testing Lambda function directly: {function_name}")
        
        # Test payload
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'query': 'What is the current status of the industrial conveyor?',
                'sessionId': 'test-session-123'
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        print(f"   Sending test event...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"   Status Code: {response_payload.get('statusCode', 'Unknown')}")
        
        if response_payload.get('statusCode') == 200:
            body = json.loads(response_payload.get('body', '{}'))
            print(f"✅ Lambda test successful!")
            print(f"   Response: {body.get('response', 'No response')[:200]}...")
            return True
        else:
            print(f"❌ Lambda test failed")
            print(f"   Response: {response_payload}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def check_lambda_logs():
    """Check recent Lambda logs"""
    config = load_config()
    if not config:
        return
    
    try:
        logs_client = boto3.client('logs', region_name=config['region'])
        
        function_name = config['lambda_functions']['query_handler']['function_name']
        log_group_name = f"/aws/lambda/{function_name}"
        
        print(f"\n📋 Checking recent logs for: {log_group_name}")
        
        # Get recent log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if response['logStreams']:
            latest_stream = response['logStreams'][0]
            stream_name = latest_stream['logStreamName']
            
            print(f"   Latest log stream: {stream_name}")
            
            # Get recent log events
            events_response = logs_client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=stream_name,
                limit=10
            )
            
            events = events_response.get('events', [])
            if events:
                print(f"   Recent log events:")
                for event in events[-5:]:  # Show last 5 events
                    message = event['message'].strip()
                    print(f"     {message}")
            else:
                print(f"   No recent log events found")
        else:
            print(f"   No log streams found")
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

def main():
    """Main function"""
    print("🔍 Testing Lambda function directly...\n")
    
    success = test_lambda_direct()
    
    if not success:
        check_lambda_logs()
    
    print("\n" + "="*50)
    print("✅ Direct Lambda test complete!")

if __name__ == "__main__":
    main()