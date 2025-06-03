#!/usr/bin/env python3

import requests
import json
import time
import re

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
        return full_address, ""

def generate_address_variants(address1):
    """Generate comprehensive address variants"""
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
    ]
    
    base_addresses = [address1]
    if stripped != address1:
        base_addresses.append(stripped)
    
    for base in base_addresses:
        for pattern, replacement in suffix_map:
            alt = re.sub(pattern, replacement, base, flags=re.IGNORECASE)
            if alt != base and alt not in variants:
                variants.append(alt)
    
    return list(dict.fromkeys(variants))  # Remove duplicates

def try_attom_avm(address1, address2):
    """Try ATTOM AVM endpoint"""
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
    headers = {"accept": "application/json", "apikey": ATTOM_API_KEY}
    params = {"address1": address1, "address2": address2}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", {})
            
            if status.get("code") == 0 and status.get("msg") == "SuccessWithResult":
                properties = data.get("property", [])
                if properties:
                    prop = properties[0]
                    avm_val = prop.get("avm", {}).get("amount", {}).get("value")
                    address_info = prop.get("address", {})
                    one_line = address_info.get("oneLine", f"{address1}, {address2}")
                    
                    if avm_val:
                        return {"type": "AVM", "value": avm_val, "address": one_line, "status": "success"}
            
            # Property found but no AVM value
            attom_id = status.get("attomId")
            if attom_id:
                return {"type": "AVM", "value": None, "address": f"{address1}, {address2}", "status": "found_no_value", "attomId": attom_id}
                
    except Exception as e:
        pass
    
    return {"type": "AVM", "status": "failed"}

def try_attom_property_detail(address1, address2):
    """Try ATTOM Property Detail endpoint"""
    url = "https://search.onboard-apis.com/propertyapi/v1.0.0/property/detail"
    headers = {"Accept": "application/json", "apikey": ATTOM_API_KEY}
    params = {"address1": address1, "address2": address2, "format": "json"}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            properties = data.get("property", [])
            
            if properties:
                prop = properties[0]
                address_info = prop.get("address", {})
                assessment = prop.get("assessment", {})
                market = assessment.get("market", {})
                
                market_val = market.get("mktttlvalue")
                one_line = address_info.get("oneLine", f"{address1}, {address2}")
                
                if market_val:
                    return {"type": "Property", "value": market_val, "address": one_line, "status": "success"}
                else:
                    return {"type": "Property", "value": None, "address": one_line, "status": "found_no_value"}
                    
    except Exception as e:
        pass
    
    return {"type": "Property", "status": "failed"}

def comprehensive_attom_lookup(raw_address):
    """Comprehensive ATTOM lookup with all variants and endpoints"""
    print(f"\n🏠 {raw_address}")
    print("=" * 70)
    
    address1, address2 = split_address(raw_address)
    if not address2:
        return {"status": "parse_failed", "address": raw_address}
    
    print(f"Parsed: '{address1}' + '{address2}'")
    
    # Generate variants
    variants = generate_address_variants(address1)
    print(f"Testing {len(variants)} variants: {variants}")
    
    results = []
    
    for i, variant in enumerate(variants):
        print(f"\n  [{i+1}/{len(variants)}] {variant}")
        
        # Try AVM first (faster)
        avm_result = try_attom_avm(variant, address2)
        if avm_result["status"] == "success":
            print(f"    ✅ AVM: ${avm_result['value']:,} - {avm_result['address']}")
            return {
                "status": "success",
                "source": "AVM",
                "value": avm_result["value"],
                "address": avm_result["address"],
                "original": raw_address
            }
        elif avm_result["status"] == "found_no_value":
            print(f"    📍 AVM: Found property (ID: {avm_result.get('attomId')}) but no valuation")
            results.append(avm_result)
        else:
            print(f"    ❌ AVM: Not found")
        
        # Try Property Detail
        detail_result = try_attom_property_detail(variant, address2)
        if detail_result["status"] == "success":
            print(f"    ✅ Property: ${detail_result['value']:,} - {detail_result['address']}")
            return {
                "status": "success",
                "source": "Property",
                "value": detail_result["value"],
                "address": detail_result["address"],
                "original": raw_address
            }
        elif detail_result["status"] == "found_no_value":
            print(f"    📍 Property: Found {detail_result['address']} but no market value")
            results.append(detail_result)
        else:
            print(f"    ❌ Property: Not found")
    
    # Check if we found any properties (even without values)
    found_properties = [r for r in results if r["status"] == "found_no_value"]
    if found_properties:
        best_match = found_properties[0]
        return {
            "status": "found_no_value",
            "address": best_match["address"],
            "original": raw_address,
            "note": "Property exists but no valuation data available"
        }
    
    return {
        "status": "not_found",
        "address": raw_address,
        "note": "Property not found in ATTOM database"
    }

# Test all addresses from original list
all_addresses = [
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
    print("🏠 FINAL COMPREHENSIVE ATTOM SOLUTION")
    print("=" * 70)
    
    results = []
    success_count = 0
    found_count = 0
    
    for address in all_addresses:
        result = comprehensive_attom_lookup(address)
        results.append(result)
        
        if result["status"] == "success":
            success_count += 1
        elif result["status"] == "found_no_value":
            found_count += 1
        
        time.sleep(0.3)
    
    # Final Summary
    print(f"\n📊 FINAL RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total addresses: {len(all_addresses)}")
    print(f"✅ Got valuations: {success_count}")
    print(f"📍 Found but no valuation: {found_count}")
    print(f"❌ Not found: {len(all_addresses) - success_count - found_count}")
    print(f"Success rate: {success_count/len(all_addresses)*100:.1f}%")
    print(f"Find rate: {(success_count + found_count)/len(all_addresses)*100:.1f}%")
    
    print(f"\n✅ SUCCESSFUL VALUATIONS:")
    for result in results:
        if result["status"] == "success":
            print(f"  ${result['value']:,} - {result['address']} (via {result['source']})")
    
    print(f"\n📍 FOUND BUT NO VALUATION:")
    for result in results:
        if result["status"] == "found_no_value":
            print(f"  {result['address']} - {result['note']}")
    
    print(f"\n❌ NOT FOUND:")
    for result in results:
        if result["status"] == "not_found":
            print(f"  {result['address']}")

if __name__ == "__main__":
    main() 