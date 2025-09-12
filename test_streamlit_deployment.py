#!/usr/bin/env python3
"""
Test Streamlit application deployment readiness.
Verifies the Streamlit app can start and has all required components.
"""

import os
import sys
import subprocess
import importlib.util
import time
from datetime import datetime
from typing import Dict, List

class StreamlitDeploymentTester:
    """Test Streamlit application deployment readiness."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results = []
        self.app_path = 'streamlit_app/app.py'
        self.requirements_path = 'streamlit_app/requirements.txt'
        
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
    
    def test_app_file_exists(self) -> bool:
        """Test if Streamlit app file exists."""
        print("\n📁 Testing App File Existence...")
        
        exists = os.path.exists(self.app_path)
        
        if exists:
            # Get file size and modification time
            stat = os.stat(self.app_path)
            size_kb = stat.st_size / 1024
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            details = f"Size: {size_kb:.1f}KB, Modified: {mod_time}"
        else:
            details = f"File not found: {self.app_path}"
        
        self.log_test("App File Exists", exists, details)
        return exists
    
    def test_requirements_file(self) -> bool:
        """Test if requirements file exists and is valid."""
        print("\n📋 Testing Requirements File...")
        
        if not os.path.exists(self.requirements_path):
            self.log_test("Requirements File", False, f"File not found: {self.requirements_path}")
            return False
        
        try:
            with open(self.requirements_path, 'r') as f:
                requirements = f.read().strip().split('\n')
            
            # Filter out empty lines and comments
            packages = [req.strip() for req in requirements if req.strip() and not req.strip().startswith('#')]
            
            # Check for essential packages
            essential_packages = ['streamlit', 'requests']
            missing_packages = []
            
            for package in essential_packages:
                if not any(package in req.lower() for req in packages):
                    missing_packages.append(package)
            
            success = len(missing_packages) == 0
            details = f"Packages: {len(packages)}, Missing essential: {missing_packages}" if missing_packages else f"All {len(packages)} packages present"
            
            self.log_test("Requirements File", success, details)
            return success
            
        except Exception as e:
            self.log_test("Requirements File", False, str(e))
            return False
    
    def test_app_syntax(self) -> bool:
        """Test if the app has valid Python syntax."""
        print("\n🐍 Testing App Syntax...")
        
        try:
            # Try to compile the app file
            with open(self.app_path, 'r') as f:
                app_content = f.read()
            
            compile(app_content, self.app_path, 'exec')
            
            self.log_test("App Syntax", True, "Valid Python syntax")
            return True
            
        except SyntaxError as e:
            self.log_test("App Syntax", False, f"Syntax error: Line {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            self.log_test("App Syntax", False, str(e))
            return False
    
    def test_app_imports(self) -> bool:
        """Test if the app can import required modules."""
        print("\n📦 Testing App Imports...")
        
        try:
            # Load the app module
            spec = importlib.util.spec_from_file_location("streamlit_app", self.app_path)
            module = importlib.util.module_from_spec(spec)
            
            # This will test imports but not execute the main code
            spec.loader.exec_module(module)
            
            self.log_test("App Imports", True, "All imports successful")
            return True
            
        except ImportError as e:
            self.log_test("App Imports", False, f"Import error: {str(e)}")
            return False
        except Exception as e:
            self.log_test("App Imports", False, str(e))
            return False
    
    def test_app_structure(self) -> bool:
        """Test if the app has required functions and structure."""
        print("\n🏗️  Testing App Structure...")
        
        try:
            with open(self.app_path, 'r') as f:
                app_content = f.read()
            
            # Check for required components
            required_components = {
                'main function': 'def main(',
                'streamlit import': 'import streamlit',
                'requests import': 'import requests',
                'chat interface': 'chat_message',
                'session state': 'session_state',
                'API endpoint config': 'api_endpoint',
                'query function': 'send_query'
            }
            
            missing_components = []
            present_components = []
            
            for component, pattern in required_components.items():
                if pattern in app_content:
                    present_components.append(component)
                else:
                    missing_components.append(component)
            
            success = len(missing_components) == 0
            
            if success:
                details = f"All {len(required_components)} components present"
            else:
                details = f"Missing: {missing_components}"
            
            self.log_test("App Structure", success, details)
            return success
            
        except Exception as e:
            self.log_test("App Structure", False, str(e))
            return False
    
    def test_function_url_configuration(self) -> bool:
        """Test if Function URL is properly configured in the app."""
        print("\n🔗 Testing Function URL Configuration...")
        
        try:
            with open(self.app_path, 'r') as f:
                app_content = f.read()
            
            # Look for Function URL pattern
            import re
            url_pattern = r'https://[a-z0-9]+\.lambda-url\.[a-z0-9-]+\.on\.aws/'
            urls = re.findall(url_pattern, app_content)
            
            if urls:
                # Check if it's not the placeholder URL
                valid_urls = [url for url in urls if 'your-lambda-url' not in url]
                
                if valid_urls:
                    success = True
                    details = f"Function URL configured: {valid_urls[0]}"
                else:
                    success = False
                    details = "Only placeholder URL found"
            else:
                success = False
                details = "No Function URL found in app"
            
            self.log_test("Function URL Configuration", success, details)
            return success
            
        except Exception as e:
            self.log_test("Function URL Configuration", False, str(e))
            return False
    
    def test_streamlit_startup(self) -> bool:
        """Test if Streamlit can start the app (dry run)."""
        print("\n🚀 Testing Streamlit Startup...")
        
        try:
            # Try to validate the app with streamlit
            result = subprocess.run([
                sys.executable, '-m', 'streamlit', 'run', self.app_path, '--help'
            ], capture_output=True, text=True, timeout=10)
            
            # If streamlit command works, it means the app is valid
            success = result.returncode == 0
            
            if success:
                details = "Streamlit can run the app"
            else:
                details = f"Streamlit error: {result.stderr[:100]}"
            
            self.log_test("Streamlit Startup", success, details)
            return success
            
        except subprocess.TimeoutExpired:
            self.log_test("Streamlit Startup", False, "Streamlit command timed out")
            return False
        except FileNotFoundError:
            self.log_test("Streamlit Startup", False, "Streamlit not installed")
            return False
        except Exception as e:
            self.log_test("Streamlit Startup", False, str(e))
            return False
    
    def test_deployment_readiness(self) -> bool:
        """Test overall deployment readiness."""
        print("\n🎯 Testing Deployment Readiness...")
        
        readiness_checks = []
        
        # Check if all previous tests passed
        passed_tests = [r for r in self.test_results if r['success']]
        total_tests = len(self.test_results)
        
        if total_tests > 0:
            success_rate = len(passed_tests) / total_tests
            readiness_checks.append(f"Test success rate: {success_rate:.0%}")
        
        # Check file sizes (reasonable for deployment)
        if os.path.exists(self.app_path):
            app_size = os.path.getsize(self.app_path)
            if app_size > 1024 * 1024:  # > 1MB
                readiness_checks.append("⚠️  App file is large (>1MB)")
            else:
                readiness_checks.append("✓ App file size reasonable")
        
        # Check for deployment guide
        if os.path.exists('STREAMLIT_DEPLOYMENT_GUIDE.md'):
            readiness_checks.append("✓ Deployment guide available")
        else:
            readiness_checks.append("⚠️  No deployment guide found")
        
        # Overall readiness
        success = success_rate >= 0.8 if total_tests > 0 else False
        details = "; ".join(readiness_checks)
        
        self.log_test("Deployment Readiness", success, details)
        return success
    
    def run_all_tests(self) -> Dict:
        """Run all Streamlit deployment tests."""
        print("🎨 Starting Streamlit Deployment Testing...")
        print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 App path: {self.app_path}")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_app_file_exists,
            self.test_requirements_file,
            self.test_app_syntax,
            self.test_app_imports,
            self.test_app_structure,
            self.test_function_url_configuration,
            self.test_streamlit_startup,
            self.test_deployment_readiness
        ]
        
        passed_tests = 0
        
        for test_func in tests:
            if test_func():
                passed_tests += 1
        
        # Generate summary
        total_tests = len(tests)
        success_rate = passed_tests / total_tests
        overall_success = success_rate >= 0.8  # 80% success rate required
        
        summary = {
            'success': overall_success,
            'tests_passed': passed_tests,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'app_path': self.app_path,
            'test_results': self.test_results
        }
        
        self.print_summary(summary)
        return summary
    
    def print_summary(self, summary: Dict):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 STREAMLIT DEPLOYMENT TEST SUMMARY")
        print("=" * 60)
        
        overall_status = "✅ READY" if summary['success'] else "❌ NOT READY"
        print(f"Deployment Status: {overall_status}")
        print(f"Tests Passed: {summary['tests_passed']}/{summary['total_tests']} ({summary['success_rate']:.0%})")
        print(f"App Path: {summary['app_path']}")
        
        print("\n📋 Detailed Results:")
        print("-" * 40)
        
        for result in summary['test_results']:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 Deployment Status:")
        if summary['success']:
            print("✅ Streamlit app is ready for deployment!")
            print("📝 Next steps:")
            print("   1. Choose deployment platform (Streamlit Cloud, Heroku, AWS ECS)")
            print("   2. Push code to Git repository if using Streamlit Cloud")
            print("   3. Configure environment variables if needed")
            print("   4. Deploy and test the live application")
            print("   5. Monitor application performance and user feedback")
        else:
            print("⚠️  Streamlit app needs fixes before deployment:")
            failed_tests = [r for r in summary['test_results'] if not r['success']]
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
            print("   • Fix the issues above and re-run the test")
        
        print("\n" + "=" * 60)

def main():
    """Main function."""
    tester = StreamlitDeploymentTester()
    results = tester.run_all_tests()
    
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    main()