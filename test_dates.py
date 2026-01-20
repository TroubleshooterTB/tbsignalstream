"""
Check if date is valid and test with a recent known trading day
"""
import sys
from datetime import datetime, timedelta
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

# Test with different dates - yesterday and last week
test_dates = [
    "2026-01-20",  # Yesterday (Monday)
    "2026-01-17",  # Last Friday
    "2026-01-16",  # Last Thursday
    "2026-01-02",  # User's date
]

for test_date in test_dates:
    dt = datetime.strptime(test_date, '%Y-%m-%d')
    day_name = dt.strftime('%A')
    
    historicParam = {
        "exchange": "NSE",
        "symboltoken": "2885",  # RELIANCE
        "interval": "ONE_MINUTE",
        "fromdate": f"{test_date} 09:15",
        "todate": f"{test_date} 15:30"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {test_date} ({day_name})")
    print(f"{'='*60}")
    
    try:
        response = smart_api.getCandleData(historicParam)
        
        if response.get('status') or response.get('success'):
            data = response.get('data', [])
            print(f"✅ SUCCESS: {len(data)} candles")
            if data:
                print(f"   First candle: {data[0]}")
        else:
            print(f"❌ FAILED: {response.get('message')} (Code: {response.get('errorCode')})")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
