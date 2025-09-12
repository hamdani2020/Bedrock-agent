#!/usr/bin/env python3
"""
Run the Streamlit application locally for testing
"""

import subprocess
import sys
import os

def install_requirements():
    """Install Streamlit requirements"""
    print("📦 Installing Streamlit requirements...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "streamlit_app/requirements.txt"
        ])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def run_streamlit():
    """Run the Streamlit application"""
    print("🚀 Starting Streamlit application...")
    
    try:
        # Change to streamlit_app directory
        os.chdir("streamlit_app")
        
        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Streamlit application stopped")
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")

def main():
    """Main function"""
    print("🔧 Maintenance Agent Streamlit App\n")
    
    # Install requirements
    if install_requirements():
        print("\n" + "="*50)
        print("🌐 Starting Streamlit app at http://localhost:8501")
        print("Press Ctrl+C to stop the application")
        print("="*50 + "\n")
        
        # Run Streamlit
        run_streamlit()
    else:
        print("❌ Cannot start application due to installation errors")

if __name__ == "__main__":
    main()