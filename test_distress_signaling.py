#!/usr/bin/env python3

import requests
import json
import time
import re
import sys
import os
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append('src')
sys.path.append('src/services')

load_dotenv()

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

def get_comprehensive_attom_data(address1, address2):
    """Get comprehensive ATTOM property data for distress analysis"""
    
    # Try AVM endpoint first
    avm_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
    avm_headers = {"accept": "application/json", "apikey": ATTOM_API_KEY}
    avm_params = {"address1": address1, "address2": address2}
    
    avm_data = {}
    try:
        resp = requests.get(avm_url, params=avm_params, headers=avm_headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status", {}).get("code") == 0:
                properties = data.get("property", [])
                if properties:
                    prop = properties[0]
                    avm_data = {
                        "avm_value": prop.get("avm", {}).get("amount", {}).get("value"),
                        "address": prop.get("address", {}).get("oneLine"),
                        "source": "AVM"
                    }
    except Exception as e:
        print(f"    AVM Error: {e}")
    
    # Try Property Detail endpoint for more comprehensive data
    detail_url = "https://search.onboard-apis.com/propertyapi/v1.0.0/property/detail"
    detail_headers = {"Accept": "application/json", "apikey": ATTOM_API_KEY}
    detail_params = {"address1": address1, "address2": address2, "format": "json"}
    
    detail_data = {}
    try:
        resp = requests.get(detail_url, params=detail_params, headers=detail_headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            properties = data.get("property", [])
            if properties:
                prop = properties[0]
                
                # Extract comprehensive property data
                address_info = prop.get("address", {})
                assessment = prop.get("assessment", {})
                building = prop.get("building", {})
                lot = prop.get("lot", {})
                
                detail_data = {
                    "address": address_info.get("oneLine"),
                    "property_type": building.get("propertyType"),
                    "year_built": building.get("yearBuilt"),
                    "bedrooms": building.get("rooms", {}).get("beds"),
                    "bathrooms": building.get("rooms", {}).get("baths"),
                    "square_feet": building.get("size", {}).get("livingsize"),
                    "lot_size": lot.get("lotsize1"),
                    "assessment_data": assessment,
                    "source": "Property Detail"
                }
                
                # Market value from assessment
                market = assessment.get("market", {})
                if market.get("mktttlvalue"):
                    detail_data["market_value"] = market.get("mktttlvalue")
    
    except Exception as e:
        print(f"    Property Detail Error: {e}")
    
    # Combine data
    combined_data = {**detail_data, **avm_data}
    return combined_data

def generate_mock_distress_indicators(property_data, address):
    """Generate mock distress indicators for testing (since we don't have full ATTOM data)"""
    
    # Base distress indicators with some realistic mock data
    indicators = {
        # From ATTOM (if available)
        "loanToValuePct": property_data.get("loanToValuePct", 0),
        "daysOnMarket": property_data.get("daysOnMarket", 0),
        "medianDaysOnMarket": property_data.get("medianDaysOnMarket", 60),  # Mock median
        "originalListPrice": property_data.get("originalListPrice", 0),
        "currentListPrice": property_data.get("currentListPrice", 0),
        "preforeclosureActive": property_data.get("preforeclosureActive", False),
        "taxDelinquent": property_data.get("taxDelinquent", False),
        "absenteeOwner": property_data.get("absenteeOwner", False),
        "absorptionRate": property_data.get("absorptionRate", 0.15),  # Mock absorption rate
        
        # Additional mock indicators for testing
        "property_value": property_data.get("avm_value") or property_data.get("market_value", 0),
        "address": property_data.get("address", address),
        "property_type": property_data.get("property_type", "Unknown"),
        "year_built": property_data.get("year_built"),
        "square_feet": property_data.get("square_feet")
    }
    
    # Generate some mock distress scenarios based on address characteristics
    if "PGA BLVD" in address.upper():
        # Commercial property - higher LTV, longer on market
        indicators.update({
            "loanToValuePct": 85,
            "daysOnMarket": 120,
            "absenteeOwner": True,
            "scenario": "Commercial Property Distress"
        })
    elif "LIQUID CT" in address.upper():
        # Condo - price reduction scenario
        indicators.update({
            "loanToValuePct": 90,
            "originalListPrice": 350000,
            "currentListPrice": 315000,
            "daysOnMarket": 95,
            "scenario": "Condo Price Reduction"
        })
    elif "LAKE WORTH" in address.upper():
        # Tax delinquent scenario
        indicators.update({
            "taxDelinquent": True,
            "loanToValuePct": 95,
            "daysOnMarket": 180,
            "scenario": "Tax Delinquent Property"
        })
    elif "POPLAR" in address.upper() or "COHUNE" in address.upper():
        # Healthy properties (we know these have valuations)
        indicators.update({
            "loanToValuePct": 65,
            "daysOnMarket": 30,
            "absorptionRate": 0.25,
            "scenario": "Healthy Property"
        })
    else:
        # Default moderate distress
        indicators.update({
            "loanToValuePct": 80,
            "daysOnMarket": 75,
            "scenario": "Moderate Market Stress"
        })
    
    return indicators

def calculate_distress_score(distress_data):
    """Calculate distress score using the existing algorithm"""
    try:
        from calculateDistressScore import calculateDistressScore
        result = calculateDistressScore(distress_data)
        return result
    except ImportError:
        # Fallback calculation if import fails
        score = 0
        
        # LTV (25% weight)
        ltv = distress_data.get("loanToValuePct", 0)
        if ltv > 90:
            score += 25
        elif ltv > 80:
            score += 20
        elif ltv > 70:
            score += 15
        elif ltv > 60:
            score += 10
        
        # Days on Market (20% weight)
        dom = distress_data.get("daysOnMarket", 0)
        median_dom = distress_data.get("medianDaysOnMarket", 60)
        if dom > median_dom * 2:
            score += 20
        elif dom > median_dom * 1.5:
            score += 15
        elif dom > median_dom:
            score += 10
        
        # Price Reduction (15% weight)
        original = distress_data.get("originalListPrice", 0)
        current = distress_data.get("currentListPrice", 0)
        if original > 0 and current > 0:
            reduction_pct = ((original - current) / original) * 100
            if reduction_pct > 15:
                score += 15
            elif reduction_pct > 10:
                score += 10
            elif reduction_pct > 5:
                score += 7
        
        # Binary indicators
        if distress_data.get("preforeclosureActive"):
            score += 15
        if distress_data.get("taxDelinquent"):
            score += 10
        if distress_data.get("absenteeOwner"):
            score += 10
        
        # Absorption rate (5% weight)
        absorption = distress_data.get("absorptionRate", 0)
        if absorption < 0.1:
            score += 5
        elif absorption < 0.15:
            score += 3
        
        return {"distressScore": min(score, 100), "riskLevel": "HIGH" if score > 70 else "MEDIUM" if score > 40 else "LOW"}

def test_distress_signaling_pipeline(raw_address):
    """Complete distress signaling test pipeline"""
    print(f"\n🚨 DISTRESS ANALYSIS: {raw_address}")
    print("=" * 80)
    
    # Step 1: Parse address
    address1, address2 = split_address(raw_address)
    if not address2:
        return {"error": "Could not parse address", "address": raw_address}
    
    print(f"📍 Parsed: '{address1}' + '{address2}'")
    
    # Step 2: Get ATTOM property data
    print("🔍 Fetching ATTOM property data...")
    property_data = get_comprehensive_attom_data(address1, address2)
    
    if property_data:
        print(f"✅ Property found: {property_data.get('address', 'N/A')}")
        if property_data.get('avm_value'):
            print(f"💰 AVM Value: ${property_data['avm_value']:,}")
        if property_data.get('market_value'):
            print(f"🏠 Market Value: ${property_data['market_value']:,}")
        if property_data.get('property_type'):
            print(f"🏗️  Property Type: {property_data['property_type']}")
    else:
        print("❌ No ATTOM data found - using address for mock indicators")
    
    # Step 3: Generate distress indicators (mock data for testing)
    print("\n📊 Generating distress indicators...")
    distress_indicators = generate_mock_distress_indicators(property_data, raw_address)
    
    print(f"   Scenario: {distress_indicators.get('scenario', 'Unknown')}")
    print(f"   LTV: {distress_indicators.get('loanToValuePct', 0)}%")
    print(f"   Days on Market: {distress_indicators.get('daysOnMarket', 0)}")
    print(f"   Tax Delinquent: {distress_indicators.get('taxDelinquent', False)}")
    print(f"   Absentee Owner: {distress_indicators.get('absenteeOwner', False)}")
    
    # Step 4: Calculate distress score
    print("\n🎯 Calculating distress score...")
    distress_result = calculate_distress_score(distress_indicators)
    
    score = distress_result.get("distressScore", 0)
    risk_level = distress_result.get("riskLevel", "UNKNOWN")
    
    # Color coding for output
    if risk_level == "HIGH":
        risk_emoji = "🔴"
    elif risk_level == "MEDIUM":
        risk_emoji = "🟡"
    else:
        risk_emoji = "🟢"
    
    print(f"   {risk_emoji} Distress Score: {score}/100")
    print(f"   {risk_emoji} Risk Level: {risk_level}")
    
    return {
        "address": raw_address,
        "parsed_address": property_data.get('address', f"{address1}, {address2}"),
        "property_data": property_data,
        "distress_indicators": distress_indicators,
        "distress_score": score,
        "risk_level": risk_level,
        "status": "success"
    }

# Test addresses for distress signaling
test_addresses = [
    "920 POPLAR DRIVE, LAKE PARK, FL 33403",  # Known working (healthy)
    "4704 COHUNE PALM DRIVE, GREENACRES, FL 33463",  # Known working (healthy)
    "4520 PGA BLVD, PALM BEACH GARDENS, FL 33418",  # Commercial distress
    "4943 LIQUID CT, West Palm Beach, FL 33415",  # Condo distress
    "8401 LAKE WORTH ROAD, LAKE WORTH, FL 33467",  # Tax delinquent
    "1520 10TH AVENUE N, LAKE WORTH, FL 33460",  # Moderate stress
]

def main():
    print("🚨 DISTRESS SIGNALING TEST SUITE")
    print("=" * 80)
    print("Testing comprehensive distress analysis pipeline...")
    
    results = []
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    
    for address in test_addresses:
        result = test_distress_signaling_pipeline(address)
        results.append(result)
        
        if result.get("risk_level") == "HIGH":
            high_risk_count += 1
        elif result.get("risk_level") == "MEDIUM":
            medium_risk_count += 1
        else:
            low_risk_count += 1
        
        time.sleep(0.5)
    
    # Summary Report
    print(f"\n📋 DISTRESS SIGNALING SUMMARY")
    print("=" * 80)
    print(f"Total properties analyzed: {len(test_addresses)}")
    print(f"🔴 HIGH Risk: {high_risk_count}")
    print(f"🟡 MEDIUM Risk: {medium_risk_count}")
    print(f"🟢 LOW Risk: {low_risk_count}")
    
    print(f"\n🔴 HIGH RISK PROPERTIES:")
    for result in results:
        if result.get("risk_level") == "HIGH":
            score = result.get("distress_score", 0)
            scenario = result.get("distress_indicators", {}).get("scenario", "Unknown")
            print(f"  Score {score}/100 - {result['address']} ({scenario})")
    
    print(f"\n🟡 MEDIUM RISK PROPERTIES:")
    for result in results:
        if result.get("risk_level") == "MEDIUM":
            score = result.get("distress_score", 0)
            scenario = result.get("distress_indicators", {}).get("scenario", "Unknown")
            print(f"  Score {score}/100 - {result['address']} ({scenario})")
    
    print(f"\n🟢 LOW RISK PROPERTIES:")
    for result in results:
        if result.get("risk_level") == "LOW":
            score = result.get("distress_score", 0)
            scenario = result.get("distress_indicators", {}).get("scenario", "Unknown")
            print(f"  Score {score}/100 - {result['address']} ({scenario})")

if __name__ == "__main__":
    main() 