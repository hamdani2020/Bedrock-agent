#!/usr/bin/env python3
"""
Deploy Streamlit app with multiple deployment options.
"""
import os
import subprocess
import sys

def deploy_to_streamlit_cloud():
    """Instructions for Streamlit Cloud deployment."""
    print("🚀 Streamlit Cloud Deployment")
    print("=" * 40)
    print("\n1. Push your code to GitHub:")
    print("   git init")
    print("   git add .")
    print("   git commit -m 'Initial commit'")
    print("   git remote add origin <your-github-repo-url>")
    print("   git push -u origin main")
    
    print("\n2. Go to https://share.streamlit.io")
    print("3. Connect your GitHub repository")
    print("4. Set main file path: streamlit_app/app.py")
    print("5. Deploy!")
    
    print("\n✅ Streamlit Cloud is FREE and easiest option")

def create_heroku_files():
    """Create files needed for Heroku deployment."""
    
    # Create Procfile
    with open("/home/user/Downloads/test/Procfile", "w") as f:
        f.write("web: streamlit run streamlit_app/app.py --server.port=$PORT --server.address=0.0.0.0\n")
    
    # Create runtime.txt
    with open("/home/user/Downloads/test/runtime.txt", "w") as f:
        f.write("python-3.11.0\n")
    
    # Create requirements.txt for root
    with open("/home/user/Downloads/test/requirements_heroku.txt", "w") as f:
        f.write("streamlit>=1.28.0\nrequests>=2.31.0\n")
    
    print("✅ Created Heroku deployment files:")
    print("  - Procfile")
    print("  - runtime.txt") 
    print("  - requirements_heroku.txt")

def deploy_to_heroku():
    """Instructions for Heroku deployment."""
    print("\n🚀 Heroku Deployment")
    print("=" * 30)
    
    create_heroku_files()
    
    print("\n1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli")
    print("2. Login: heroku login")
    print("3. Create app: heroku create your-app-name")
    print("4. Deploy:")
    print("   git add .")
    print("   git commit -m 'Deploy to Heroku'")
    print("   git push heroku main")
    
    print("\n✅ Heroku provides custom domains and scaling")

def run_locally():
    """Run Streamlit app locally."""
    print("\n🏠 Running Locally")
    print("=" * 25)
    
    try:
        os.chdir("/home/user/Downloads/test/streamlit_app")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Error running Streamlit")
        print("Install streamlit: pip install streamlit")
    except KeyboardInterrupt:
        print("\n✅ Streamlit stopped")

def main():
    """Main deployment menu."""
    print("🚀 Streamlit Deployment Options")
    print("=" * 35)
    print("\n1. Streamlit Cloud (Recommended - FREE)")
    print("2. Heroku (Production)")
    print("3. Run Locally (Testing)")
    print("4. Exit")
    
    choice = input("\nChoose deployment option (1-4): ").strip()
    
    if choice == "1":
        deploy_to_streamlit_cloud()
    elif choice == "2":
        deploy_to_heroku()
    elif choice == "3":
        run_locally()
    elif choice == "4":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()