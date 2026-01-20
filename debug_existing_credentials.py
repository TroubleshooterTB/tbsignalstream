"""
Debug SmartAPI credentials since you already have SmartAPI access
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

print("CURRENT SMARTAPI CREDENTIALS DEBUG")
print("=" * 60)

print(f"Client Code: {creds.get('client_code')}")
print(f"API Key: {creds.get('api_key')}")
print(f"TOTP Secret: {creds.get('totp_secret', 'NOT SET')}")
print(f"Password Set: {'YES' if creds.get('password') else 'NO'}")

print(f"\nToken Status:")
print(f"JWT Token Generated At: {creds.get('token_generated_at', 'NEVER')}")
print(f"Last Login: {creds.get('last_login', 'NEVER')}")

# Check if JWT token is actually set
jwt_token = creds.get('jwt_token', '')
if jwt_token.startswith('Bearer '):
    jwt_token = jwt_token[7:]  # Remove Bearer prefix

print(f"JWT Token Length: {len(jwt_token) if jwt_token else 0} chars")
print(f"Refresh Token Length: {len(creds.get('refresh_token', '')) if creds.get('refresh_token') else 0} chars")

print(f"\n{'='*60}")
print("POTENTIAL ISSUES:")
print("1. JWT tokens expire daily - may need refresh")
print("2. SmartAPI may have changed authentication requirements") 
print("3. IP restrictions or account limitations")
print("4. API credentials may be from old/demo environment")
print(f"{'='*60}")

print(f"\nNEXT STEPS:")
print("1. Try regenerating tokens with current SmartAPI credentials")
print("2. Check if SmartAPI login works on their website")
print("3. Verify API key is for production (not demo/sandbox)")
print("4. Test with minimal API call to isolate issue")