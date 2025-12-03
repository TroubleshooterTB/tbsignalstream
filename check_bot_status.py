#!/usr/bin/env python3
"""Check actual bot status in Firestore"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase Admin
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'tbsignalstream',
})

db = firestore.client()

# Check bot_configs for all users
print("=" * 60)
print("BOT CONFIGS IN FIRESTORE")
print("=" * 60)

bot_configs = db.collection('bot_configs').stream()
configs_found = False

for doc in bot_configs:
    configs_found = True
    data = doc.to_dict()
    print(f"\nUser: {doc.id}")
    print(f"Status: {data.get('status', 'N/A')}")
    print(f"Is Running: {data.get('is_running', False)}")
    print(f"Last Started: {data.get('last_started', 'N/A')}")
    print(f"Last Stopped: {data.get('last_stopped', 'N/A')}")
    print(f"Config: {data}")

if not configs_found:
    print("\nNo bot configs found in Firestore")

# Check angel_one_credentials
print("\n" + "=" * 60)
print("ANGEL ONE CREDENTIALS IN FIRESTORE")
print("=" * 60)

creds = db.collection('angel_one_credentials').stream()
creds_found = False

for doc in creds:
    creds_found = True
    data = doc.to_dict()
    print(f"\nUser: {doc.id}")
    print(f"Client Code: {data.get('client_code', 'N/A')}")
    print(f"Has JWT Token: {'jwt_token' in data}")
    print(f"Has Feed Token: {'feed_token' in data}")
    if 'last_login' in data:
        print(f"Last Login: {data.get('last_login', 'N/A')}")

if not creds_found:
    print("\nNo credentials found in Firestore")

print("\n" + "=" * 60)
