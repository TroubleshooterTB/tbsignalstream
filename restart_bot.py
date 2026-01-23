#!/usr/bin/env python3
"""
Restart Bot to Pick Up New Deployment
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys

print("=" * 80)
print("RESTARTING BOT TO PICK UP NEW DEPLOYMENT")
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

# Find active bot
bot_configs = list(db.collection('bot_configs').stream())
active_user = None

for doc in bot_configs:
    data = doc.to_dict()
    if data.get('is_running') == True or data.get('status') == 'running':
        active_user = doc.id
        break

if not active_user:
    print("❌ No active bot found!")
    print("\n👉 Please start the bot from the dashboard")
    sys.exit(1)

print(f"Found active bot for user: {active_user}")
print("\nStopping bot to force reload of new code...")

# Stop the bot
db.collection('bot_configs').document(active_user).update({
    'status': 'stopped',
    'is_running': False,
    'stopped_at': firestore.SERVER_TIMESTAMP,
    'updated_at': firestore.SERVER_TIMESTAMP,
    'restart_required': True
})

print("✅ Bot stopped")
print("\n" + "=" * 80)
print("BOT STOPPED - ACTION REQUIRED")
print("=" * 80)
print("\n🔄 The bot has been stopped to pick up the new deployment.")
print("\n👉 NEXT STEPS:")
print("   1. Go to your dashboard: https://studio--tbsignalstream.us-central1.hosted.app/")
print("   2. Click 'Start Trading Bot'")
print("   3. The bot will now use the NEW fixed code")
print("   4. Activity feed will start populating immediately!")
print("\n" + "=" * 80)
