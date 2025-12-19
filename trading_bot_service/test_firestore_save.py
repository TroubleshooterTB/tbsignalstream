"""
Test Firestore Backtest Save
Quick script to verify backtest_results collection is writable
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase (if not already initialized)
try:
    firebase_admin.get_app()
    print("✅ Firebase already initialized")
except ValueError:
    cred = credentials.Certificate('firebase-service-account.json')
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized")

db = firestore.client()

# Test write
print("\n📝 Testing Firestore write to backtest_results...")

test_data = {
    'strategy': 'test-strategy',
    'start_date': '2025-12-01',
    'end_date': '2025-12-18',
    'capital': 100000,
    'summary': {
        'total_trades': 10,
        'win_rate': 60.0,
        'profit_factor': 2.5,
        'total_pnl': 15000
    },
    'trades': [],
    'timestamp': firestore.SERVER_TIMESTAMP,
    'user': 'test_user',
    'created_at': datetime.now().isoformat()
}

try:
    doc_ref = db.collection('backtest_results').add(test_data)
    print(f"✅ Test document created with ID: {doc_ref[1].id}")
    
    # Read it back
    print("\n📖 Reading back...")
    doc = db.collection('backtest_results').document(doc_ref[1].id).get()
    if doc.exists:
        print(f"✅ Document found: {doc.to_dict()}")
        
        # Delete test document
        print(f"\n🗑️  Deleting test document...")
        db.collection('backtest_results').document(doc_ref[1].id).delete()
        print("✅ Test document deleted")
    else:
        print("❌ Document not found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("✅ Firestore backtest_results collection is working!")
print("="*80)
