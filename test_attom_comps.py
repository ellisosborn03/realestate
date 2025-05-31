import requests

ATTOM_API_KEY = "ad91f2f30426f1ee54aec35791aaa044"

def get_attom_avm(address1, address2):
    """Get AVM details from ATTOM API."""
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
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
    test_addresses = [
        ('19943 DEAN DR', 'BOCA RATON, FL 33434'),
        ('4888 KIRKWOOD ROAD', 'LAKE WORTH, FL 33461'),
        ('5933 AZALEA CIR', 'West Palm Beach, FL 33415'),
        ('6775 TURTLE POINT DR', 'Lake Worth, FL 33467')
    ]
    
    for address1, address2 in test_addresses:
        print(f"\nQuerying ATTOM for AVM details: {address1}, {address2}")
        result = get_attom_avm(address1, address2)
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            prop = (result.get("property") or [{}])[0]
            avm = prop.get("avm", {})
            value = avm.get("amount", {}).get("value", "N/A")
            confidence = avm.get("confidenceScore", "N/A")
            last_updated = avm.get("lastUpdated", "N/A")
            print(f"Value: {value}")
            print(f"Confidence: {confidence}")
            print(f"Last Updated: {last_updated}") 