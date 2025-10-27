#!/usr/bin/env python3
"""
Local development runner for KaTek Real Estate Platform
This script sets up the environment and runs the Django development server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🏠 Starting KaTek Real Estate Platform (Local Development)")
    print("=" * 60)
    
    # Set development environment
    os.environ['DEBUG'] = 'True'
    os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1'
    
    # Check if we're in the right directory
    if not Path('manage.py').exists():
        print("❌ Error: manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment not detected. Consider using a virtual environment.")
    
    try:
        print("🔍 Running system checks...")
        subprocess.run([sys.executable, 'manage.py', 'check'], check=True)
        
        print("🗄️ Running migrations...")
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        
        print("🚀 Starting development server...")
        print("📱 Open your browser to: http://127.0.0.1:8000")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the development server
        subprocess.run([sys.executable, 'manage.py', 'runserver'], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Django commands: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
        sys.exit(0)

if __name__ == '__main__':
    main()
