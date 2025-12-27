import firebase_admin
from firebase_admin import credentials, firestore
import sys

# Initialize Firebase
try:
    cred = credentials.Certificate('firestore-key.json')
    firebase_admin.initialize_app(cred)
except:
    pass  # Already initialized

db = firestore.client()

# Get your user ID from environment or hardcode temporarily
# You can get this from the Firebase Console or from the dashboard
print("Checking bot status...")

# List all bot_configs to find active bots
configs = db.collection('bot_configs').stream()

print("\n=== BOT CONFIGS ===")
for config in configs:
    data = config.to_dict()
    print(f"\nUser ID: {config.id}")
    print(f"Status: {data.get('status', 'N/A')}")
    print(f"Mode: {data.get('trading_mode', 'N/A')}")
    print(f"Replay Mode: {data.get('replay_mode', False)}")
    print(f"Error: {data.get('error_message', 'None')}")

# Check recent activities
print("\n=== RECENT BOT ACTIVITIES (Last 10) ===")
activities = db.collection('bot_activities').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()

activity_count = 0
for activity in activities:
    activity_count += 1
    data = activity.to_dict()
    print(f"\n{activity_count}. Type: {data.get('type', 'N/A')}")
    print(f"   Message: {data.get('message', 'N/A')}")
    print(f"   User: {data.get('user_id', 'N/A')[:10]}...")
    print(f"   Time: {data.get('timestamp', 'N/A')}")

if activity_count == 0:
    print("No activities found!")

print("\n=== DONE ===")
