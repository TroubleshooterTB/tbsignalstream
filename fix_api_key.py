"""
Quick fix script to add api_key to Firestore credentials
"""
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'tbsignalstream',
})

db = firestore.client()

# Your user ID
user_id = "PiRehqxZQleR8QCZG0QczmQTY402"

# Get API key from Secret Manager (you'll need to paste it)
api_key = input("Paste your Angel One API key (from Secret Manager): ").strip()

if not api_key:
    print("ERROR: No API key provided")
    exit(1)

# Update Firestore
try:
    doc_ref = db.collection('angel_one_credentials').document(user_id)
    doc_ref.update({
        'api_key': api_key
    })
    print(f"✅ SUCCESS: API key added to Firestore for user {user_id}")
    print("\nNow try starting the bot again from the dashboard!")
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\nTrying to set (create if not exists)...")
    try:
        doc_ref.set({
            'api_key': api_key
        }, merge=True)
        print(f"✅ SUCCESS: API key added to Firestore for user {user_id}")
        print("\nNow try starting the bot again from the dashboard!")
    except Exception as e2:
        print(f"❌ ERROR: {e2}")
