#!/usr/bin/env python3
"""
Simple deployment script for Bedrock Agent infrastructure.
This script provides basic deployment utilities for AWS resources.
"""
import json
import boto3
import zipfile
import os
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load AWS configuration from config file."""
    with open('config/aws_config.json', 'r') as f:
        return json.load(f)

def create_lambda_deployment_package(function_path: str) -> str:
    """Create deployment package for Lambda function."""
    zip_path = f"{function_path}/deployment.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add Lambda function code
        lambda_file = f"{function_path}/lambda_function.py"
        if os.path.exists(lambda_file):
            zipf.write(lambda_file, 'lambda_function.py')
        
        # Add requirements if they exist
        req_file = f"{function_path}/requirements.txt"
        if os.path.exists(req_file):
            zipf.write(req_file, 'requirements.txt')
    
    return zip_path

def deploy_lambda_function(function_name: str, function_config: Dict[str, Any]) -> str:
    """Deploy Lambda function with Function URL."""
    lambda_client = boto3.client('lambda')
    
    # Create deployment package
    function_path = f"lambda_functions/{function_name}"
    zip_path = create_lambda_deployment_package(function_path)
    
    try:
        # Read deployment package
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Create or update Lambda function
        try:
            response = lambda_client.create_function(
                FunctionName=function_config['function_name'],
                Runtime=function_config['runtime'],
                Role=f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:role/{function_config.get('role', 'lambda-execution-role')}",
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_content},
                Timeout=function_config['timeout'],
                MemorySize=function_config['memory_size'],
                Environment={'Variables': function_config.get('environment_variables', {})}
            )
            print(f"Created Lambda function: {function_config['function_name']}")
        except lambda_client.exceptions.ResourceConflictException:
            # Function exists, update it
            response = lambda_client.update_function_code(
                FunctionName=function_config['function_name'],
                ZipFile=zip_content
            )
            print(f"Updated Lambda function: {function_config['function_name']}")
        
        # Create Function URL if configured
        if 'function_url' in function_config:
            try:
                url_response = lambda_client.create_function_url_config(
                    FunctionName=function_config['function_name'],
                    AuthType=function_config['function_url']['auth_type'],
                    Cors=function_config['function_url']['cors']
                )
                print(f"Created Function URL: {url_response['FunctionUrl']}")
                return url_response['FunctionUrl']
            except lambda_client.exceptions.ResourceConflictException:
                # Function URL exists, get it
                url_response = lambda_client.get_function_url_config(
                    FunctionName=function_config['function_name']
                )
                print(f"Function URL exists: {url_response['FunctionUrl']}")
                return url_response['FunctionUrl']
        
        return response['FunctionArn']
        
    finally:
        # Clean up deployment package
        if os.path.exists(zip_path):
            os.remove(zip_path)

def main():
    """Main deployment function."""
    print("Bedrock Agent Deployment Script")
    print("===============================")
    
    config = load_config()
    
    print("\nNote: This is a basic deployment script template.")
    print("Actual deployment will be implemented in later tasks.")
    print("\nLambda functions configured:")
    
    for func_name, func_config in config['lambda_functions'].items():
        print(f"  - {func_name}: {func_config['function_name']}")
    
    print(f"\nProject: {config['project_name']}")
    print(f"Region: {config['region']}")
    
    # TODO: Implement actual deployment logic in later tasks
    print("\nDeployment logic will be implemented when AWS resources are created.")

if __name__ == "__main__":
    main()