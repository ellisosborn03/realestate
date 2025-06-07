#!/usr/bin/env python3

import requests
import json
import time

def populate_sample_data():
    """Populate database with sample distress analysis data"""
    
    sample_properties = [
        {
            'address': '254 SHORE COURT, FORT LAUDERDALE, FL 33308',
            'distress_score': 100,
            'confidence': 95,
            'risk_factors': [
                "Active divorce proceedings",
                "Court-ordered sale timeline", 
                "Dual mortgage obligations",
                "High legal fee burden ($15k+)",
                "Child support obligations",
                "Spousal support orders",
                "Contested divorce case",
                "Extended case duration (18 months)",
                "High-value property (>$500k)",
                "Required equity split",
                "Buyer's market conditions",
                "Urgent sale deadline (90 days)"
            ],
            'analysis_type': 'divorce',
            'source_file': 'Divorce_Cases_03_2024_Sample.xlsx',
            'case_id': '502024DR004652XXXAMB',
            'party_name': 'JOHN SMITH'
        },
        {
            'address': '6775 TURTLE POINT DR, Lake Worth, FL 33467',
            'distress_score': 98,
            'confidence': 94,
            'risk_factors': [
                "Active divorce proceedings",
                "Court-ordered sale timeline",
                "Dual mortgage obligations", 
                "High legal fee burden ($15k+)",
                "Child support obligations",
                "Spousal support orders",
                "Contested divorce case",
                "Extended case duration (18 months)",
                "High-value property (>$500k)",
                "Required equity split",
                "Buyer's market conditions",
                "Seasonal timing challenges"
            ],
            'analysis_type': 'divorce',
            'source_file': 'Divorce_Cases_03_2024_Sample.xlsx',
            'case_id': '502024DR004653XXXAMB',
            'party_name': 'EDGAR ARDILA'
        },
        {
            'address': '5103 NORTH OCEAN BLVD, OCEAN RIDGE, FL 33435',
            'distress_score': 95,
            'confidence': 93,
            'risk_factors': [
                "Active divorce proceedings",
                "Court-ordered sale timeline",
                "Dual mortgage obligations",
                "High legal fee burden ($15k+)",
                "Child support obligations",
                "Spousal support orders",
                "Contested divorce case",
                "Extended case duration (18 months)",
                "High-value property (>$500k)",
                "Required equity split"
            ],
            'analysis_type': 'divorce',
            'source_file': 'Divorce_Cases_03_2024_Sample.xlsx',
            'case_id': '502024DR004634XXXASB',
            'party_name': 'JESSICA O\'BRIEN'
        },
        {
            'address': '123 PALM AVENUE, WEST PALM BEACH, FL 33401',
            'distress_score': 75,
            'confidence': 85,
            'risk_factors': [
                "Extended time on market (120 days)",
                "Multiple price reductions (3)",
                "Building >30 years old (Florida risk)",
                "Coastal insurance risk",
                "Poor market absorption (0.12)"
            ],
            'analysis_type': 'general',
            'source_file': 'General_Market_Analysis.xlsx',
            'case_id': None,
            'party_name': None
        },
        {
            'address': '5060 PALM HILL DR, WEST PALM BEACH, FL 33415',
            'distress_score': 88,
            'confidence': 89,
            'risk_factors': [
                "Active divorce proceedings",
                "Dual mortgage obligations",
                "Legal fee burden",
                "Child support obligations",
                "Contested divorce case",
                "Buyer's market conditions"
            ],
            'analysis_type': 'divorce',
            'source_file': 'Divorce_Cases_03_2024_Sample.xlsx',
            'case_id': '502024DR004636XXXAMB',
            'party_name': 'RODNEY PENA GOMEZ'
        },
        {
            'address': '789 SUNSET BOULEVARD, BOCA RATON, FL 33432',
            'distress_score': 62,
            'confidence': 78,
            'risk_factors': [
                "Building >30 years old (Florida risk)",
                "Coastal insurance risk",
                "High crime area",
                "Poor market absorption (0.14)"
            ],
            'analysis_type': 'general',
            'source_file': 'General_Market_Analysis.xlsx',
            'case_id': None,
            'party_name': None
        },
        {
            'address': '456 LAKE VIEW DRIVE, DELRAY BEACH, FL 33444',
            'distress_score': 45,
            'confidence': 72,
            'risk_factors': [
                "Building >30 years old (Florida risk)",
                "Recent sales decline"
            ],
            'analysis_type': 'general',
            'source_file': 'General_Market_Analysis.xlsx',
            'case_id': None,
            'party_name': None
        },
        {
            'address': '321 MARINA POINT, FORT LAUDERDALE, FL 33316',
            'distress_score': 28,
            'confidence': 65,
            'risk_factors': [
                "Coastal insurance risk"
            ],
            'analysis_type': 'general',
            'source_file': 'General_Market_Analysis.xlsx',
            'case_id': None,
            'party_name': None
        }
    ]
    
    base_url = 'http://localhost:5001'
    successful_saves = 0
    
    print("🚀 POPULATING DASHBOARD WITH SAMPLE DATA")
    print("=" * 60)
    
    for i, property_data in enumerate(sample_properties):
        print(f"\n[{i+1}/{len(sample_properties)}] Saving: {property_data['address']}")
        print(f"   Score: {property_data['distress_score']}/100 | Confidence: {property_data['confidence']}%")
        
        try:
            response = requests.post(f'{base_url}/api/save-analysis', json=property_data, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Saved successfully")
                successful_saves += 1
            else:
                print(f"   ❌ Save failed: {response.status_code}")
                print(f"      {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.2)  # Small delay
    
    print(f"\n📊 SUMMARY")
    print("=" * 30)
    print(f"✅ Successfully saved: {successful_saves}/{len(sample_properties)}")
    print(f"🌐 View dashboard at: {base_url}/distress-dashboard")
    
    if successful_saves > 0:
        print(f"\n🎯 SAMPLE DATA BREAKDOWN:")
        
        # Count by risk level
        risk_counts = {}
        for prop in sample_properties:
            level = prop['risk_level']
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        for level, count in risk_counts.items():
            emoji = {"CRITICAL": "🔴🚨", "HIGH": "🔴", "MEDIUM-HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(level, "⚪")
            print(f"   {emoji} {level}: {count} properties")
        
        # Total portfolio value
        total_value = sum(p['property_value'] for p in sample_properties)
        print(f"\n💰 Total Portfolio Value: ${total_value:,}")
        
        # High priority leads
        high_priority = [p for p in sample_properties if p['distress_score'] >= 85]
        print(f"🔥 High Priority Leads (85+): {len(high_priority)}")
        
        print(f"\n🔥 TOP LEADS:")
        sorted_props = sorted(sample_properties, key=lambda x: x['distress_score'], reverse=True)
        for i, prop in enumerate(sorted_props[:3]):
            value = prop['property_value']
            print(f"   {i+1}. {prop['address']}")
            print(f"      Score: {prop['distress_score']}/100 | Value: ${value:,}")

if __name__ == "__main__":
    populate_sample_data() 