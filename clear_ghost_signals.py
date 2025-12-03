#!/usr/bin/env python3
"""
GHOST SIGNAL ELIMINATOR
Deletes all trading_signals from Firestore to ensure clean state
"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase Admin
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'tbsignalstream',
})

db = firestore.client()

print("=" * 60)
print("GHOST SIGNAL ELIMINATOR")
print("=" * 60)

# Delete ALL trading_signals
signals_ref = db.collection('trading_signals')
signals = signals_ref.stream()

deleted_count = 0
for signal in signals:
    print(f"Deleting signal: {signal.id} - {signal.to_dict().get('symbol', 'Unknown')}")
    signal.reference.delete()
    deleted_count += 1

print(f"\n✅ Deleted {deleted_count} signals from Firestore")
print("=" * 60)
