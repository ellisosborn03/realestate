#!/usr/bin/env python3

import pandas as pd
from analysis.ai_scored_distress_detector_grok import GroqAIScoredDistressDetector
import os
from datetime import datetime

def process_excel():
    # Read the Excel file
    input_file = 'uploads/Divorce_Cases_2025_05_23_060122.xlsx.xlsx'
    df = pd.read_excel(input_file)
    
    # Show total properties and ask for confirmation
    total_properties = len(df)
    print(f"\n📊 Found {total_properties} properties in the Excel file.")
    
    while True:
        try:
            num_to_analyze = int(input(f"\nHow many properties would you like to analyze? (1-{total_properties}): "))
            if 1 <= num_to_analyze <= total_properties:
                break
            print(f"Please enter a number between 1 and {total_properties}")
        except ValueError:
            print("Please enter a valid number")
    
    # Confirm API usage
    print(f"\n⚠️  This will use {num_to_analyze} Groq API tokens.")
    confirm = input("Continue? (y/n): ").lower()
    if confirm != 'y':
        print("Analysis cancelled.")
        return
    
    # Initialize the detector
    detector = GroqAIScoredDistressDetector()
    
    # Process each row
    results = []
    for index, row in df.head(num_to_analyze).iterrows():
        try:
            # Assuming columns are named 'Street', 'City', 'State', 'ZIP'
            address1 = f"{row['Street Address']}"
            address2 = f"{row['City']}, {row['State']} {row['Zip Code']}"
            
            print(f"\nProcessing {index + 1}/{num_to_analyze}: {address1}, {address2}")
            
            # Get analysis
            result = detector.analyze_property(address1, address2)
            
            # Add to results
            results.append({
                'Address': f"{address1}, {address2}",
                'Distress_Score': result['ai_analysis']['score'],
                'Confidence': result['ai_analysis']['conf'],
                'Discount_Range': result['ai_analysis']['discount'],
                'Reasoning': result['ai_analysis']['reason']
            })
            
        except Exception as e:
            print(f"Error processing row {index + 1}: {e}")
            results.append({
                'Address': f"{address1}, {address2}",
                'Distress_Score': 'Error',
                'Confidence': 'Error',
                'Discount_Range': 'Error',
                'Reasoning': str(e)
            })
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Save to Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'groq_analysis_results_{timestamp}.xlsx'
    results_df.to_excel(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    process_excel() 