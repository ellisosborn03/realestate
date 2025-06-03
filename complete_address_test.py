#!/usr/bin/env python3

import os
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv()

# API Keys
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

def validate_with_google_places(raw_address):
    """Use Google Places Autocomplete to validate address"""
    if not GOOGLE_API_KEY:
        return {"status": "skipped", "error": "No Google API key"}
    
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": raw_address,
        "types": "address",
        "components": "country:us|administrative_area:FL",
        "key": GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "OK" and data.get("predictions"):
            return {
                "status": "success",
                "formatted_address": data["predictions"][0]["description"],
                "place_id": data["predictions"][0].get("place_id")
            }
        else:
            return {
                "status": "failed",
                "error": f"Google API status: {data.get('status', 'Unknown')}"
            }
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Google API error: {str(e)}"
        }

def strip_unit_or_lot_suffix(address):
    """Remove unit or lot info from address for retrying ATTOM lookups"""
    return re.sub(r'\b(UNIT|APT|LOT)\s*[A-Z0-9#\-]+$', '', address).strip().rstrip(',')

def generate_address_variants(address1):
    """Generate address variants: original, stripped unit/apt/lot, alternate suffixes"""
    variants = [address1]
    
    # Strip unit/apt/lot
    stripped = strip_unit_or_lot_suffix(address1)
    if stripped != address1:
        variants.append(stripped)
    
    # Try alternate suffixes
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
    ]
    
    for pattern, replacement in suffix_map:
        alt = re.sub(pattern, replacement, address1, flags=re.IGNORECASE)
        if alt != address1 and alt not in variants:
            variants.append(alt)
        if stripped:
            alt2 = re.sub(pattern, replacement, stripped, flags=re.IGNORECASE)
            if alt2 != stripped and alt2 not in variants:
                variants.append(alt2)
    
    return variants

def try_attom_variants(address1_variants, address2):
    """Try each address1 variant until ATTOM AVM succeeds"""
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
    headers = {"accept": "application/json", "apikey": ATTOM_API_KEY}
    
    for i, variant in enumerate(address1_variants):
        print(f"    [{i+1}/{len(address1_variants)}] Trying: {variant}")
        
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
                        
                        print(f"    ✅ SUCCESS: {one_line} -> ${value:,}")
                        return one_line, value
                    
            print(f"    ❌ No result for: {variant}")
            
        except Exception as e:
            print(f"    ❌ Error for {variant}: {e}")
    
    print(f"    💥 All variants failed for: {address1_variants[0]}")
    return f"{address1_variants[0]}, {address2}", None

def test_complete_pipeline(raw_address):
    """Complete pipeline: Google validation -> ATTOM variants"""
    print(f"\n🏠 Testing: {raw_address}")
    print("=" * 70)
    
    # Step 1: Try Google Places validation
    print("1️⃣  Google Places validation...")
    google_result = validate_with_google_places(raw_address)
    
    addresses_to_try = []
    
    if google_result["status"] == "success":
        validated = google_result["formatted_address"]
        print(f"    ✅ Google validated: {validated}")
        addresses_to_try.append(("Google", validated))
    elif google_result["status"] == "skipped":
        print(f"    ⏭️  Google skipped: {google_result['error']}")
    else:
        print(f"    ❌ Google failed: {google_result['error']}")
    
    # Always try original too
    addresses_to_try.append(("Original", raw_address))
    
    # Step 2: Try ATTOM with variants
    print("2️⃣  ATTOM AVM with variants...")
    
    for source, addr in addresses_to_try:
        print(f"  📍 Trying {source} address: {addr}")
        
        try:
            address1, address2 = split_address(addr)
            if not address2:
                print(f"    ❌ Could not split address: {addr}")
                continue
                
            print(f"    Split: '{address1}' + '{address2}'")
            
            # Generate variants
            variants = generate_address_variants(address1)
            print(f"    Generated {len(variants)} variants: {variants}")
            
            # Try variants
            final_address, valuation = try_attom_variants(variants, address2)
            
            if valuation:
                return {
                    "status": "success",
                    "source": source,
                    "address": final_address,
                    "valuation": valuation
                }
                
        except Exception as e:
            print(f"    ❌ Error processing {source} address: {e}")
    
    return {
        "status": "failed",
        "address": raw_address,
        "valuation": None
    }

# Test addresses from your list
test_addresses = [
    "4520 PGA BLVD, PALM BEACH GARDENS, FL 33418",
    "8401 LAKE WORTH ROAD, LAKE WORTH, FL 33467", 
    "4520 PGA BLVD SUITE 109, PALM BEACH GARDENS, FL 33418",
    "4520 PGA BLVD SUITE 304B, PALM BEACH GARDENS, FL 33418",
    "4943 LIQUID CT, West Palm Beach, FL 33415",
    "4943 LIQUID CT UNIT A32, West Palm Beach, FL 33415",
    "1520 10TH AVENUE N, LAKE WORTH, FL 33460",
    "1520 10TH AVENUE N SUITE F, LAKE WORTH, FL 33460",
    "920 POPLAR DRIVE, LAKE PARK, FL 33403",
    "60 LINDELL DRIVE, DELRAY BEACH, FL 33444",
    "4704 COHUNE PALM DRIVE, GREENACRES, FL 33463",
    "5 HEATHER TRACE DRIVE, BOYNTON BEACH, FL 33436"
]

def main():
    print("🏠 COMPLETE ADDRESS VALIDATION & VALUATION TEST")
    print("=" * 70)
    
    results = []
    successful = 0
    
    for address in test_addresses:
        result = test_complete_pipeline(address)
        results.append(result)
        
        if result["status"] == "success":
            successful += 1
        
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    print(f"\n📊 FINAL SUMMARY")
    print("=" * 70)
    print(f"Addresses tested: {len(test_addresses)}")
    print(f"Successful valuations: {successful}")
    print(f"Success rate: {successful/len(test_addresses)*100:.1f}%")
    
    print(f"\n✅ SUCCESSFUL VALUATIONS:")
    for result in results:
        if result["status"] == "success":
            val = result["valuation"]
            addr = result["address"]
            source = result.get("source", "Unknown")
            print(f"  ${val:,} - {addr} (via {source})")
    
    print(f"\n❌ FAILED ADDRESSES:")
    for i, result in enumerate(results):
        if result["status"] == "failed":
            print(f"  {test_addresses[i]}")

if __name__ == "__main__":
    main() 