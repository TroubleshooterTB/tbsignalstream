"""
Check token expiry and details
"""
import sys
sys.path.insert(0, 'trading_bot_service')

from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

print("Token Analysis:")
print(f"JWT Token exists: {bool(creds.get('jwt_token'))}")
print(f"JWT Token time: {creds.get('jwt_token_time')}")
print(f"Current time: {datetime.now()}")

# Try to decode JWT without verification
try:
    import jwt as pyjwt
    token = creds['jwt_token'].replace('Bearer ', '')
    token_data = pyjwt.decode(token, options={'verify_signature': False})
    exp_time = datetime.fromtimestamp(token_data['exp'])
    print(f"Token expires at: {exp_time}")
    print(f"Token is {'EXPIRED' if exp_time < datetime.now() else 'VALID'}")
    print(f"Token data: {token_data}")
except Exception as e:
    print(f"Could not decode token: {e}")

# Test a simple profile API call
print(f"\n{'='*60}")
print("Testing basic profile API...")
print(f"{'='*60}")

from SmartApi import SmartConnect

try:
    smart_api = SmartConnect(api_key=creds['api_key'])
    smart_api.setAccessToken(creds['jwt_token'])
    smart_api.setRefreshToken(creds['refresh_token'])
    
    profile = smart_api.getProfile()
    print(f"Profile API response: {profile}")
    
except Exception as e:
    print(f"Profile API error: {e}")