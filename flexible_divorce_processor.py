#!/usr/bin/env python3

import pandas as pd
import sys
import os
from divorce_lead_analyzer import DivorceLeadAnalyzer
import time
import json
import re
import requests

def detect_excel_format(df):
    """Detect which Excel format we're dealing with"""
    columns = [col.lower() for col in df.columns]
    
    # Format 1: Standard format
    if 'case id' in columns and 'street address' in columns:
        return {
            "format": "standard",
            "case_id_col": "Case ID",
            "street_col": "Street Address", 
            "city_col": "City",
            "state_col": "State",
            "zip_col": "Zip Code",
            "party_name_col": "Party Name",
            "attorney_col": "Atty For"
        }
    
    # Format 2: Database export format
    elif 'cdbcase id' in columns and 'street address' in columns:
        return {
            "format": "database",
            "case_id_col": "cdbcase id",
            "street_col": "street address",
            "csz_col": "CSZ",  # City, State, Zip combined
            "first_name_col": "spriden first name",
            "last_name_col": "spriden last name",
            "filing_date_col": "cdbcase init filing",
            "party_type_col": "cdrcpty ptyp code"
        }
    
    else:
        return {"format": "unknown"}

def parse_csz(csz_string):
    """Parse City, State, Zip from combined string"""
    if pd.isna(csz_string):
        return "", "FL", ""
    
    csz = str(csz_string).strip()
    
    # Pattern: "CITY, STATE ZIP" or "CITY STATE ZIP"
    zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', csz)
    zip_code = zip_match.group(1) if zip_match else ""
    
    # Remove ZIP to get city/state
    csz_no_zip = re.sub(r'\b\d{5}(?:-\d{4})?\b', '', csz).strip().rstrip(',').strip()
    
    # Split by comma or last space for state
    if ',' in csz_no_zip:
        parts = csz_no_zip.split(',')
        city = parts[0].strip()
        state = parts[1].strip() if len(parts) > 1 else "FL"
    else:
        # Try to split by last two letters (state)
        words = csz_no_zip.split()
        if len(words) >= 2 and len(words[-1]) == 2:
            state = words[-1]
            city = " ".join(words[:-1])
        else:
            city = csz_no_zip
            state = "FL"
    
    return city, state, zip_code

def clean_address_flexible(street, city_state_zip_data, format_info):
    """Clean address based on detected format"""
    if pd.isna(street) or str(street).strip() == "":
        return None
    
    street = str(street).strip()
    
    # Remove suite/unit info for better ATTOM matching
    street = street.split(" SUITE")[0].split(" UNIT")[0].split(" APT")[0].split(" #")[0]
    
    if format_info["format"] == "standard":
        # Separate city, state, zip columns
        city = str(city_state_zip_data.get("city", "")).strip()
        state = str(city_state_zip_data.get("state", "FL")).strip()
        zip_code = str(city_state_zip_data.get("zip", "")).strip()
        
    elif format_info["format"] == "database":
        # Combined CSZ column
        csz = city_state_zip_data.get("csz", "")
        city, state, zip_code = parse_csz(csz)
    
    else:
        city, state, zip_code = "", "FL", ""
    
    # Build full address
    if city and state:
        if zip_code and zip_code != "nan":
            return f"{street}, {city}, {state} {zip_code}"
        else:
            return f"{street}, {city}, {state}"
    else:
        return f"{street}, FL"

def save_to_database(result, source_file):
    """Save analysis result to the Flask database"""
    try:
        # Extract property data from the analysis result
        property_data = {
            'current_value': result.get('property_value', 0),
            'days_on_market': result.get('days_on_market', 0),
            'tax_liens': result.get('tax_liens', 0),
            'year_built': result.get('year_built', 0),
            'court_deadline': result.get('court_deadline', 0),
            'case_duration': result.get('case_duration_months', 0)
        }
        
        data = {
            'address': result.get('address'),
            'distress_score': result.get('distress_score'),
            'risk_level': result.get('risk_level'),
            'discount_potential': result.get('discount_potential'),
            'property_value': result.get('property_value', 0),
            'confidence': result.get('confidence'),
            'risk_factors': result.get('risk_factors', []),
            'analysis_type': 'divorce',
            'source_file': source_file,
            'case_id': result.get('case_id'),
            'party_name': result.get('party_name'),
            # Pass property data for better explanations
            'days_on_market': property_data['days_on_market'],
            'tax_liens': property_data['tax_liens'],
            'year_built': property_data['year_built'],
            'court_deadline': property_data['court_deadline'],
            'case_duration_months': property_data['case_duration']
        }
        
        response = requests.post('http://localhost:5001/api/save-analysis', json=data, timeout=10)
        if response.status_code == 200:
            print(f"    ✅ Saved to database")
        else:
            print(f"    ❌ Database save failed: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Database save error: {e}")

def process_flexible_divorce_excel(file_path, max_properties=0):
    """Process divorce Excel with flexible format detection"""
    
    print(f"📊 PROCESSING DIVORCE EXCEL: {file_path}")
    print("=" * 80)
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        print(f"✅ Loaded {len(df)} records")
        
        # Detect format
        format_info = detect_excel_format(df)
        print(f"🔍 Detected format: {format_info['format']}")
        
        if format_info["format"] == "unknown":
            print("❌ Unknown Excel format. Columns found:")
            print(f"   {list(df.columns)}")
            return []
        
        # Process based on format
        if format_info["format"] == "standard":
            # Standard format processing
            df['Full_Address'] = df.apply(
                lambda row: clean_address_flexible(
                    row[format_info["street_col"]],
                    {
                        "city": row.get(format_info["city_col"], ""),
                        "state": row.get(format_info["state_col"], "FL"),
                        "zip": row.get(format_info["zip_col"], "")
                    },
                    format_info
                ), axis=1
            )
            
            df['Party_Name'] = df.get(format_info["party_name_col"], "Unknown")
            df['Case_ID'] = df[format_info["case_id_col"]]
            df['Has_Attorney'] = df.get(format_info["attorney_col"], "").notna()
            
        elif format_info["format"] == "database":
            # Database format processing
            df['Full_Address'] = df.apply(
                lambda row: clean_address_flexible(
                    row[format_info["street_col"]],
                    {"csz": row.get(format_info["csz_col"], "")},
                    format_info
                ), axis=1
            )
            
            # Combine first and last name
            first_name = df.get(format_info["first_name_col"], "").fillna("")
            last_name = df.get(format_info["last_name_col"], "").fillna("")
            df['Party_Name'] = (first_name + " " + last_name).str.strip()
            
            df['Case_ID'] = df[format_info["case_id_col"]]
            df['Has_Attorney'] = False  # Not available in this format
            df['Filing_Date'] = df.get(format_info["filing_date_col"], None)
        
        # Filter valid addresses
        valid_addresses = df[df['Full_Address'].notna() & (df['Full_Address'] != "")]
        print(f"📍 {len(valid_addresses)} records with valid addresses")
        
        # Get unique properties
        unique_properties = valid_addresses.drop_duplicates(subset=['Full_Address'])
        print(f"🏠 {len(unique_properties)} unique properties")
        
        # Get case statistics
        unique_cases = df['Case_ID'].nunique()
        print(f"⚖️  {unique_cases} unique divorce cases")
        
        # Process all properties (no limit)
        if max_properties > 0:
            unique_properties = unique_properties.head(max_properties)
            print(f"🎯 Analyzing {len(unique_properties)} properties (limited)")
        else:
            print(f"🎯 Analyzing all {len(unique_properties)} properties")
        
        # Initialize analyzer
        analyzer = DivorceLeadAnalyzer()
        
        results = []
        high_priority_leads = []
        
        print(f"\n🚀 STARTING ANALYSIS...")
        print("=" * 60)
        
        source_filename = os.path.basename(file_path)
        
        for idx, row in unique_properties.iterrows():
            address = row['Full_Address']
            case_id = row['Case_ID']
            party_name = row['Party_Name']
            
            print(f"\n[{len(results) + 1}/{len(unique_properties)}] {case_id}")
            print(f"👤 {party_name}")
            print(f"📍 {address}")
            
            # Create case data
            case_data = {
                "case_id": case_id,
                "case_type": "contested",
                "children": True,
                "duration_months": 18,
                "has_attorney": row.get('Has_Attorney', False)
            }
            
            # Analyze property
            result = analyzer.analyze_divorce_lead(address, case_data)
            
            if result.get("status") == "success":
                result["case_id"] = case_id
                result["party_name"] = party_name
                results.append(result)
                
                # Save to database
                save_to_database(result, source_filename)
                
                # Track high priority
                if result.get("distress_score", 0) >= 70:
                    high_priority_leads.append(result)
                    print(f"🔥 HIGH PRIORITY: Score {result['distress_score']}/100")
            
            time.sleep(0.3)  # Rate limiting
        
        # Generate report
        print(f"\n📋 ANALYSIS RESULTS")
        print("=" * 60)
        print(f"📊 Properties Analyzed: {len(results)}")
        print(f"🔥 High Priority (≥70): {len(high_priority_leads)}")
        print(f"💾 Saved to database: {len(results)} properties")
        
        if results:
            avg_score = sum(r.get("distress_score", 0) for r in results) / len(results)
            print(f"📈 Average Score: {avg_score:.1f}/100")
            
            # Risk breakdown
            risk_counts = {}
            for r in results:
                level = r.get("risk_level", "UNKNOWN")
                risk_counts[level] = risk_counts.get(level, 0) + 1
            
            print(f"\n🎯 RISK BREAKDOWN:")
            for level, count in risk_counts.items():
                emoji = {"CRITICAL": "🔴🚨", "HIGH": "🔴", "MEDIUM-HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(level, "⚪")
                pct = (count/len(results))*100
                print(f"   {emoji} {level}: {count} ({pct:.1f}%)")
        
        # Show top leads
        if high_priority_leads:
            print(f"\n🔥 TOP PRIORITY LEADS:")
            sorted_leads = sorted(high_priority_leads, key=lambda x: x.get("distress_score", 0), reverse=True)
            for i, lead in enumerate(sorted_leads[:3]):
                score = lead.get("distress_score", 0)
                value = lead.get("property_value", 0)
                discount = lead.get("discount_potential", "N/A")
                print(f"  {i+1}. Score {score}/100 | ${value:,} | {discount}")
                print(f"     {lead['address']}")
        
        # Save results
        timestamp = int(time.time())
        output_file = f"divorce_analysis_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump({
                "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_processed": file_path,
                "format_detected": format_info["format"],
                "total_records": len(df),
                "unique_cases": unique_cases,
                "properties_analyzed": len(results),
                "high_priority_count": len(high_priority_leads),
                "saved_to_database": len(results),
                "results": results
            }, f, indent=2)
        
        print(f"\n💾 Results saved: {output_file}")
        print(f"🌐 View dashboard: http://localhost:5001/distress-dashboard")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main execution"""
    files = [f for f in os.listdir('uploads') if f.endswith('.xlsx')]
    
    if not files:
        print("❌ No Excel files in uploads/")
        return
    
    print("📁 Available files:")
    for i, f in enumerate(files):
        size = os.path.getsize(f"uploads/{f}") / 1024
        print(f"  {i+1}. {f} ({size:.1f}KB)")
    
    # Process the most recent file
    latest = max(files, key=lambda f: os.path.getmtime(f"uploads/{f}"))
    print(f"\n🎯 Processing: {latest}")
    
    results = process_flexible_divorce_excel(f"uploads/{latest}", max_properties=0)
    print(f"\n✅ Complete! Analyzed {len(results)} properties.")

if __name__ == "__main__":
    main() 