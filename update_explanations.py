#!/usr/bin/env python3

import sqlite3
import json
import sys
import os

# Add the current directory to Python path to import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_distress_explanation

def update_all_explanations():
    """Update all existing properties with new explanation format"""
    
    conn = sqlite3.connect('distress_analysis.db')
    cursor = conn.cursor()
    
    # Get all properties
    cursor.execute('''
        SELECT id, distress_score, discount_potential, risk_factors, property_value,
               case_id, party_name, source_file
        FROM properties
    ''')
    
    properties = cursor.fetchall()
    print(f"Found {len(properties)} properties to update...")
    
    updated_count = 0
    
    for prop in properties:
        prop_id, distress_score, discount_potential, risk_factors_json, property_value, case_id, party_name, source_file = prop
        
        # Parse risk factors
        try:
            risk_factors = json.loads(risk_factors_json) if risk_factors_json else []
        except:
            risk_factors = []
        
        # Create property data based on what we can infer
        property_data = {
            'current_value': property_value or 0,
            'days_on_market': 0,  # Not available in old data
            'tax_liens': 0,       # Not available in old data
            'year_built': 0,      # Not available in old data
            'court_deadline': 90, # Default from analysis - 90 day deadline
            'case_duration_months': 18  # Default from analysis - 18 months
        }
        
        # Generate new explanation
        new_explanation = generate_distress_explanation(
            distress_score, 
            discount_potential, 
            risk_factors, 
            property_data
        )
        
        # Update the database
        cursor.execute('''
            UPDATE properties 
            SET distress_explanation = ? 
            WHERE id = ?
        ''', (new_explanation, prop_id))
        
        updated_count += 1
        print(f"Updated {updated_count}/{len(properties)}: {case_id} - {party_name}")
        print(f"  New explanation: {new_explanation}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Successfully updated {updated_count} property explanations!")
    print("All properties now use the new concise explanation format.")

if __name__ == "__main__":
    update_all_explanations() 