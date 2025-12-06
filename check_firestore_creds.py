#!/usr/bin/env python3
"""Check Firestore credentials for debugging."""

from google.cloud import firestore
import json

db = firestore.Client(database="(default)")
user_id = "PiRehqxZQleR8QCZG0QczmQTY402"

doc_ref = db.collection('angel_one_credentials').document(user_id)
doc = doc_ref.get()

if doc.exists:
    data = doc.to_dict()
    print(f"✅ Document found for user: {user_id}\n")
    print("Fields in document:")
    for key, value in data.items():
        if key == 'api_key':
            print(f"  ✅ {key}: {value[:4]}...{value[-4:] if len(value) > 8 else value}")
        elif key in ['jwt_token', 'feed_token', 'refresh_token']:
            print(f"  ✅ {key}: {value[:10]}..." if value else f"  ❌ {key}: (empty)")
        else:
            print(f"  ✅ {key}: {value}")
    
    print("\nRequired fields check:")
    required = ['api_key', 'client_code', 'jwt_token', 'feed_token']
    missing = [f for f in required if f not in data or not data.get(f)]
    if missing:
        print(f"  ❌ MISSING: {', '.join(missing)}")
    else:
        print("  ✅ All required fields present!")
else:
    print(f"❌ Document not found for user: {user_id}")
