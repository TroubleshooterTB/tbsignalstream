"""
Check if bot data is appearing in Firestore for dashboard
"""

import firebase_admin
from firebase_admin import firestore
from datetime import datetime

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

print("="*70)
print("DASHBOARD DATA CHECK")
print("="*70)
print()

# Check bot_status
print("📊 BOT STATUS:")
bot_status = list(db.collection('bot_status').limit(5).stream())
if bot_status:
    for doc in bot_status:
        data = doc.to_dict()
        print(f"  User: {doc.id}")
        print(f"  Status: {data.get('status')}")
        print(f"  Strategy: {data.get('strategy')}")
        print(f"  Mode: {data.get('mode')}")
        print(f"  Capital: ₹{data.get('capital', 0):,.2f}")
        print(f"  Open Positions: {data.get('open_positions', 0)}")
        print(f"  Total Trades: {data.get('total_trades', 0)}")
        print()
else:
    print("  ❌ No bot status found")
    print()

# Check bot_activity
print("📋 BOT ACTIVITY (Last 5):")
activity = list(db.collection('bot_activity').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).stream())
if activity:
    for doc in activity:
        data = doc.to_dict()
        print(f"  {data.get('action')}: {data.get('details')}")
else:
    print("  ❌ No activity found")
print()

# Check signals
print("🎯 SIGNALS (Last 5):")
signals = list(db.collection('signals').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).stream())
if signals:
    for doc in signals:
        data = doc.to_dict()
        print(f"  {data.get('symbol')} {data.get('direction')} @ ₹{data.get('entry_price', 0):.2f}")
else:
    print("  ❌ No signals found")
print()

# Check trades
print("💼 TRADES (Last 5):")
trades = list(db.collection('trades').order_by('exit_time', direction=firestore.Query.DESCENDING).limit(5).stream())
if trades:
    for doc in trades:
        data = doc.to_dict()
        pnl = data.get('pnl', 0)
        emoji = '✅' if pnl > 0 else '❌'
        print(f"  {emoji} {data.get('symbol')} {data.get('direction')}: ₹{pnl:,.2f}")
else:
    print("  ❌ No trades found")
print()

print("="*70)
print("Dashboard should now show this data!")
print("="*70)
