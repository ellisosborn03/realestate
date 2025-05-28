import requests

# ATTOM API endpoint and headers
url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
headers = {
    "accept": "application/json",
    "apikey": "ad91f2f30426f1ee54aec35791aaa044"  # Replace with your actual API key
}

# Address to search
address = "254 Shore Court, Fort Lauderdale, Florida 33308"

# Parameters for the request
params = {
    "address1": address.split(',')[0].strip(),
    "address2": address.split(',')[1].strip()
}

# Make the request
response = requests.get(url, headers=headers, params=params)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code}")
    print(response.text)

# Fetch AVM details
url_avm = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
response_avm = requests.get(url_avm, headers=headers, params=params)

# Check if the AVM request was successful
if response_avm.status_code == 200:
    data_avm = response_avm.json()
    print(data_avm)
else:
    print(f"Error: {response_avm.status_code}")
    print(response_avm.text) 