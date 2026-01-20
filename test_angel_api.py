"""
Test Angel One Historical API with actual request
"""
import requests
import sys
import os
sys.path.insert(0, 'trading_bot_service')

# Get credentials from Firestore
from firebase_admin import credentials, firestore, initialize_app

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

# Test API call
url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"

headers = {
    'Authorization': f'Bearer {creds["jwt_token"]}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-PrivateKey': creds["api_key"]
}

payload = {
    "exchange": "NSE",
    "symboltoken": "2885",  # RELIANCE
    "interval": "ONE_MINUTE",
    "fromdate": "2026-01-02 09:15",
    "todate": "2026-01-02 15:30"
}

print("Testing Angel One Historical API...")
print(f"URL: {url}")
print(f"Payload: {payload}")
print(f"API Key: {creds['api_key']}")
print(f"JWT Token exists: {bool(creds.get('jwt_token'))}")
print("\nMaking request...")

response = requests.post(url, json=payload, headers=headers, timeout=30)
print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    print(f"\nSuccess: {data.get('status')}")
    print(f"Message: {data.get('message')}")
    if data.get('data'):
        print(f"Candles received: {len(data['data'])}")
else:
    print(f"\nERROR: {response.status_code}")
    try:
        print(f"Error details: {response.json()}")
    except:
        print(f"Raw response: {response.text}")
