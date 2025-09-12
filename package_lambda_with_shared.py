#!/usr/bin/env python3
"""
Helper script to package Lambda functions with shared utilities.
Creates deployment packages that include the shared S3 utilities.
"""
import os
import shutil
import zipfile
from pathlib import Path

def package_lambda_function(function_name: str, output_dir: str = "dist") -> str:
    """
    Package a Lambda function with shared utilities.
    
    Args:
        function_name: Name of the Lambda function directory
        output_dir: Output directory for the package
        
    Returns:
        Path to the created package
    """
    function_dir = Path(f"lambda_functions/{function_name}")
    shared_dir = Path("lambda_functions/shared")
    output_path = Path(output_dir)
    
    if not function_dir.exists():
        raise ValueError(f"Function directory not found: {function_dir}")
    
    if not shared_dir.exists():
        raise ValueError(f"Shared directory not found: {shared_dir}")
    
    # Create output directory
    output_path.mkdir(exist_ok=True)
    
    # Create temporary packaging directory
    temp_dir = output_path / f"temp_{function_name}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # Copy function files
        for file_path in function_dir.glob("*"):
            if file_path.is_file():
                shutil.copy2(file_path, temp_dir)
        
        # Copy shared utilities
        shared_temp = temp_dir / "shared"
        shutil.copytree(shared_dir, shared_temp)
        
        # Create zip package
        package_path = output_path / f"{function_name}.zip"
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Packaged {function_name} -> {package_path}")
        return str(package_path)
        
    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def main():
    """Package all Lambda functions with shared utilities."""
    print("=" * 50)
    print("Lambda Function Packaging")
    print("=" * 50)
    
    functions = ["data_sync", "health_check", "query_handler", "session_manager"]
    packages = []
    
    for function_name in functions:
        try:
            package_path = package_lambda_function(function_name)
            packages.append(package_path)
        except Exception as e:
            print(f"❌ Failed to package {function_name}: {str(e)}")
    
    print(f"\n📦 Created {len(packages)} packages:")
    for package in packages:
        print(f"   - {package}")
    
    print(f"\n📋 Deployment Notes:")
    print(f"   - Packages include shared S3 utilities")
    print(f"   - Upload these packages when deploying Lambda functions")
    print(f"   - Ensure IAM roles have S3 and Bedrock permissions")

if __name__ == "__main__":
    main()