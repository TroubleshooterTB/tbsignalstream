#!/usr/bin/env python3
"""
Force Stop ALL Bots - Complete Reset
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys

print("=" * 80)
print("FORCE STOPPING ALL BOT INSTANCES")
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

# Stop ALL bots
bot_configs = list(db.collection('bot_configs').stream())
stopped_count = 0

for doc in bot_configs:
    data = doc.to_dict()
    user_id = doc.id
    
    if data.get('is_running') or data.get('status') == 'running':
        print(f"Stopping bot for user: {user_id}")
        db.collection('bot_configs').document(user_id).update({
            'status': 'stopped',
            'is_running': False,
            'stopped_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'force_restart': True
        })
        stopped_count += 1

print(f"\n✅ Stopped {stopped_count} bot(s)")

# Clear all activity logs to start fresh
print("\nClearing old activity logs...")
activities = list(db.collection('bot_activity').stream())
for doc in activities:
    doc.reference.delete()
print(f"✅ Deleted {len(activities)} old activity logs")

print("\n" + "=" * 80)
print("ALL BOTS STOPPED - CLEAN SLATE")
print("=" * 80)
print("\n🔄 All bot instances have been forcefully stopped.")
print("   Old activity logs cleared.")
print("\n👉 NEXT STEPS:")
print("   1. Wait 30 seconds for containers to terminate")
print("   2. Go to: https://studio--tbsignalstream.us-central1.hosted.app/")
print("   3. Click 'Start Trading Bot'")
print("   4. New container will start with FIXED code")
print("   5. Activity feed will populate immediately!")
print("\n⏰ Current time: " + str(firestore.SERVER_TIMESTAMP))
print("=" * 80)
