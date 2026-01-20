"""
Test using SmartAPI SDK instead of direct REST calls
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

print("Testing with SmartAPI SDK...")
smart_api = SmartConnect(api_key=creds['api_key'])

# Set tokens manually  
smart_api.setAccessToken(creds['jwt_token'])
smart_api.setRefreshToken(creds['refresh_token'])

print(f"Feed Token: {smart_api.getfeedToken()}")

# Try getting historical data using SDK
try:
    historicParam = {
        "exchange": "NSE",
        "symboltoken": "2885",  # RELIANCE
        "interval": "ONE_MINUTE",
        "fromdate": "2026-01-02 09:15",
        "todate": "2026-01-02 15:30"
    }
    
    print(f"\nFetching historical data with SDK...")
    print(f"Params: {historicParam}")
    
    response = smart_api.getCandleData(historicParam)
    print(f"\nSDK Response: {response}")
    
except Exception as e:
    print(f"\nSDK Error: {e}")
    import traceback
    traceback.print_exc()
