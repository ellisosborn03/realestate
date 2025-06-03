#!/usr/bin/env python3

import os
import requests
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ATTOM_API_KEY = os.getenv("ATTOM_API_KEY", "05b92ead42c0f09a4b9c4b96d3f73a94")

def validate_address_with_google(raw_address):
    """Use Google Places Autocomplete to validate and standardize address"""
    if not GOOGLE_API_KEY:
        print("❌ No Google API key found - set GOOGLE_API_KEY in .env")
        return None
    
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
            # Get the first prediction (most likely match)
            prediction = data["predictions"][0]
            return {
                "formatted_address": prediction["description"],
                "place_id": prediction.get("place_id"),
                "status": "success"
            }
        else:
            return {
                "error": f"Google API error: {data.get('status', 'Unknown')}",
                "status": "failed"
            }
    except Exception as e:
        return {
            "error": f"Google API request failed: {str(e)}",
            "status": "failed"
        }

def get_attom_valuation(address):
    """Get property valuation from ATTOM API"""
    if not address:
        return {"error": "No address provided", "status": "failed"}
    
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
        
        if response.status_code == 200:
            data = response.json()
            properties = data.get("property", [])
            
            if properties:
                prop = properties[0]
                valuation = prop.get("assessment", {}).get("market", {}).get("mktttlvalue")
                
                return {
                    "valuation": valuation,
                    "address": prop.get("address", {}).get("oneLine"),
                    "status": "success",
                    "property_count": len(properties)
                }
            else:
                return {
                    "error": "No properties found",
                    "status": "no_results"
                }
        else:
            return {
                "error": f"ATTOM API error: {response.status_code} - {response.text[:200]}",
                "status": "failed"
            }
    except Exception as e:
        return {
            "error": f"ATTOM API request failed: {str(e)}",
            "status": "failed"
        }

def test_address_pipeline(raw_address):
    """Complete pipeline: Google validation -> ATTOM valuation"""
    print(f"\n🔍 Testing: {raw_address}")
    print("=" * 60)
    
    # Step 1: Google Places validation
    print("1️⃣  Google Places validation...")
    google_result = validate_address_with_google(raw_address)
    
    if google_result["status"] == "success":
        validated_address = google_result["formatted_address"]
        print(f"✅ Google validated: {validated_address}")
        
        # Step 2: ATTOM valuation
        print("2️⃣  ATTOM valuation...")
        attom_result = get_attom_valuation(validated_address)
        
        if attom_result["status"] == "success":
            valuation = attom_result.get("valuation")
            if valuation:
                print(f"💰 Valuation: ${valuation:,}")
                print(f"📍 ATTOM address: {attom_result.get('address')}")
                return {"status": "success", "valuation": valuation, "address": validated_address}
            else:
                print("⚠️  No valuation data available")
                return {"status": "no_valuation", "address": validated_address}
        else:
            print(f"❌ ATTOM failed: {attom_result.get('error')}")
            return {"status": "attom_failed", "address": validated_address}
    else:
        print(f"❌ Google validation failed: {google_result.get('error')}")
        
        # Try ATTOM with original address anyway
        print("2️⃣  Trying ATTOM with original address...")
        attom_result = get_attom_valuation(raw_address)
        
        if attom_result["status"] == "success":
            valuation = attom_result.get("valuation")
            if valuation:
                print(f"💰 Valuation (original): ${valuation:,}")
                return {"status": "success_original", "valuation": valuation, "address": raw_address}
        
        return {"status": "failed", "error": google_result.get("error")}

# Test addresses from the user's list
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
    print("🏠 Real Estate Address Validation & Valuation Test")
    print("=" * 60)
    
    results = []
    successful_valuations = 0
    
    for address in test_addresses:
        result = test_address_pipeline(address)
        results.append({
            "original": address,
            "result": result
        })
        
        if result.get("status") in ["success", "success_original"]:
            successful_valuations += 1
        
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    print(f"Total addresses tested: {len(test_addresses)}")
    print(f"Successful valuations: {successful_valuations}")
    print(f"Success rate: {successful_valuations/len(test_addresses)*100:.1f}%")
    
    print(f"\n✅ SUCCESSFUL VALUATIONS:")
    for r in results:
        if r["result"].get("status") in ["success", "success_original"]:
            val = r["result"].get("valuation")
            print(f"  ${val:,} - {r['original']}")

if __name__ == "__main__":
    main() 