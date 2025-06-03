# Usage: create a .env file in this directory with a line like:

from dotenv import load_dotenv
load_dotenv()
import os
import requests
import time

API_KEY = os.getenv("GOOGLE_API_KEY")

def get_autocomplete(address, city, state, zip_code):
    input_str = f"{address}, {city}, {state} {zip_code}"
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": input_str,
        "types": "address",
        "components": f"country:us|administrative_area:{state}",
        "key": API_KEY
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if data.get("status") == "OK" and data.get("predictions"):
        return data["predictions"][0]["description"]
    else:
        return None

addresses = [
    ("4500 PGA BLVD SUITE 303B", "PALM BEACH GARDENS", "FL", "33418"),
    # ... add the rest ...
]

for addr, city, state, zipc in addresses:
    print(f"Trying: {addr}, {city}, {state} {zipc}")
    result = get_autocomplete(addr, city, state, zipc)
    print("  →", result if result else "No match")
    time.sleep(0.2) 