"""
Check Angel One credentials from Firestore
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase (use default credentials if deployed, else try service account)
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app()
        print("Using default Firebase credentials")
    except:
        # Try to find service account key
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"Using service account: {cred_path}")
        else:
            print("ERROR: No Firebase credentials found")
            print("Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            exit(1)

db = firestore.client()

# Get credentials
creds_ref = db.collection('angel_one_credentials').limit(1).get()

if len(creds_ref) > 0:
    cred_doc = creds_ref[0].to_dict()
    print("\nAngel One Credentials Found:")
    print("="*60)
    print(f"API Key: {cred_doc.get('api_key', 'NOT FOUND')}")
    print(f"Client Code: {cred_doc.get('client_code', 'NOT FOUND')}")
    print(f"Password: {'***' if cred_doc.get('password') else 'NOT FOUND'}")
    print(f"TOTP Secret: {cred_doc.get('totp_secret', 'NOT FOUND')}")
    print("="*60)
    
    # Check if TOTP is valid base32
    import pyotp
    totp_secret = cred_doc.get('totp_secret', '')
    try:
        totp = pyotp.TOTP(totp_secret)
        current_token = totp.now()
        print(f"\nCurrent TOTP token: {current_token}")
        print("TOTP secret is valid!")
    except Exception as e:
        print(f"\nERROR: TOTP secret is invalid: {e}")
        print("You need to update the TOTP secret in Firestore")
else:
    print("NO credentials found in Firestore")
