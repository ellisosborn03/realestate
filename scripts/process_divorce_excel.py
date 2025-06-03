#!/usr/bin/env python3

import pandas as pd
import sys
import os
from divorce_lead_analyzer import DivorceLeadAnalyzer
import time
import json

def clean_address(street, city, state, zip_code):
    """Combine address components into a clean full address"""
    if pd.isna(street) or str(street).strip() == "":
        return None
    
    # Clean up components
    street = str(street).strip()
    city = str(city).strip() if not pd.isna(city) else ""
    state = str(state).strip() if not pd.isna(state) else "FL"  # Default to FL
    zip_code = str(zip_code).strip() if not pd.isna(zip_code) else ""
    
    # Remove suite/unit info for better ATTOM matching
    street = street.split(" SUITE")[0].split(" UNIT")[0].split(" APT")[0].split(" #")[0]
    
    # Build full address
    if city and state:
        if zip_code and zip_code != "nan":
            return f"{street}, {city}, {state} {zip_code}"
        else:
            return f"{street}, {city}, {state}"
    else:
        return f"{street}, FL"  # Default fallback

def analyze_divorce_party_data(df):
    """Extract additional insights from divorce party data"""
    party_insights = {}
    
    # Count parties per case
    case_party_counts = df.groupby('Case ID')['Party Seq No'].count()
    avg_parties = case_party_counts.mean()
    
    # Analyze case complexity
    complex_cases = case_party_counts[case_party_counts > 2].count()
    total_cases = len(case_party_counts)
    
    party_insights = {
        "total_cases": total_cases,
        "total_parties": len(df),
        "avg_parties_per_case": avg_parties,
        "complex_cases_pct": (complex_cases / total_cases) * 100 if total_cases > 0 else 0,
        "cases_with_attorneys": df[df['Atty For'].notna()]['Case ID'].nunique(),
    }
    
    return party_insights

