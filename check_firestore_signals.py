#!/usr/bin/env python3
"""Check Firestore for any trading signals"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys

# Initialize Firebase
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

# Query all trading signals
print("=" * 80)
print("CHECKING FIRESTORE FOR TRADING SIGNALS")
print("=" * 80)

# Check all signals (regardless of status)
all_signals = list(db.collection('trading_signals').limit(50).stream())
print(f"\n📊 TOTAL SIGNALS IN DATABASE: {len(all_signals)}")

if all_signals:
    print("\n" + "-" * 80)
    for idx, doc in enumerate(all_signals, 1):
        data = doc.to_dict()
        print(f"\n{idx}. Document ID: {doc.id}")
        print(f"   Symbol: {data.get('symbol', 'N/A')}")
        print(f"   Type: {data.get('type', 'N/A')}")
        print(f"   Status: {data.get('status', 'N/A')}")
        print(f"   Price: ₹{data.get('price', 0):.2f}")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"   User ID: {data.get('user_id', 'N/A')}")
    print("-" * 80)

# Check only open signals
open_signals = list(db.collection('trading_signals').where('status', '==', 'open').limit(50).stream())
print(f"\n🔓 OPEN SIGNALS: {len(open_signals)}")

if open_signals:
    print("\n" + "=" * 80)
    print("⚠️  FOUND OPEN SIGNALS (These will appear on dashboard):")
    print("=" * 80)
    for idx, doc in enumerate(open_signals, 1):
        data = doc.to_dict()
        print(f"\n{idx}. {data.get('symbol')} - {data.get('type')} @ ₹{data.get('price', 0):.2f}")
        print(f"   Document ID: {doc.id}")
        print(f"   Timestamp: {data.get('timestamp')}")
        print(f"   Signal Type: {data.get('signal_type', 'N/A')}")
        print(f"   User ID: {data.get('user_id', 'N/A')}")
else:
    print("✅ No open signals found - dashboard should be clean")

print("\n" + "=" * 80)
