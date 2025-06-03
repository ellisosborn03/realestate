#!/usr/bin/env python3

import requests
import json
import time

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

def try_property_detail_endpoint(address1, address2):
    """Try ATTOM property detail endpoint for market assessment value"""
    url = "https://search.onboard-apis.com/propertyapi/v1.0.0/property/detail"
    
    headers = {
        "Accept": "application/json",
        "apikey": ATTOM_API_KEY
    }
    
    params = {
        "address1": address1,
        "address2": address2,
        "format": "json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            properties = data.get("property", [])
            
            if properties:
                prop = properties[0]
                address_info = prop.get("address", {})
                assessment = prop.get("assessment", {})
                market = assessment.get("market", {})
                
                valuation = market.get("mktttlvalue")
                one_line = address_info.get("oneLine", f"{address1}, {address2}")
                
                print(f"✅ Property Detail: {one_line}")
                print(f"   Market Value: ${valuation:,}" if valuation else "   Market Value: N/A")
                print(f"   Assessment keys: {list(assessment.keys())}")
                print(f"   Market keys: {list(market.keys())}")
                
                return valuation, one_line
            else:
                print(f"❌ No properties found")
                return None, None
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def test_both_endpoints(raw_address):
    """Test both AVM and Property Detail endpoints"""
    print(f"\n🏠 {raw_address}")
    print("=" * 70)
    
    address1, address2 = split_address(raw_address)
    if not address2:
        print("❌ Could not parse address")
        return
    
    print(f"Split: '{address1}' + '{address2}'")
    
    # Test 1: AVM endpoint (what we've been using)
    print(f"\n1️⃣ AVM Endpoint:")
    avm_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
    avm_params = {"address1": address1, "address2": address2}
    avm_headers = {"accept": "application/json", "apikey": ATTOM_API_KEY}
    
    try:
        resp = requests.get(avm_url, params=avm_params, headers=avm_headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", {})
            if status.get("code") == 0 and status.get("msg") == "SuccessWithResult":
                prop = data.get("property", [{}])[0]
                avm_val = prop.get("avm", {}).get("amount", {}).get("value")
                print(f"✅ AVM Value: ${avm_val:,}" if avm_val else "❌ AVM: No value")
            else:
                print(f"❌ AVM: {status.get('msg')} (attomId: {status.get('attomId', 'None')})")
    except Exception as e:
        print(f"❌ AVM Error: {e}")
    
    # Test 2: Property Detail endpoint  
    print(f"\n2️⃣ Property Detail Endpoint:")
    detail_val, detail_addr = try_property_detail_endpoint(address1, address2)
    
    # Test 3: Try with street suffix variations
    print(f"\n3️⃣ Trying suffix variants:")
    if "ROAD" in address1:
        alt_address1 = address1.replace("ROAD", "RD")
        print(f"   Trying: {alt_address1}")
        alt_val, alt_addr = try_property_detail_endpoint(alt_address1, address2)
    elif "DRIVE" in address1:
        alt_address1 = address1.replace("DRIVE", "DR")
        print(f"   Trying: {alt_address1}")
        alt_val, alt_addr = try_property_detail_endpoint(alt_address1, address2)
    else:
        print("   No obvious suffix to try")

# Test the failed addresses
failed_addresses = [
    "4520 PGA BLVD, PALM BEACH GARDENS, FL 33418",
    "8401 LAKE WORTH ROAD, LAKE WORTH, FL 33467",
    "4943 LIQUID CT, West Palm Beach, FL 33415",
    "1520 10TH AVENUE N, LAKE WORTH, FL 33460"
]

def main():
    print("🔍 TESTING MULTIPLE ATTOM ENDPOINTS")
    print("=" * 70)
    
    for address in failed_addresses:
        test_both_endpoints(address)
        time.sleep(0.5)

if __name__ == "__main__":
    main() 