#!/usr/bin/env python3
"""
Indian Court Data Fetcher - Run Script
Simple script to start the Flask application
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the Flask app
from app import app

if __name__ == '__main__':
    # Check if required environment variables are set
    if not os.getenv('GROQ_API_KEY'):
        print("Warning: GROQ_API_KEY not set. AI summaries will not work.")
        print("Please set your Groq API key in the .env file.")
    
    if not os.getenv('FLASK_SECRET_KEY'):
        print("Warning: FLASK_SECRET_KEY not set. Using default key.")
    
    # Run the application
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting Indian Court Data Fetcher on port {port}")
    print(f"Debug mode: {debug_mode}")
    print(f"Access the application at: http://localhost:{port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )
