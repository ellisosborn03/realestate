#!/usr/bin/env python3

import os
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ATTOM_API_KEY = "ad91f2f30426f1ee54aec35791aaa044"

def split_address(full_address):
    """Split full address into address1 (street) and address2 (city, state, zip)"""
    parts = full_address.rsplit(',', 2)
    
    if len(parts) >= 3:
        address1 = parts[0].strip()
        city_state_zip = f"{parts[1].strip()}, {parts[2].strip()}"
        return address1, city_state_zip
    elif len(parts) == 2:
        address1 = parts[0].strip()
        city_state_zip = parts[1].strip()
        return address1, city_state_zip
    else:
        match = re.search(r'^(.+?)\s+([A-Z\s]+),?\s+FL\s+(\d{5})$', full_address.strip())
        if match:
            street = match.group(1).strip()
            city = match.group(2).strip()
            zip_code = match.group(3)
            return street, f"{city}, FL {zip_code}"
        else:
            return full_address, ""

def generate_enhanced_variants(address1):
    """Generate more comprehensive address variants"""
    variants = [address1]
    
    # Strip unit/apt/lot/suite
    stripped = re.sub(r'\b(UNIT|APT|LOT|SUITE)\s*[A-Z0-9#\-]+$', '', address1).strip().rstrip(',')
    if stripped != address1:
        variants.append(stripped)
    
    # Street suffix variations
    suffix_map = [
        (r"\bDRIVE\b", "DR"), (r"\bDR\b", "DRIVE"),
        (r"\bROAD\b", "RD"), (r"\bRD\b", "ROAD"),
        (r"\bSTREET\b", "ST"), (r"\bST\b", "STREET"),
        (r"\bCOURT\b", "CT"), (r"\bCT\b", "COURT"),
        (r"\bLANE\b", "LN"), (r"\bLN\b", "LANE"),
        (r"\bAVENUE\b", "AVE"), (r"\bAVE\b", "AVENUE"),
        (r"\bBOULEVARD\b", "BLVD"), (r"\bBLVD\b", "BOULEVARD"),
        (r"\bPLACE\b", "PL"), (r"\bPL\b", "PLACE"),
        (r"\bPARKWAY\b", "PKWY"), (r"\bPKWY\b", "PARKWAY"),
        (r"\bTERRACE\b", "TER"), (r"\bTER\b", "TERRACE"),
        (r"\bCIRCLE\b", "CIR"), (r"\bCIR\b", "CIRCLE"),
        (r"\bWAY\b", "WAY"), (r"\bTRAIL\b", "TRL"),
    ]
    
    # Apply suffix changes to original and stripped
    base_addresses = [address1]
    if stripped != address1:
        base_addresses.append(stripped)
    
    for base in base_addresses:
        for pattern, replacement in suffix_map:
            alt = re.sub(pattern, replacement, base, flags=re.IGNORECASE)
            if alt != base and alt not in variants:
                variants.append(alt)
    
    # Try numbered street variations (10TH vs TENTH, etc.)
    for base in base_addresses:
        # Try ordinal to number (TENTH -> 10TH)
        ordinal_map = {
            'FIRST': '1ST', 'SECOND': '2ND', 'THIRD': '3RD', 'FOURTH': '4TH',
            'FIFTH': '5TH', 'SIXTH': '6TH', 'SEVENTH': '7TH', 'EIGHTH': '8TH',
            'NINTH': '9TH', 'TENTH': '10TH', 'ELEVENTH': '11TH', 'TWELFTH': '12TH'
        }
        for word, num in ordinal_map.items():
            if word in base:
                alt = base.replace(word, num)
                if alt not in variants:
                    variants.append(alt)
    
    # Remove duplicates and empty strings
    variants = [v for v in list(dict.fromkeys(variants)) if v.strip()]
    
    return variants

def try_attom_variants(address1_variants, address2):
    """Try each address1 variant until ATTOM AVM succeeds"""
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
    headers = {"accept": "application/json", "apikey": ATTOM_API_KEY}
    
    print(f"    Testing {len(address1_variants)} variants...")
    
    for i, variant in enumerate(address1_variants):
        print(f"    [{i+1}/{len(address1_variants)}] {variant}")
        
        params = {"address1": variant, "address2": address2}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", {})
                
                if status.get("code") == 0 and status.get("msg") == "SuccessWithResult":
                    properties = data.get("property", [])
                    if properties:
                        prop = properties[0]
                        address_info = prop.get("address", {})
                        avm = prop.get("avm", {})
                        amount = avm.get("amount", {})
                        
                        one_line = address_info.get("oneLine", f"{variant}, {address2}")
                        value = amount.get("value")
                        
                        print(f"    ✅ FOUND: {one_line} -> ${value:,}")
                        return one_line, value
                        
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print(f"    💥 No matches found")
    return f"{address1_variants[0]}, {address2}", None

def test_enhanced_pipeline(raw_address):
    """Enhanced testing pipeline"""
    print(f"\n🏠 {raw_address}")
    print("=" * 70)
    
    try:
        address1, address2 = split_address(raw_address)
        if not address2:
            print(f"❌ Could not parse address")
            return {"status": "failed", "address": raw_address, "valuation": None}
            
        print(f"Split: '{address1}' + '{address2}'")
        
        # Generate enhanced variants
        variants = generate_enhanced_variants(address1)
        print(f"Generated {len(variants)} variants: {variants[:5]}{'...' if len(variants) > 5 else ''}")
        
        # Try ATTOM
        final_address, valuation = try_attom_variants(variants, address2)
        
        if valuation:
            return {
                "status": "success",
                "address": final_address,
                "valuation": valuation
            }
        else:
            return {
                "status": "failed",
                "address": raw_address,
                "valuation": None
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "failed", "address": raw_address, "valuation": None}

# Test addresses - focusing on the failed ones
failed_addresses = [
    "4520 PGA BLVD, PALM BEACH GARDENS, FL 33418",
    "8401 LAKE WORTH ROAD, LAKE WORTH, FL 33467",
    "4943 LIQUID CT, West Palm Beach, FL 33415",
    "1520 10TH AVENUE N, LAKE WORTH, FL 33460",
    "60 LINDELL DRIVE, DELRAY BEACH, FL 33444",
    "5 HEATHER TRACE DRIVE, BOYNTON BEACH, FL 33436"
]

def main():
    print("🏠 ENHANCED ADDRESS VALIDATION TEST")
    print("Focusing on previously failed addresses...")
    print("=" * 70)
    
    results = []
    successful = 0
    
    for address in failed_addresses:
        result = test_enhanced_pipeline(address)
        results.append(result)
        
        if result["status"] == "success":
            successful += 1
        
        time.sleep(0.3)
    
    # Summary
    print(f"\n📊 RESULTS")
    print("=" * 50)
    print(f"Previously failed addresses: {len(failed_addresses)}")
    print(f"Now successful: {successful}")
    print(f"Improvement: {successful}/{len(failed_addresses)} addresses rescued")
    
    if successful > 0:
        print(f"\n✅ RESCUED ADDRESSES:")
        for result in results:
            if result["status"] == "success":
                val = result["valuation"]
                addr = result["address"]
                print(f"  ${val:,} - {addr}")

if __name__ == "__main__":
    main() 