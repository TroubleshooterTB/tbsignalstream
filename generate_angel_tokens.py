"""
Angel One Token Generator
Generates JWT and Feed tokens by logging into Angel One API
"""

import os
import sys
import pyotp
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add trading_bot_service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'trading_bot_service'))

print("=" * 80)
print("ANGEL ONE TOKEN GENERATOR")
print("=" * 80 + "\n")

# Initialize Firestore
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    try:
        firebase_admin.get_app()
        print("[OK] Firebase already initialized")
    except ValueError:
        # Try multiple possible paths
        possible_paths = [
            "firestore-key.json",
            "../firestore-key.json",
            os.path.join(os.path.dirname(__file__), "firestore-key.json"),
            os.path.join(os.path.dirname(__file__), "..", "firestore-key.json")
        ]
        
        cred_path = None
        for path in possible_paths:
            if os.path.exists(path):
                cred_path = path
                break
        
        if not cred_path:
            print(f"[ERROR] Firestore credentials not found")
            sys.exit(1)
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print(f"[OK] Firebase initialized")
    
    db = firestore.client()
    
except Exception as e:
    print(f"[ERROR] Failed to initialize Firestore: {e}")
    sys.exit(1)

USER_ID = "default_user"

# Get Angel One credentials from Firestore
print(f"\n[LOADING] Getting Angel One credentials from Firestore...")

try:
    creds_doc = db.collection('angel_one_credentials').document(USER_ID).get()
    
    if not creds_doc.exists:
        print(f"[ERROR] No Angel One credentials found")
        print("[INFO] Run initialize_bot_firestore.py first")
        sys.exit(1)
    
    creds = creds_doc.to_dict()
    
    api_key = creds.get('api_key')
    client_code = creds.get('client_code')
    password = creds.get('password')
    totp_secret = creds.get('totp_secret')
    
    print(f"[OK] Credentials loaded")
    print(f"   API Key: {api_key}")
    print(f"   Client Code: {client_code}")
    print(f"   TOTP Secret: {'*' * len(totp_secret) if totp_secret else 'None'}")
    
    if not all([api_key, client_code, password, totp_secret]):
        print(f"[ERROR] Missing credentials in Firestore")
        sys.exit(1)
    
except Exception as e:
    print(f"[ERROR] Failed to load credentials: {e}")
    sys.exit(1)

# Import SmartAPI
print(f"\n[IMPORT] Importing SmartAPI...")

try:
    from SmartApi import SmartConnect
    print("[OK] SmartAPI imported")
except Exception as e:
    print(f"[ERROR] Failed to import SmartAPI: {e}")
    print("[INFO] Install: pip install smartapi-python")
    sys.exit(1)

# Generate TOTP
print(f"\n[TOTP] Generating TOTP token...")

try:
    totp = pyotp.TOTP(totp_secret)
    totp_token = totp.now()
    print(f"[OK] TOTP generated: {totp_token}")
except Exception as e:
    print(f"[ERROR] Failed to generate TOTP: {e}")
    sys.exit(1)

# Login to Angel One
print(f"\n[LOGIN] Logging into Angel One...")

try:
    smart_api = SmartConnect(api_key=api_key)
    
    login_data = smart_api.generateSession(
        clientCode=client_code,
        password=password,
        totp=totp_token
    )
    
    if not login_data or login_data.get('status') == False:
        error_msg = login_data.get('message', 'Unknown error') if login_data else 'No response'
        print(f"[ERROR] Login failed: {error_msg}")
        sys.exit(1)
    
    jwt_token = login_data['data']['jwtToken']
    refresh_token = login_data['data']['refreshToken'] 
    feed_token = login_data['data']['feedToken']
    
    # Remove Bearer prefix if present (SmartAPI SDK doesn't need it)
    if jwt_token.startswith('Bearer '):
        jwt_token = jwt_token[7:]
    
    print(f"[OK] Login successful!")
    print(f"   JWT Token: {jwt_token[:20]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...")
    print(f"   Feed Token: {feed_token[:20]}...")
    
except Exception as e:
    print(f"[ERROR] Login failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Save tokens to Firestore
print(f"\n[SAVE] Saving tokens to Firestore...")

try:
    db.collection('angel_one_credentials').document(USER_ID).update({
        'jwt_token': jwt_token,
        'refresh_token': refresh_token,
        'feed_token': feed_token,
        'token_generated_at': datetime.now().isoformat(),
        'last_login': datetime.now().isoformat()
    })
    
    print(f"[OK] Tokens saved to Firestore")
    
    # Log to activity feed
    db.collection('activity_feed').add({
        'user_id': USER_ID,
        'timestamp': datetime.now(),
        'type': 'BROKER_CONNECTED',
        'message': 'Angel One tokens generated successfully',
        'details': {
            'client_code': client_code,
            'totp_used': totp_token
        }
    })
    
    print(f"[OK] Activity logged: BROKER_CONNECTED")
    
except Exception as e:
    print(f"[ERROR] Failed to save tokens: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("SUCCESS - Tokens generated and saved!")
print("=" * 80)
print("\nYou can now start the bot with: python start_bot_locally_fixed.py")
print("\nNote: These tokens expire daily. Re-run this script each day.")
