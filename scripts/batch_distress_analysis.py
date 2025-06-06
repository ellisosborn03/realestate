import os
import requests
import json
from typing import List, Dict

# You must set these environment variables
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
ATTOM_API_KEY = os.environ.get('ATTOM_API_KEY')

PROPERTIES = [
    {"street": "360 COLUMBIA DRIVE SUITE #100", "city": "WEST PALM BEACH", "state": "FL", "zip_code": "33409"},
    {"street": "824 W. INDIANTOWN ROAD", "city": "JUPITER", "state": "FL", "zip_code": "33458"},
    {"street": "22000 PORTOFINO CIR. APT. 103", "city": "PALM BEACH GARDENS", "state": "FL", "zip_code": "33418"},
    {"street": "11901 S GARDENS DRIVE #104 N", "city": "PALM BEACH GARDENS", "state": "FL", "zip_code": "33418"},
    {"street": "1675 N MILITARY TR STE. 730", "city": "BOCA RATON", "state": "FL", "zip_code": "33486"},
]

def get_google_place(address: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/place/findplacefromquery/json"
    params = {
        "input": address,
        "inputtype": "textquery",
        "fields": "formatted_address,address_components,place_id",
        "key": GOOGLE_API_KEY
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def ask_groq_for_address(raw_address: str, google_result: dict) -> dict:
    # This is a stub for the Groq API call
    # Replace with your actual Groq API call
    print(f"\n[Groq troubleshooting] Raw address: {raw_address}")
    print(f"Google geocode result: {json.dumps(google_result, indent=2)}")
    # Simulate Groq output
    return {"canonical_address": raw_address, "variants": [raw_address]}

def get_attom_data(street: str, city: str, state: str, zip_code: str) -> dict:
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
    headers = {"apikey": ATTOM_API_KEY, "accept": "application/json"}
    params = {"address1": street, "address2": f"{city}, {state} {zip_code}"}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 200:
        return resp.json()
    return {}

def build_groq_property_payload(attom_data: dict, address: dict, canonical: str) -> dict:
    # Only include fields that are available, fallback to canonical address if no ATTOM data
    return {
        "property_id": attom_data.get("property_id") if attom_data else None,
        "address": attom_data.get("address") if attom_data else canonical,
        "zip_code": attom_data.get("zip_code") if attom_data else address['zip_code'],
        "avm_estimate": attom_data.get("avm", {}).get("value") if attom_data else None,
        "avm_value_change_pct_yoy": attom_data.get("avm", {}).get("valueChangePct") if attom_data else None,
        "tax_lien": attom_data.get("financialLienIndicator", False) if attom_data else None,
        "foreclosure_status": attom_data.get("foreclosureStatus") if attom_data else None,
        "auction_date": attom_data.get("auctionDate") if attom_data else None,
        "listing_status": attom_data.get("listingStatus") if attom_data else None,
        "listing_price": attom_data.get("listingPrice") if attom_data else None,
        "price_change_pct": attom_data.get("priceChangePct") if attom_data else None,
        "days_on_market": attom_data.get("daysOnMarket") if attom_data else None,
        "price_reduction": attom_data.get("priceReductionIndicator") if attom_data else None,
        "owner_type": attom_data.get("ownerType") if attom_data else None,
        "owner_absentee": (attom_data.get("mailingAddress") != attom_data.get("siteAddress")) if attom_data else None,
        "neighborhood_trend": {
            "price_trend": attom_data.get("priceTrend") if attom_data else None,
            "sales_volume_trend": attom_data.get("salesVolumeTrend") if attom_data else None
        },
        "mechanic_liens": (any(lien.get("lienType") == "Mechanic" for lien in attom_data.get("liens", [])) if attom_data and attom_data.get("liens") else False) if attom_data else None,
        "year_built": attom_data.get("yearBuilt") if attom_data else None,
        "structure_risk_flag": (attom_data.get("yearBuilt", 3000) < 1975 if attom_data and attom_data.get("yearBuilt") else False) if attom_data else None
    }

def main():
    for prop in PROPERTIES:
        raw_address = f"{prop['street']}, {prop['city']}, {prop['state']} {prop['zip_code']}"
        print(f"\nProcessing: {raw_address}")
        google_result = get_google_place(raw_address)
        canonical = None
        if google_result.get('candidates'):
            candidate = google_result['candidates'][0]
            canonical = candidate.get('formatted_address', raw_address)
        if not canonical:
            groq_result = ask_groq_for_address(raw_address, google_result)
            canonical = groq_result['canonical_address']
        # Try ATTOM with canonical address
        attom_data = get_attom_data(canonical, prop['city'], prop['state'], prop['zip_code'])
        # Build and print the payload for Groq distress analysis (even if ATTOM fails)
        payload = build_groq_property_payload(attom_data if attom_data else None, prop, canonical)
        print("\n[Payload to Groq for distress analysis]:")
        print(json.dumps(payload, indent=2))
        if not attom_data:
            print(f"ATTOM returned no data for: {canonical}")
            print("Passing to Groq for troubleshooting...")
            ask_groq_for_address(canonical, google_result)
            continue
        # Here you would call Groq for distress analysis
        # result = call_groq_distress_analysis(payload)
        # print(result)

if __name__ == "__main__":
    main() 