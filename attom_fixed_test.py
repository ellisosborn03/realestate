#!/usr/bin/env python3

import requests
import json
import time
import re

ATTOM_API_KEY = "ad91f2f30426f1ee54aec35791aaa044"

def split_address(full_address):
    """Split full address into address1 (street) and address2 (city, state, zip)"""
    # Handle various formats like:
    # "4520 PGA BLVD, PALM BEACH GARDENS, FL 33418"
    # "4943 LIQUID CT, West Palm Beach, FL 33415"
    
    # Split on the last comma to separate address1 from city,state,zip
    parts = full_address.rsplit(',', 2)
    
    if len(parts) >= 3:
        # Format: "street, city, state zip"
        address1 = parts[0].strip()
        city_state_zip = f"{parts[1].strip()}, {parts[2].strip()}"
        return address1, city_state_zip
    elif len(parts) == 2:
        # Format: "street, city state zip"
        address1 = parts[0].strip()
        city_state_zip = parts[1].strip()
        return address1, city_state_zip
    else:
        # Single string - try to parse differently
        # Look for state pattern (FL) followed by zip
        match = re.search(r'^(.+?)\s+([A-Z\s]+),?\s+FL\s+(\d{5})$', full_address.strip())
        if match:
            street = match.group(1).strip()
            city = match.group(2).strip()
            zip_code = match.group(3)
            return street, f"{city}, FL {zip_code}"
        else:
            # Fallback - return as-is
            return full_address, ""

def test_attom_avm(address1, address2):
    """Test ATTOM AVM API with detailed response logging"""
    print(f"\n🔍 Testing ATTOM AVM:")
    print(f"  Address1: {address1}")
    print(f"  Address2: {address2}")
    print("-" * 50)
    
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
    
    headers = {
        "accept": "application/json",
        "apikey": ATTOM_API_KEY
    }
    
    params = {
        "address1": address1,
        "address2": address2
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Request URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            status = data.get("status", {})
            print(f"Status: {status}")
            
            if status.get("code") == 0 and status.get("msg") == "SuccessWithResult":
                properties = data.get("property", [])
                print(f"Properties found: {len(properties)}")
                
                if properties:
                    prop = properties[0]
                    address_info = prop.get("address", {})
                    avm = prop.get("avm", {})
                    amount = avm.get("amount", {})
                    
                    print(f"✅ Found property:")
                    print(f"  Address: {address_info.get('oneLine', 'N/A')}")
                    print(f"  AVM Value: ${amount.get('value', 'N/A')}")
                    print(f"  AVM keys: {list(avm.keys())}")
                    print(f"  Amount keys: {list(amount.keys())}")
                    
                    return amount.get('value')
                else:
                    print("❌ No properties found in response")
                    return None
            else:
                print(f"❌ API Status Error: {status}")
                return None
        else:
            print(f"❌ HTTP Error: {response.text[:300]}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

# Test addresses from your list
test_addresses = [
    "4520 PGA BLVD, PALM BEACH GARDENS, FL 33418",
    "8401 LAKE WORTH ROAD, LAKE WORTH, FL 33467", 
    "4943 LIQUID CT, West Palm Beach, FL 33415",
    "1520 10TH AVENUE N, LAKE WORTH, FL 33460",
    "920 POPLAR DRIVE, LAKE PARK, FL 33403",
    "60 LINDELL DRIVE, DELRAY BEACH, FL 33444",
    "4704 COHUNE PALM DRIVE, GREENACRES, FL 33463",
    "5 HEATHER TRACE DRIVE, BOYNTON BEACH, FL 33436"
]

print("🏠 ATTOM AVM API Test (Correct Format)")
print("=" * 60)

successful = 0
total = len(test_addresses)
results = []

for full_addr in test_addresses:
    address1, address2 = split_address(full_addr)
    valuation = test_attom_avm(address1, address2)
    
    if valuation:
        successful += 1
        results.append((full_addr, valuation))
        print(f"💰 SUCCESS: ${valuation:,}")
    else:
        print(f"❌ FAILED: No valuation")
    
    time.sleep(0.5)

print(f"\n📊 FINAL RESULTS")
print("=" * 60)
print(f"Successful: {successful}/{total} ({successful/total*100:.1f}%)")

if results:
    print(f"\n✅ SUCCESSFUL VALUATIONS:")
    for addr, val in results:
        print(f"  ${val:,} - {addr}")
else:
    print("\n❌ No successful valuations") 