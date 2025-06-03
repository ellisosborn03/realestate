#!/usr/bin/env python3

import requests
import json
import time

ATTOM_API_KEY = "ad91f2f30426f1ee54aec35791aaa044"

def test_attom_address(address):
    """Test ATTOM API with detailed response logging"""
    print(f"\n🔍 Testing ATTOM: {address}")
    print("-" * 50)
    
    url = "https://search.onboard-apis.com/propertyapi/v1.0.0/property/detail"
    
    headers = {
        "Accept": "application/json",
        "apikey": ATTOM_API_KEY
    }
    
    params = {
        "address1": address,
        "format": "json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Request URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            properties = data.get("property", [])
            print(f"Properties found: {len(properties)}")
            
            if properties:
                prop = properties[0]
                address_info = prop.get("address", {})
                assessment = prop.get("assessment", {})
                market = assessment.get("market", {})
                
                print(f"✅ Found property:")
                print(f"  Address: {address_info.get('oneLine', 'N/A')}")
                print(f"  Market Value: ${market.get('mktttlvalue', 'N/A')}")
                print(f"  Assessment keys: {list(assessment.keys())}")
                print(f"  Market keys: {list(market.keys())}")
                
                return market.get('mktttlvalue')
            else:
                print("❌ No properties found in response")
                return None
        else:
            print(f"❌ API Error: {response.text[:300]}")
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

# Also test with cleaned versions (no commas)
def clean_address(addr):
    return addr.replace(", ", " ").replace(",", " ")

print("🏠 ATTOM API Direct Test")
print("=" * 60)

successful = 0
total = len(test_addresses)

for addr in test_addresses:
    valuation = test_attom_address(addr)
    if valuation:
        successful += 1
        print(f"💰 SUCCESS: ${valuation:,}")
    else:
        # Try without commas
        clean_addr = clean_address(addr)
        if clean_addr != addr:
            print(f"🔄 Retrying without commas: {clean_addr}")
            valuation = test_attom_address(clean_addr)
            if valuation:
                successful += 1
                print(f"💰 SUCCESS (cleaned): ${valuation:,}")
    
    time.sleep(0.5)

print(f"\n📊 FINAL RESULTS")
print("=" * 40)
print(f"Successful: {successful}/{total} ({successful/total*100:.1f}%)") 