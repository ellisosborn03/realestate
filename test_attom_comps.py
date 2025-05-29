import os
import requests
from dotenv import load_dotenv

load_dotenv()

ATTOM_API_KEY = os.getenv('ATTOM_API_KEY')

def get_attom_property_details(address1, address2):
    """Get property details from ATTOM API."""
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
    params = {
        'address1': address1,
        'address2': address2
    }
    headers = {
        'accept': 'application/json',
        'apikey': ATTOM_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

if __name__ == '__main__':
    # Test address: 17938 Lake Azure Way, Boca Raton 33496, United States
    address1 = '17938 Lake Azure Way'
    address2 = 'Boca Raton 33496'
    
    print(f"Querying ATTOM for property details: {address1}, {address2}")
    result = get_attom_property_details(address1, address2)
    print(f"Response: {result}") 