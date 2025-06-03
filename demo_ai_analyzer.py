#!/usr/bin/env python3

import sys
import os
sys.path.append('analysis')

from ai_distress_analyzer import AIDistressAnalyzer

class DemoAIDistressAnalyzer(AIDistressAnalyzer):
    """Demo version that uses sample AI responses to show full functionality"""
    
    def analyze_with_chatgpt(self, formatted_data):
        """Demo version that returns sample AI analysis"""
        
        print("🤖 Sending data to ChatGPT for analysis...")
        print("📊 [DEMO MODE] Using sample BEST REAL ESTATE AGENT responses...")
        
        # Enhanced sample AI responses based on comprehensive distress framework
        if "$1,161,804" in formatted_data:
            # High-value oceanfront condo
            return {
                "distress_score": 52,
                "confidence_level": 83,
                "valuation_discount": "12-18%",
                "explanation": "MODERATE-HIGH distress driven by Environmental & Structural Risk factors: Ocean Proximity + FL SB-4D regulations create emotional burnout from potential special assessments and re-certification requirements in post-Surfside environment. Building Age considerations and Condition & Market signals from absentee ownership patterns compound urgency. Strong investment opportunity due to regulatory fear exceeding actual financial impact."
            }
        elif "$802,326" in formatted_data:
            # Mid-high value Lake Worth property  
            return {
                "distress_score": 68,
                "confidence_level": 85,
                "valuation_discount": "15-22%", 
                "explanation": "HIGH distress across multiple categories: Demographics & Life Events suggest potential elderly ownership (>75) triggering downsizing urgency, while Condition & Market Signals show extended days on market and low absorption rate deflating seller morale. Financial Distress likely from deferred maintenance and mounting carrying costs. Excellent acquisition opportunity with motivated seller requiring quick disposition."
            }
        elif "$1,750,250" in formatted_data:
            # High-value Fort Lauderdale townhouse
            return {
                "distress_score": 43,
                "confidence_level": 87,
                "valuation_discount": "8-14%",
                "explanation": "MODERATE distress primarily from Condition & Market Signals: Absentee ownership creates disconnection and reduced motivation to maximize value, while townhouse format may indicate incomplete construction or stalled progress leading to owner burnout. Strong Fort Lauderdale market fundamentals limit severe distress, but emotional fatigue from property management creates negotiation leverage for experienced investors."
            }
        else:
            # Default response with framework references
            return {
                "distress_score": 58,
                "confidence_level": 78,
                "valuation_discount": "12-18%",
                "explanation": "MODERATE-HIGH distress indicated by multiple framework factors including Financial Distress signals from tax burden assessment ratios and potential Condition & Market indicators from extended market exposure. Demographics & Life Events may contribute through ownership transition stress. Solid investment opportunity requiring comprehensive due diligence on specific distress category prominence."
            }

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 demo_ai_analyzer.py \"STREET ADDRESS\" \"CITY, STATE ZIP\"")
        print("\nDemo Properties:")
        print("  python3 demo_ai_analyzer.py \"5103 NORTH OCEAN BLVD\" \"OCEAN RIDGE, FL 33435\"")
        print("  python3 demo_ai_analyzer.py \"6775 TURTLE POINT DR\" \"Lake Worth, FL 33467\"") 
        print("  python3 demo_ai_analyzer.py \"254 SHORE COURT\" \"FORT LAUDERDALE, FL 33308\"")
        return
    
    print("🎬 DEMO: AI-POWERED REAL ESTATE DISTRESS ANALYSIS")
    print("=" * 80)
    print("This demo shows the full AI analysis output using sample expert responses")
    print("=" * 80)
    
    analyzer = DemoAIDistressAnalyzer(openai_api_key="demo-key")
    result = analyzer.analyze_property(sys.argv[1], sys.argv[2])
    
    if result:
        print(f"\n💾 [DEMO] Analysis complete - would normally save to JSON file")
        print(f"🔗 In production, this runs with live ChatGPT-4o API")

if __name__ == "__main__":
    main() 