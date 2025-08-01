#!/usr/bin/env python3
"""
Test Artifact Generator Startup Script
Checks dependencies and starts the Flask application
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependency(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - Not installed")
        return False

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tesseract OCR")
            return True
        else:
            print("❌ Tesseract OCR - Not found")
            return False
    except FileNotFoundError:
        print("❌ Tesseract OCR - Not installed")
        return False

def check_env_file():
    """Check if .env file exists"""
    if os.path.exists('.env'):
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("   Please copy env_example.txt to .env and add your OpenAI API key")
        return False

def install_dependencies():
    """Install missing dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Test Artifact Generator Startup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    print("\n📋 Checking dependencies...")
    dependencies = [
        ('flask', 'flask'),
        ('openai', 'openai'),
        ('pillow', 'PIL'),
        ('pytesseract', 'pytesseract'),
        ('PyPDF2', 'PyPDF2'),
        ('python-docx', 'docx'),
        ('reportlab', 'reportlab'),
        ('flask-cors', 'flask_cors'),
        ('python-dotenv', 'dotenv'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('jinja2', 'jinja2'),
        ('werkzeug', 'werkzeug'),
        ('requests', 'requests'),
        ('beautifulsoup4', 'bs4'),
        ('lxml', 'lxml'),
        ('markdown', 'markdown')
    ]
    
    missing_deps = []
    for package, import_name in dependencies:
        if not check_dependency(package, import_name):
            missing_deps.append(package)
    
    # Check Tesseract
    check_tesseract()
    
    # Check environment file
    check_env_file()
    
    # Install missing dependencies if any
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        response = input("Would you like to install missing dependencies? (y/n): ")
        if response.lower() in ['y', 'yes']:
            if not install_dependencies():
                sys.exit(1)
        else:
            print("Please install missing dependencies manually:")
            print("pip install -r requirements.txt")
            sys.exit(1)
    
    # Check OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("\n⚠️  OpenAI API key not configured")
        print("   Please add your OpenAI API key to the .env file")
        print("   Get your API key from: https://platform.openai.com/api-keys")
        response = input("Continue anyway? (y/n): ")
        if response.lower() not in ['y', 'yes']:
            sys.exit(1)
    else:
        print("✅ OpenAI API key configured")
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    print("✅ Directories created")
    
    # Start the application
    print("\n🌐 Starting Test Artifact Generator...")
    print("   Open your browser and go to: http://localhost:5000")
    print("   Press Ctrl+C to stop the server")
    print("=" * 40)
    
    try:
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 