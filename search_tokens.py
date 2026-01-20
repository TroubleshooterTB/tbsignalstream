"""
Get current valid token for RELIANCE using searchScrip API
"""
import sys
import requests
sys.path.insert(0, 'trading_bot_service')

from firebase_admin import credentials, firestore, initialize_app

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/searchScrip"

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

test_symbols = ['RELIANCE', 'HDFCBANK', 'INFY', 'TCS']

for symbol in test_symbols:
    payload = {
        "exchange": "NSE",
        "searchscrip": symbol
    }
    
    print(f"\n{'='*60}")
    print(f"Searching for: {symbol}")
    print(f"{'='*60}")
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            for item in data['data'][:3]:  # Show first 3 results
                print(f"  Symbol: {item.get('tradingsymbol')}")
                print(f"  Token: {item.get('symboltoken')}")
                print(f"  Exchange: {item.get('exch_seg')}")
                print()
    else:
        print(f"ERROR: {response.text}")
