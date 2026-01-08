#!/usr/bin/env python3
"""
Fix Bot Config and Clear Activity Feed
Resets bot config to correct state and optionally starts bot
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import sys

print("=" * 80)
print("FIX BOT CONFIG & ACTIVITY FEED")
print("=" * 80)

try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'tbsignalstream',
    })
    db = firestore.client()
    print("✅ Firebase initialized\n")
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    sys.exit(1)

# Step 1: Find the user
print("Step 1: Finding user...")
bot_configs = list(db.collection('bot_configs').stream())

if not bot_configs:
    print("❌ No bot configs found!")
    sys.exit(1)

user_doc = bot_configs[0]
user_id = user_doc.id
current_config = user_doc.to_dict()

print(f"✅ Found user: {user_id}")
print(f"   Current status: {current_config.get('status')}")
print(f"   Current is_running: {current_config.get('is_running', 'NOT SET')}")

# Step 2: Fix bot config - set to stopped state
print("\nStep 2: Resetting bot config to STOPPED state...")
try:
    db.collection('bot_configs').document(user_id).set({
        'status': 'stopped',
        'is_running': False,
        'last_stopped': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'error_message': None  # Clear any error messages
    }, merge=True)
    print("✅ Bot config reset to STOPPED")
except Exception as e:
    print(f"❌ Failed to update bot config: {e}")
    sys.exit(1)

# Step 3: Clear old activity feed (optional - uncomment if needed)
print("\nStep 3: Checking activity feed...")
activities = list(db.collection('bot_activity').where('user_id', '==', user_id).stream())
print(f"   Found {len(activities)} old activity entries")

clear_activities = input("\nClear old activities? (yes/no): ").strip().lower()
if clear_activities == 'yes':
    print("   Clearing activities...")
    for doc in activities:
        doc.reference.delete()
    print(f"   ✅ Deleted {len(activities)} old activities")
else:
    print("   Skipped clearing activities")

# Summary
print("\n" + "=" * 80)
print("COMPLETED SUCCESSFULLY")
print("=" * 80)
print("\nNext steps:")
print("1. Deploy the updated backend code to Cloud Run")
print("2. Go to the dashboard")
print("3. Click 'Start Trading Bot'")
print("4. You should now see activity feed updates in real-time!")
print("\nTo deploy:")
print("  gcloud run deploy trading-bot-service --source .")
print("\nOr use your deploy script:")
print("  .\\deploy.ps1")
print("=" * 80)
