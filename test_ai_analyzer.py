#!/usr/bin/env python3

import os
import sys

# Add analysis directory to path
sys.path.append('analysis')

from ai_distress_analyzer import AIDistressAnalyzer

def test_ai_analyzer():
    """Test the AI-powered distress analyzer with sample properties"""
    
    print("🧪 TESTING AI-POWERED DISTRESS ANALYZER")
    print("=" * 60)
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("\nOr run with: python test_ai_analyzer.py --api-key YOUR_KEY")
        return
    
    analyzer = AIDistressAnalyzer()
    
    # Test properties with different risk profiles
    test_properties = [
        {
            'address1': '920 POPLAR DRIVE',
            'address2': 'LAKE PARK, FL 33403',
            'expected_risk': 'LOW'
        },
        {
            'address1': '4520 PGA BLVD',
            'address2': 'PALM BEACH GARDENS, FL 33418', 
            'expected_risk': 'MEDIUM-HIGH'
        }
    ]
    
    for i, prop in enumerate(test_properties, 1):
        print(f"\n🏠 TEST PROPERTY #{i}")
        print("-" * 40)
        
        result = analyzer.analyze_property(
            prop['address1'], 
            prop['address2']
        )
        
        if result:
            print(f"✅ Analysis completed for {prop['address1']}, {prop['address2']}")
            print(f"   Expected Risk: {prop['expected_risk']}")
        else:
            print(f"❌ Analysis failed for {prop['address1']}, {prop['address2']}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("AI Distress Analyzer Test Script")
        print("\nUsage:")
        print("  python test_ai_analyzer.py")
        print("  export OPENAI_API_KEY='your-key-here' && python test_ai_analyzer.py")
        print("\nOr analyze a specific property:")
        print("  python analysis/ai_distress_analyzer.py \"123 MAIN ST\" \"CITY, FL 12345\"")
    else:
        test_ai_analyzer() 