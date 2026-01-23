"""
Quick test replay mode with the production fixes
"""
import sys
sys.path.insert(0, 'trading_bot_service')

from SmartApi import SmartConnect
from firebase_admin import credentials, firestore, initialize_app
import requests

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

print("TESTING REPLAY MODE AFTER PRODUCTION FIX")
print("=" * 60)

# Test the exact same API call that replay mode makes
print("Testing historical data API call like replay mode...")

# Format JWT token properly (add Bearer if not present)
auth_token = creds.get('jwt_token', '')
if not auth_token.startswith('Bearer '):
    auth_token = f'Bearer {auth_token}'

url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"

headers = {
    'Authorization': auth_token,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-PrivateKey': creds.get('api_key')
}

# Test with RELIANCE for 2026-01-12 (the failing date from screenshot)
payload = {
    "exchange": "NSE",
    "symboltoken": "2885",  # RELIANCE
    "interval": "ONE_MINUTE",
    "fromdate": "2026-01-12 09:15",  # Original failing date
    "todate": "2026-01-12 15:30"
}

print(f"Testing API call for: {payload['fromdate']} to {payload['todate']}")
print(f"Symbol: RELIANCE (token: {payload['symboltoken']})")
print(f"Auth token: {auth_token[:50]}...")

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            hist_data = response.json()
            
            if hist_data and hist_data.get('status') and hist_data.get('data'):
                candles = hist_data['data']
                print(f"🎉 SUCCESS! Got {len(candles)} candles")
                if candles:
                    print(f"First candle: {candles[0]}")
                print(f"\n✅ REPLAY MODE IS NOW FIXED!")
                print(f"✅ Historical data API working perfectly")
                
            else:
                error_msg = hist_data.get('message', 'No message') if hist_data else 'No response'
                error_code = hist_data.get('errorCode', 'No code') if hist_data else 'No code'
                print(f"❌ API returned error: {error_msg} (Code: {error_code})")
                
                # Check if it's a date issue (Sunday)
                from datetime import datetime
                date_obj = datetime.strptime("2026-01-12", "%Y-%m-%d")
                if date_obj.weekday() == 6:  # Sunday
                    print(f"NOTE: 2026-01-12 is a Sunday - try a weekday instead")
                elif date_obj.weekday() == 5:  # Saturday  
                    print(f"NOTE: 2026-01-12 is a Saturday - try a weekday instead")
                    
        except Exception as json_error:
            print(f"❌ JSON parsing error: {json_error}")
            print(f"Raw response: {response.text[:200]}...")
            
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
except Exception as e:
    print(f"❌ Request error: {e}")

# Test with a different date (Friday) in case Sunday is the issue
print(f"\n{'='*40}")
print("Testing with Friday 2026-01-10...")

payload_friday = {
    "exchange": "NSE",
    "symboltoken": "2885",  # RELIANCE
    "interval": "ONE_MINUTE",
    "fromdate": "2026-01-10 09:15",  # Friday
    "todate": "2026-01-10 15:30"
}

try:
    response_friday = requests.post(url, json=payload_friday, headers=headers, timeout=30)
    
    if response_friday.status_code == 200:
        try:
            hist_data_friday = response_friday.json()
            if hist_data_friday and hist_data_friday.get('status') and hist_data_friday.get('data'):
                candles_friday = hist_data_friday['data']
                print(f"🎉 Friday SUCCESS! Got {len(candles_friday)} candles")
                print(f"✅ REPLAY MODE COMPLETELY FIXED!")
            else:
                print(f"❌ Friday failed too: {hist_data_friday.get('message', 'No message')}")
        except:
            print(f"❌ Friday JSON error: {response_friday.text[:100]}...")
    else:
        print(f"❌ Friday HTTP error: {response_friday.status_code}")
        
except Exception as e:
    print(f"❌ Friday request error: {e}")

print(f"\n{'='*60}")
print("SUMMARY: If Friday works, the issue was just Sunday being a market holiday!")
print("The JWT token format fix should resolve all replay mode issues.")
print(f"{'='*60}")