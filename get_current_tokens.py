"""
Download current symbol master data from Angel One and find RELIANCE token
"""
import sys
sys.path.insert(0, 'trading_bot_service')

from SmartApi import SmartConnect
import requests
import json
from firebase_admin import credentials, firestore, initialize_app

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

smart_api = SmartConnect(api_key=creds['api_key'])
smart_api.setAccessToken(creds['jwt_token'])

print("Getting current instrument master...")

# Method 1: Try getting through API
try:
    # Angel One provides instrument master download
    url = "https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json"
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        instruments = response.json()
        print(f"Downloaded {len(instruments)} instruments")
        
        # Find RELIANCE
        reliance_tokens = []
        for instrument in instruments:
            if ('RELIANCE' in instrument.get('name', '') or 
                'RELIANCE' in instrument.get('tradingsymbol', '')):
                reliance_tokens.append({
                    'name': instrument.get('name'),
                    'symbol': instrument.get('tradingsymbol'),
                    'token': instrument.get('token'),
                    'exchange': instrument.get('exch_seg'),
                    'lotsize': instrument.get('lotsize')
                })
        
        print(f"\nFound {len(reliance_tokens)} RELIANCE instruments:")
        for i, token_data in enumerate(reliance_tokens[:10]):  # Show first 10
            print(f"{i+1}. {token_data}")
            
        # Find the NSE cash segment RELIANCE
        nse_reliance = next((t for t in reliance_tokens if t['exchange'] == 'NSE'), None)
        if nse_reliance:
            print(f"\n🎯 NSE RELIANCE token found: {nse_reliance['token']}")
            
            # Test with this new token
            print(f"\nTesting historical data with correct token {nse_reliance['token']}...")
            historicParam = {
                "exchange": "NSE",
                "symboltoken": str(nse_reliance['token']),
                "interval": "ONE_MINUTE", 
                "fromdate": "2025-12-27 09:15",
                "todate": "2025-12-27 10:00"
            }
            
            try:
                response = smart_api.getCandleData(historicParam)
                
                if response.get('status') or response.get('success'):
                    data = response.get('data', [])
                    print(f"✅ SUCCESS with correct token! {len(data)} candles received")
                    if data and len(data) > 0:
                        print(f"   Sample candle: {data[0]}")
                else:
                    print(f"❌ Still failed: {response.get('message')} (Code: {response.get('errorCode')})")
                    
            except Exception as e:
                print(f"❌ ERROR testing new token: {e}")
        
    else:
        print(f"Failed to download instruments: HTTP {response.status_code}")
        
except Exception as e:
    print(f"Error downloading instruments: {e}")

# Method 2: Try searchScrip API with proper auth
print(f"\n{'='*60}")
print("Trying searchScrip API...")
print(f"{'='*60}")

try:
    search_result = smart_api.searchScrip("NSE", "RELIANCE")
    print(f"SearchScrip result: {search_result}")
except Exception as e:
    print(f"SearchScrip error: {e}")

# Method 3: Test LTP with proper parameters
print(f"\n{'='*60}")
print("Testing LTP data...")
print(f"{'='*60}")

try:
    # Get LTP for a known working symbol
    response = smart_api.ltpData("NSE", "RELIANCE-EQ", "2885")  # Using the old token for comparison
    print(f"LTP with old token: {response}")
except Exception as e:
    print(f"LTP error: {e}")