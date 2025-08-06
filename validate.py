#!/usr/bin/env python3
"""
Validation script for Indian Court Data Fetcher
Checks if all dependencies are installed and basic functionality works
"""

import sys
import os
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_limiter',
        'selenium',
        'webdriver_manager',
        'requests',
        'langchain',
        'langchain_groq',
        'groq',
        'reportlab',
        'PIL',
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_environment_variables():
    """Check if environment variables are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    env_vars = {
        'GROQ_API_KEY': 'Required for AI summaries',
        'FLASK_SECRET_KEY': 'Required for Flask sessions'
    }
    
    issues = []
    
    for var, description in env_vars.items():
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} is not set - {description}")
            issues.append(var)
    
    return len(issues) == 0, issues

def check_file_structure():
    """Check if all required files are present"""
    required_files = [
        'app.py',
        'models.py',
        'scraper.py',
        'summarizer_langchain.py',
        'requirements.txt',
        'README.md',
        'LICENSE',
        '.gitignore',
        'templates/form.html',
        'templates/result.html',
        'templates/history.html',
        'static/style.css'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} is missing")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def test_basic_imports():
    """Test if basic application imports work"""
    try:
        from app import app
        print("✅ Flask app imports successfully")
        
        from models import db, CourtCase
        print("✅ Database models import successfully")
        
        from scraper import IndianCourtScraper
        print("✅ Scraper imports successfully")
        
        from summarizer_langchain import CourtDataSummarizer
        print("✅ Summarizer imports successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def main():
    """Run all validation checks"""
    print("🔍 Validating Indian Court Data Fetcher Setup\n")
    
    all_good = True
    
    # Check Python version
    print("1. Checking Python version...")
    if not check_python_version():
        all_good = False
    print()
    
    # Check dependencies
    print("2. Checking dependencies...")
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        print(f"Missing packages: {', '.join(missing_deps)}")
        print("Run: pip install -r requirements.txt")
        all_good = False
    print()
    
    # Check environment variables
    print("3. Checking environment variables...")
    env_ok, missing_env = check_environment_variables()
    if not env_ok:
        print("Copy .env.example to .env and set required values")
    print()
    
    # Check file structure
    print("4. Checking file structure...")
    files_ok, missing_files = check_file_structure()
    if not files_ok:
        print(f"Missing files: {', '.join(missing_files)}")
        all_good = False
    print()
    
    # Test imports
    if all_good:
        print("5. Testing basic imports...")
        if not test_basic_imports():
            all_good = False
        print()
    
    # Final result
    if all_good:
        print("🎉 All checks passed! The application is ready to run.")
        print("Start the application with: python run.py")
    else:
        print("❌ Some issues found. Please fix them before running the application.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
