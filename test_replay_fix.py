"""
Test replay mode with fresh tokens - this should work now!
"""
import sys
sys.path.insert(0, 'trading_bot_service')

from SmartApi import SmartConnect
from firebase_admin import credentials, firestore, initialize_app

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

print("TESTING REPLAY MODE WITH FRESH TOKENS")
print("=" * 60)

smart_api = SmartConnect(api_key=creds['api_key'])
smart_api.setAccessToken(creds['jwt_token'])
smart_api.setRefreshToken(creds['refresh_token'])

# Test 1: Basic profile to ensure auth works
print("1. Testing profile API...")
try:
    profile = smart_api.getProfile(creds['refresh_token'])
    if profile.get('status') or profile.get('success'):
        print(f"✅ Profile works: {profile.get('data', {}).get('name', 'Unknown')}")
    else:
        print(f"❌ Profile failed: {profile}")
except Exception as e:
    print(f"❌ Profile error: {e}")

# Test 2: Historical data for RELIANCE (the exact call that was failing)
print(f"\n2. Testing historical data (RELIANCE)...")

historicParam = {
    "exchange": "NSE",
    "symboltoken": "2885",  # RELIANCE
    "interval": "ONE_MINUTE", 
    "fromdate": "2026-01-20 09:15",  # Yesterday (Monday)
    "todate": "2026-01-20 15:30"
}

try:
    response = smart_api.getCandleData(historicParam)
    
    if response.get('status') or response.get('success'):
        data = response.get('data', [])
        print(f"✅ HISTORICAL DATA SUCCESS! Got {len(data)} candles")
        if data:
            print(f"   First candle: {data[0]}")
            print(f"   Last candle: {data[-1]}")
        print(f"\n🎉 REPLAY MODE IS FIXED! 🎉")
    else:
        print(f"❌ Historical data failed: {response.get('message')} (Code: {response.get('errorCode')})")
        
        # Try with different dates if Monday failed
        print(f"\nTrying Friday Jan 17, 2026...")
        historicParam['fromdate'] = "2026-01-17 09:15"
        historicParam['todate'] = "2026-01-17 15:30"
        
        response2 = smart_api.getCandleData(historicParam)
        if response2.get('status') or response2.get('success'):
            data2 = response2.get('data', [])
            print(f"✅ Friday data works! Got {len(data2)} candles")
        else:
            print(f"❌ Friday also failed: {response2.get('message')}")
        
except Exception as e:
    print(f"❌ Historical data error: {e}")

# Test 3: Test with multiple symbols
print(f"\n3. Testing other symbols...")

symbols_to_test = [
    ("26009", "HDFCBANK"),
    ("1594", "INFY"), 
    ("11536", "TCS")
]

for token, name in symbols_to_test:
    try:
        test_param = {
            "exchange": "NSE",
            "symboltoken": token,
            "interval": "ONE_MINUTE", 
            "fromdate": "2026-01-20 09:15",
            "todate": "2026-01-20 10:00"
        }
        
        test_response = smart_api.getCandleData(test_param)
        
        if test_response.get('status') or test_response.get('success'):
            test_data = test_response.get('data', [])
            print(f"✅ {name}: {len(test_data)} candles")
        else:
            print(f"❌ {name}: {test_response.get('message')}")
            
    except Exception as e:
        print(f"❌ {name} error: {e}")

print(f"\n{'='*60}")
print("FINAL STATUS:")
print("If historical data works = REPLAY MODE IS COMPLETELY FIXED!")
print("If still failing = May need to check trading hours or market holidays")
print(f"{'='*60}")