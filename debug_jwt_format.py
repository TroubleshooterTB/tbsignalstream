"""
Debug JWT token format - check if Bearer prefix issue
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

print("JWT TOKEN FORMAT DEBUG")
print("=" * 60)

jwt_raw = creds.get('jwt_token', '')
print(f"Raw JWT from Firestore: '{jwt_raw[:50]}...'")
print(f"Starts with 'Bearer ': {jwt_raw.startswith('Bearer ')}")
print(f"Length: {len(jwt_raw)}")

# Test both with and without Bearer prefix
jwt_clean = jwt_raw.replace('Bearer ', '') if jwt_raw.startswith('Bearer ') else jwt_raw

print(f"\nCleaned JWT: '{jwt_clean[:50]}...'")
print(f"Cleaned length: {len(jwt_clean)}")

# Test with SmartAPI SDK using clean token
print(f"\n{'='*40}")
print("Testing with CLEAN JWT token...")

smart_api = SmartConnect(api_key=creds['api_key'])
smart_api.setAccessToken(jwt_clean)  # Use clean token without Bearer
smart_api.setRefreshToken(creds['refresh_token'])

try:
    profile = smart_api.getProfile(creds['refresh_token'])
    print(f"Clean JWT Profile result: {profile}")
except Exception as e:
    print(f"Clean JWT error: {e}")

# Test with Bearer prefix explicitly
print(f"\n{'='*40}")
print("Testing with BEARER prefix...")

smart_api2 = SmartConnect(api_key=creds['api_key'])
smart_api2.setAccessToken(f"Bearer {jwt_clean}")
smart_api2.setRefreshToken(creds['refresh_token'])

try:
    profile2 = smart_api2.getProfile(creds['refresh_token'])
    print(f"Bearer JWT Profile result: {profile2}")
except Exception as e:
    print(f"Bearer JWT error: {e}")

# Manual token validation
print(f"\n{'='*40}")
print("Manual token parts analysis...")

try:
    import base64
    import json
    
    # Decode JWT payload (second part)
    jwt_parts = jwt_clean.split('.')
    if len(jwt_parts) >= 2:
        # Add padding if needed
        payload_part = jwt_parts[1]
        padding = 4 - (len(payload_part) % 4)
        if padding != 4:
            payload_part += '=' * padding
            
        decoded = base64.b64decode(payload_part)
        payload = json.loads(decoded)
        
        print(f"JWT Username: {payload.get('username')}")
        print(f"JWT Expiry: {payload.get('exp')}")
        print(f"JWT Issued: {payload.get('iat')}")
        
        # Check expiry
        import time
        current_time = time.time()
        expires_at = payload.get('exp', 0)
        
        print(f"Current timestamp: {current_time}")
        print(f"Token expires at: {expires_at}")
        print(f"Token valid: {current_time < expires_at}")
        
except Exception as e:
    print(f"Token decode error: {e}")

print(f"\n{'='*60}")
print("If token is valid but APIs fail, it might be:")
print("1. SmartAPI SDK version issue")
print("2. Account suspension or restriction") 
print("3. API endpoint changes")
print("4. Missing required headers")
print(f"{'='*60}")