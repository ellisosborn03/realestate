#!/usr/bin/env python3
"""
Real Estate Distress Analysis System
Simplified entry point for running the application
"""

import sys
import os

# Add the core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# Import and run the main application
if __name__ == '__main__':
    from app import app
    try:
        print("🏠 Starting Real Estate Distress Analysis System...")
        print("📍 Access at: http://127.0.0.1:5001")
        print("📊 Dashboard at: http://127.0.0.1:5001/distress-dashboard")
        app.run(host='127.0.0.1', port=5001, debug=True)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
