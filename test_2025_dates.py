"""
Test with recent dates in 2025 (known to work) and check if 2026 dates work
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

smart_api = SmartConnect(api_key=creds['api_key'])
smart_api.setAccessToken(creds['jwt_token'])
smart_api.setRefreshToken(creds['refresh_token'])

# Test with dates we KNOW had trading (recent December 2025)
test_dates = [
    ("2025-12-30", "Monday - Last trading day of 2025"),
    ("2025-12-27", "Friday - Recent trading day"), 
    ("2025-12-26", "Thursday - Day after Christmas"),
    ("2026-01-03", "Friday - First Friday of 2026"),
    ("2026-01-06", "Monday - First Monday of 2026"),
    ("2026-01-02", "Thursday - User's date"),
]

for test_date, description in test_dates:
    print(f"\n{'='*80}")
    print(f"Testing: {test_date} ({description})")
    print(f"{'='*80}")
    
    # Use a known valid token first - let's search for current tokens
    historicParam = {
        "exchange": "NSE",
        "symboltoken": "2885",  # RELIANCE - let's keep testing this
        "interval": "ONE_MINUTE", 
        "fromdate": f"{test_date} 09:15",
        "todate": f"{test_date} 10:00"  # Smaller window
    }
    
    try:
        response = smart_api.getCandleData(historicParam)
        
        if response.get('status') or response.get('success'):
            data = response.get('data', [])
            print(f"✅ SUCCESS: {len(data)} candles received")
            if data and len(data) > 0:
                print(f"   Sample candle: {data[0]}")
                break  # Found a working date!
        else:
            print(f"❌ FAILED: {response.get('message')} (Code: {response.get('errorCode')})")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

# Let's also test getting the current instrument list to check token validity
print(f"\n{'='*80}")
print("Testing instrument download...")
print(f"{'='*80}")

try:
    # Get market data for NIFTY 50 index (known token)
    ltp_data = {
        "exchange": "NSE",
        "tradingsymbol": "NIFTY-I",
        "symboltoken": "99926000"
    }
    
    response = smart_api.ltpData(ltp_data)
    print(f"LTP Data response: {response}")
    
except Exception as e:
    print(f"LTP Error: {e}")