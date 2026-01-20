"""
Test historical data API with fresh login token
"""
import sys
import pyotp
import requests
import json
sys.path.insert(0, 'trading_bot_service')

from firebase_admin import credentials, firestore, initialize_app

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

print("TESTING HISTORICAL DATA API WITH FRESH TOKEN")
print("=" * 60)

# Step 1: Get fresh token
totp = pyotp.TOTP(creds['totp_secret'])
fresh_totp = totp.now()

login_url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
login_payload = {
    "clientcode": creds['client_code'],
    "password": creds['password'], 
    "totp": fresh_totp
}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-UserType": "USER",
    "X-SourceID": "WEB",
    "X-ClientLocalIP": "192.168.1.1",
    "X-ClientPublicIP": "106.193.147.98", 
    "X-MACAddress": "00:00:00:00:00:00",
    "X-PrivateKey": creds['api_key']
}

response = requests.post(login_url, json=login_payload, headers=headers)
login_data = response.json()

if login_data.get('status'):
    fresh_jwt = login_data['data']['jwtToken']
    print(f"✅ Got fresh JWT token: {fresh_jwt[:30]}...")
    
    # Step 2: Test historical data API
    hist_url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"
    
    hist_payload = {
        "exchange": "NSE",
        "symboltoken": "2885",  # RELIANCE
        "interval": "ONE_MINUTE", 
        "fromdate": "2026-01-17 09:15",  # Last Friday
        "todate": "2026-01-17 10:00"
    }
    
    hist_headers = {
        "Authorization": f"Bearer {fresh_jwt}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "192.168.1.1",
        "X-ClientPublicIP": "106.193.147.98",
        "X-MACAddress": "00:00:00:00:00:00",
        "X-PrivateKey": creds['api_key']
    }
    
    print(f"Testing historical data for RELIANCE on 2026-01-17...")
    print(f"URL: {hist_url}")
    print(f"Payload: {hist_payload}")
    
    try:
        hist_response = requests.post(hist_url, json=hist_payload, headers=hist_headers, timeout=30)
        
        print(f"\nHistorical Data Response:")
        print(f"Status Code: {hist_response.status_code}")
        print(f"Response: {hist_response.text[:500]}...")
        
        if hist_response.status_code == 200:
            try:
                hist_data = hist_response.json()
                if hist_data.get('status') or hist_data.get('success'):
                    candle_data = hist_data.get('data', [])
                    print(f"✅ SUCCESS! Got {len(candle_data)} candles")
                    if candle_data:
                        print(f"Sample candle: {candle_data[0]}")
                else:
                    print(f"❌ API Error: {hist_data.get('message')} (Code: {hist_data.get('errorCode')})")
            except json.JSONDecodeError:
                print("❌ Invalid JSON in historical data response")
        else:
            print(f"❌ HTTP Error: {hist_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        
    # Step 3: Test with different date (January 20, 2026 - Monday)
    print(f"\n{'='*40}")
    print("Testing with January 20, 2026 (Monday)...")
    
    hist_payload_monday = {
        "exchange": "NSE",
        "symboltoken": "2885",  # RELIANCE
        "interval": "ONE_MINUTE", 
        "fromdate": "2026-01-20 09:15",  # Yesterday (Monday)
        "todate": "2026-01-20 10:00"
    }
    
    try:
        hist_response_monday = requests.post(hist_url, json=hist_payload_monday, headers=hist_headers, timeout=30)
        
        print(f"Monday Response Status: {hist_response_monday.status_code}")
        print(f"Monday Response: {hist_response_monday.text[:300]}...")
        
        if hist_response_monday.status_code == 200:
            try:
                monday_data = hist_response_monday.json()
                if monday_data.get('status') or monday_data.get('success'):
                    monday_candles = monday_data.get('data', [])
                    print(f"✅ Monday SUCCESS! Got {len(monday_candles)} candles")
                else:
                    print(f"❌ Monday API Error: {monday_data.get('message')}")
            except:
                print("❌ Monday JSON decode error")
                
    except Exception as e:
        print(f"❌ Monday Request Error: {e}")

else:
    print(f"❌ Login failed: {login_data.get('message')}")

print(f"\n{'='*60}")
print("If historical data works now, the issue was stale tokens!")
print("If it still fails, there may be date/market hour restrictions.")
print(f"{'='*60}")