"""
Quick Firestore Verification - Test that all collections are populated
"""

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("../firestore-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

print("\n" + "=" * 80)
print("FIRESTORE VERIFICATION - Quick Status Check")
print("=" * 80 + "\n")

USER_ID = "default_user"

# Check each collection
collections = {
    'bot_config': db.collection('bot_config').document(USER_ID),
    'bot_configs': db.collection('bot_configs').document(USER_ID),
    'bot_status': db.collection('bot_status').document(USER_ID),
    'angel_one_credentials': db.collection('angel_one_credentials').document(USER_ID),
    'user_configs': db.collection('user_configs').document(USER_ID),
}

results = {}
for name, doc_ref in collections.items():
    doc = doc_ref.get()
    results[name] = doc.exists
    
    if doc.exists:
        print(f"✅ {name}: EXISTS")
        data = doc.to_dict()
        
        if name == 'bot_config':
            print(f"   - Strategy: {data.get('strategy')}")
            print(f"   - Trading Enabled: {data.get('trading_enabled')}")
            print(f"   - Symbols: {len(data.get('symbol_universe', []))}")
            print(f"   - Status: {data.get('status')}")
        
        elif name == 'bot_status':
            print(f"   - Status: {data.get('status')}")
            print(f"   - Is Running: {data.get('is_running')}")
            print(f"   - Active Positions: {data.get('active_positions')}")
        
        elif name == 'angel_one_credentials':
            print(f"   - API Key: {'SET' if data.get('api_key') else 'MISSING'}")
            print(f"   - Client Code: {data.get('client_code', 'MISSING')}")
            print(f"   - JWT Token: {'SET' if data.get('jwt_token') else 'MISSING'}")
    else:
        print(f"❌ {name}: MISSING")

# Check activity feed
print(f"\nActivity Feed:")
activities = list(db.collection('activity_feed').limit(5).stream())
print(f"   - Total entries: {len(activities)}")
for act in activities:
    act_data = act.to_dict()
    print(f"   - {act_data.get('type')}: {act_data.get('message', '')[:50]}")

# Check signals
signals = list(db.collection('signals').limit(5).stream())
print(f"\nSignals:")
print(f"   - Total recent signals: {len(signals)}")

# Check orders
orders = list(db.collection('orders').limit(5).stream())
print(f"\nOrders:")
print(f"   - Total recent orders: {len(orders)}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

all_exist = all(results.values())

if all_exist:
    print("\n✅ ALL REQUIRED COLLECTIONS POPULATED!")
    print("\nBot is configured and ready to run.")
    print("\nNext steps:")
    print("1. Start bot: python start_bot_locally.py")
    print("2. Or deploy to Cloud Run for production use")
else:
    print("\n❌ Some collections are missing!")
    print("\nRun: python initialize_bot_firestore.py")

print("\n" + "=" * 80 + "\n")
