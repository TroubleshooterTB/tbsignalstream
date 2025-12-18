"""List all credential fields"""
import firebase_admin
from firebase_admin import firestore

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()
doc = list(db.collection('angel_one_credentials').limit(1).get())[0].to_dict()

print("All fields in angel_one_credentials:")
print("="*60)
for key, value in doc.items():
    if 'pass' in key.lower() or 'secret' in key.lower() or 'key' in key.lower():
        print(f"{key}: *** (hidden)")
    else:
        print(f"{key}: {value}")
