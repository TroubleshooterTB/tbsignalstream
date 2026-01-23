"""
Check if production Firestore has the updated JWT token without Bearer prefix
"""
import sys
sys.path.insert(0, 'trading_bot_service')

from firebase_admin import credentials, firestore, initialize_app

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

print("PRODUCTION FIRESTORE TOKEN STATUS")
print("=" * 60)

jwt_token = creds.get('jwt_token', '')
refresh_token = creds.get('refresh_token', '')

print(f"JWT Token: '{jwt_token[:50]}...'")
print(f"Starts with Bearer: {jwt_token.startswith('Bearer ')}")
print(f"JWT Length: {len(jwt_token)}")
print(f"Refresh Token Length: {len(refresh_token)}")

print(f"Last token generation: {creds.get('token_generated_at', 'NEVER')}")
print(f"Last login: {creds.get('last_login', 'NEVER')}")

# Check if we need to regenerate tokens for production
from datetime import datetime
import pyotp

if jwt_token.startswith('Bearer '):
    print(f"\n❌ PROBLEM FOUND: JWT still has Bearer prefix in production!")
    print(f"Need to regenerate tokens properly...")
    
    # Generate fresh tokens without Bearer prefix
    from SmartApi import SmartConnect
    
    totp = pyotp.TOTP(creds['totp_secret'])
    totp_token = totp.now()
    
    smart_api = SmartConnect(api_key=creds['api_key'])
    
    try:
        login_data = smart_api.generateSession(
            clientCode=creds['client_code'],
            password=creds['password'],
            totp=totp_token
        )
        
        if login_data and login_data.get('status'):
            new_jwt = login_data['data']['jwtToken']
            new_refresh = login_data['data']['refreshToken']
            new_feed = login_data['data']['feedToken']
            
            # Strip Bearer prefix if present
            if new_jwt.startswith('Bearer '):
                new_jwt = new_jwt[7:]
                
            print(f"\n✅ Generated fresh tokens:")
            print(f"New JWT (clean): {new_jwt[:50]}...")
            print(f"No Bearer prefix: {not new_jwt.startswith('Bearer ')}")
            
            # Update in Firestore
            db.collection('angel_one_credentials').document('default_user').update({
                'jwt_token': new_jwt,
                'refresh_token': new_refresh,
                'feed_token': new_feed,
                'token_generated_at': datetime.now().isoformat(),
                'last_login': datetime.now().isoformat()
            })
            
            print(f"✅ Updated production Firestore with clean tokens")
            
            # Quick test
            smart_api.setAccessToken(new_jwt)
            smart_api.setRefreshToken(new_refresh)
            
            try:
                profile = smart_api.getProfile(new_refresh)
                if profile.get('status'):
                    print(f"✅ Token test successful: {profile['data']['name']}")
                else:
                    print(f"❌ Token test failed: {profile}")
            except Exception as e:
                print(f"❌ Token test error: {e}")
                
        else:
            print(f"❌ Token generation failed: {login_data}")
            
    except Exception as e:
        print(f"❌ Token generation error: {e}")
else:
    print(f"✅ JWT token format looks correct (no Bearer prefix)")
    
    # Test if current tokens work
    from SmartApi import SmartConnect
    
    smart_api = SmartConnect(api_key=creds['api_key'])
    smart_api.setAccessToken(jwt_token)
    smart_api.setRefreshToken(refresh_token)
    
    try:
        profile = smart_api.getProfile(refresh_token)
        if profile.get('status'):
            print(f"✅ Current tokens working: {profile['data']['name']}")
        else:
            print(f"❌ Current tokens failed: {profile}")
    except Exception as e:
        print(f"❌ Current tokens error: {e}")

print(f"\n{'='*60}")
print("Next: Test actual replay mode API call with production tokens")
print(f"{'='*60}")