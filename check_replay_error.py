"""
Check Firestore for replay mode error details
"""
import os
from google.cloud import firestore

# Initialize Firestore
db = firestore.Client(project='tbsignalstream')

# Get bot config for the user (you need to replace with actual user ID)
# For now, let's list all bot configs to find the one with replay error

print("🔍 Checking bot configs for replay mode errors...")
print("=" * 80)

configs = db.collection('bot_configs').stream()

for config in configs:
    data = config.to_dict()
    user_id = config.id
    
    # Check if this has replay mode info
    if data.get('replay_mode') or data.get('replay_status') or data.get('replay_date'):
        print(f"\n👤 User: {user_id}")
        print(f"   Status: {data.get('status')}")
        print(f"   Replay Mode: {data.get('replay_mode')}")
        print(f"   Replay Status: {data.get('replay_status')}")
        print(f"   Replay Date: {data.get('replay_date')}")
        
        if data.get('error_message'):
            print(f"   ❌ Error: {data.get('error_message')}")
        
        if data.get('replay_progress') is not None:
            print(f"   Progress: {data.get('replay_progress')} / {data.get('replay_total', 0)}")

print("\n" + "=" * 80)