def process_divorce_excel_file(file_path, max_properties=10, start_from=0):
    """Process divorce Excel file and analyze properties"""
    
    print(f"📊 PROCESSING DIVORCE EXCEL: {file_path}")
    print("=" * 80)
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        print(f"✅ Loaded {len(df)} divorce party records")
        
        # Get party insights
        insights = analyze_divorce_party_data(df)
        print(f"📋 {insights['total_cases']} unique divorce cases")
        print(f"📋 {insights['avg_parties_per_case']:.1f} average parties per case")
        print(f"📋 {insights['complex_cases_pct']:.1f}% complex cases (>2 parties)")
        print(f"⚖️  {insights['cases_with_attorneys']} cases with attorney representation")
        
        # Create full addresses
        df['Full_Address'] = df.apply(
            lambda row: clean_address(
                row['Street Address'], 
                row['City'], 
                row['State'], 
                row['Zip Code']
            ), axis=1
        )
        
        # Filter out invalid addresses
        valid_addresses = df[df['Full_Address'].notna()]
        print(f"📍 {len(valid_addresses)} records with valid addresses")
        
        # Get unique properties (remove duplicates)
        unique_properties = valid_addresses.drop_duplicates(subset=['Full_Address'])
        print(f"🏠 {len(unique_properties)} unique properties found")
        
        # Apply limits
        if start_from > 0:
            unique_properties = unique_properties.iloc[start_from:]
            print(f"⏭️  Starting from property #{start_from + 1}")
            
        if max_properties > 0:
            unique_properties = unique_properties.head(max_properties)
            print(f"🎯 Analyzing top {len(unique_properties)} properties")
        
        # Initialize analyzer
        analyzer = DivorceLeadAnalyzer()
        
        results = []
        high_priority_leads = []
        total_potential_discount = 0
        
        print(f"\n🚀 STARTING DIVORCE PROPERTY ANALYSIS...")
        print("=" * 80)
        
        for idx, row in unique_properties.iterrows():
            address = row['Full_Address']
            case_id = row['Case ID']
            party_name = row['Party Name']
            
            print(f"\n[{len(results) + 1}/{len(unique_properties)}] Analyzing Case {case_id}")
            print(f"👤 Party: {party_name}")
            
            # Create case data from Excel row
            case_data = {
                "case_id": case_id,
                "case_type": "contested",  # Most divorce cases are contested
                "children": True,  # Conservative assumption
                "duration_months": 18,  # Average duration
                "has_attorney": not pd.isna(row.get('Atty For', None))
            }
            
            # Analyze the property
            result = analyzer.analyze_divorce_lead(address, case_data)
            
            if result.get("status") == "success":
                result["case_id"] = case_id
                result["party_name"] = party_name
                results.append(result)
                
                # Track high-priority leads
                if result.get("distress_score", 0) >= 70:
                    high_priority_leads.append(result)
                
                # Calculate potential discount value
                property_value = result.get("property_value", 0)
                discount_str = result.get("discount_potential", "0-0%")
                if property_value > 0 and discount_str != "0-0%":
                    try:
                        # Extract average discount percentage
                        percentages = [int(x.rstrip('%')) for x in discount_str.split('-')]
                        avg_discount_pct = sum(percentages) / 2
                        discount_value = property_value * (avg_discount_pct / 100)
                        total_potential_discount += discount_value
                    except:
                        pass
            
            # Rate limiting
            time.sleep(0.5)
        
        # Generate comprehensive report
        print(f"\n📋 DIVORCE LEAD ANALYSIS REPORT")
        print("=" * 80)
        print(f"📊 Total Properties Analyzed: {len(results)}")
        print(f"🎯 High-Priority Leads (Score ≥70): {len(high_priority_leads)}")
        print(f"💰 Total Potential Discount Value: ${total_potential_discount:,.0f}")
        
        if len(results) > 0:
            avg_score = sum(r.get("distress_score", 0) for r in results) / len(results)
            print(f"📈 Average Distress Score: {avg_score:.1f}/100")
        
        # Risk level breakdown
        risk_counts = {}
        for result in results:
            risk_level = result.get("risk_level", "UNKNOWN")
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        print(f"\n🎯 RISK LEVEL BREAKDOWN:")
        for level, count in risk_counts.items():
            emoji = {"CRITICAL": "🔴🚨", "HIGH": "🔴", "MEDIUM-HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(level, "⚪")
            percentage = (count / len(results)) * 100 if results else 0
            print(f"   {emoji} {level}: {count} ({percentage:.1f}%)")
        
        # Top priority leads details
        if high_priority_leads:
            print(f"\n🚨 TOP PRIORITY LEADS:")
            print("-" * 60)
            for i, lead in enumerate(sorted(high_priority_leads, key=lambda x: x.get("distress_score", 0), reverse=True)[:5]):
                score = lead.get("distress_score", 0)
                value = lead.get("property_value", 0)
                discount = lead.get("discount_potential", "N/A")
                case_id = lead.get("case_id", "N/A")
                
                print(f"{i+1}. Score: {score}/100 | Value: ${value:,} | Discount: {discount}")
                print(f"   Case: {case_id} | {lead['address']}")
                print()
        
        # Save results to JSON
        output_file = f"divorce_analysis_results_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "file_analyzed": file_path,
                "analysis_timestamp": time.time(),
                "summary": {
                    "total_analyzed": len(results),
                    "high_priority": len(high_priority_leads),
                    "avg_distress_score": avg_score if results else 0,
                    "total_discount_potential": total_potential_discount,
                    "risk_breakdown": risk_counts
                },
                "results": results
            }, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error processing Excel file: {e}")
        return []

def main():
    """Main function to process divorce Excel files"""
    
    # Check available files
    excel_files = [f for f in os.listdir('uploads') if f.endswith('.xlsx')]
    
    if not excel_files:
        print("❌ No Excel files found in uploads/ folder")
        print("💡 To upload files: copy your Excel files to the uploads/ folder")
        return
    
    print("📁 AVAILABLE DIVORCE EXCEL FILES:")
    for i, file in enumerate(excel_files):
        print(f"  {i+1}. {file}")
    
    # For testing, use the latest file
    latest_file = max(excel_files, key=lambda f: os.path.getmtime(f"uploads/{f}"))
    file_path = f"uploads/{latest_file}"
    
    print(f"\n🎯 Processing: {latest_file}")
    
    # Process with limits for testing
    results = process_divorce_excel_file(
        file_path=file_path,
        max_properties=5,  # Limit for testing
        start_from=0
    )
    
    print(f"\n✅ Analysis complete! Processed {len(results)} properties.")

if __name__ == "__main__":
    main() 