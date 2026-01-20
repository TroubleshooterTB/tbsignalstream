"""
Test basic profile and holdings API to check token permissions
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

print("Testing basic API functions to check token permissions...")
print(f"JWT Token: {creds['jwt_token'][:20]}...")
print(f"Refresh Token: {creds['refresh_token'][:20]}...")
print(f"API Key: {creds['api_key']}")

smart_api = SmartConnect(api_key=creds['api_key'])
smart_api.setAccessToken(creds['jwt_token'])
smart_api.setRefreshToken(creds['refresh_token'])

# Test 1: Profile API (basic auth test)
print(f"\n{'='*60}")
print("1. Testing Profile API...")
print(f"{'='*60}")

try:
    profile = smart_api.getProfile(creds['refresh_token'])
    print(f"✅ Profile API works: {profile}")
except Exception as e:
    print(f"❌ Profile API failed: {e}")

# Test 2: Position Book (portfolio access)
print(f"\n{'='*60}")
print("2. Testing Position Book...")
print(f"{'='*60}")

try:
    positions = smart_api.position()
    print(f"✅ Position API works: {positions}")
except Exception as e:
    print(f"❌ Position API failed: {e}")

# Test 3: Holdings (equity access)
print(f"\n{'='*60}")
print("3. Testing Holdings...")
print(f"{'='*60}")

try:
    holdings = smart_api.holding()
    print(f"✅ Holdings API works: {holdings}")
except Exception as e:
    print(f"❌ Holdings API failed: {e}")

# Test 4: Fund Book (funds access)
print(f"\n{'='*60}")
print("4. Testing Fund Book...")
print(f"{'='*60}")

try:
    funds = smart_api.rmsLimit()
    print(f"✅ Funds API works: {funds}")
except Exception as e:
    print(f"❌ Funds API failed: {e}")

# Test 5: Order Book (trading access)
print(f"\n{'='*60}")
print("5. Testing Order Book...")
print(f"{'='*60}")

try:
    orders = smart_api.orderBook()
    print(f"✅ Order Book API works: {orders}")
except Exception as e:
    print(f"❌ Order Book API failed: {e}")

# Test 6: Market depth (basic market data)
print(f"\n{'='*60}")
print("6. Testing Market Depth...")
print(f"{'='*60}")

try:
    depth = smart_api.getMarketData("NSE", "RELIANCE-EQ", "2885")
    print(f"✅ Market Depth API works: {depth}")
except Exception as e:
    print(f"❌ Market Depth API failed: {e}")

print(f"\n{'='*60}")
print("SUMMARY: Checking which APIs work and which don't...")
print("This will help identify if it's a token permission issue.")
print(f"{'='*60}")