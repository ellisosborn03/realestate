#!/usr/bin/env python3
"""
Real Estate Distress Analysis System
Simplified entry point for running the application
"""

import os
import sys

# Add core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# Kill any existing processes on port 5001
os.system("lsof -ti :5001 | xargs kill -9 2>/dev/null")

print("🚀 Starting Real Estate Distress Analysis System...")
print("📊 Access your dashboard at: http://127.0.0.1:5001")
print("📈 Distress dashboard at: http://127.0.0.1:5001/distress-dashboard")
print("-" * 60)

from app import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
