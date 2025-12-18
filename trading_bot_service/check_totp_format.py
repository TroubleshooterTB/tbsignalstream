"""Check TOTP secret format"""
import firebase_admin
from firebase_admin import firestore

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()
doc = list(db.collection('angel_one_credentials').limit(1).get())[0].to_dict()

totp = doc.get('totp_secret', '')
print(f"TOTP Secret: '{totp}'")
print(f"Length: {len(totp)}")
print(f"Type: {type(totp)}")
print(f"ASCII only: {totp.isascii()}")

# Check if it's valid base32
valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567')
totp_chars = set(totp.upper())
invalid_chars = totp_chars - valid_chars
print(f"Invalid characters: {invalid_chars if invalid_chars else 'None - looks valid!'}")
