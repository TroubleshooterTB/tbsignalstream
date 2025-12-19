"""
Diagnose why no trades happened on Dec 19, 2025
"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pytz

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()
ist = pytz.timezone('Asia/Kolkata')

print("=" * 80)
print("🔍 DIAGNOSING DEC 19, 2025 - NO TRADES ISSUE")
print("=" * 80)

# Check bot status
print("\n1️⃣ BOT STATUS CHECK")
print("-" * 80)
bot_status = db.collection('bot_status').stream()
for doc in bot_status:
    data = doc.to_dict()
    print(f"✅ Bot User: {doc.id}")
    print(f"   Status: {data.get('status', 'unknown')}")
    print(f"   Strategy: {data.get('strategy', 'unknown')}")
    print(f"   Mode: {data.get('mode', 'unknown')}")
    print(f"   Symbols: {data.get('symbols', 'unknown')}")
    open_pos = data.get('open_positions', [])
    print(f"   Open Positions: {len(open_pos) if isinstance(open_pos, list) else open_pos}")
    print(f"   Total Trades: {data.get('total_trades', 0)}")
    print(f"   Last Updated: {data.get('updated_at', 'N/A')}")

# Check bot activity today
print("\n2️⃣ BOT ACTIVITY TODAY")
print("-" * 80)
today_start = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
activity_ref = db.collection('bot_activity').where('timestamp', '>=', today_start).stream()
activities = list(activity_ref)

if activities:
    print(f"✅ Found {len(activities)} activity logs today")
    print("\nRecent activities:")
    for act in sorted(activities, key=lambda x: x.to_dict().get('timestamp', datetime.min), reverse=True)[:10]:
        data = act.to_dict()
        print(f"   • {data.get('timestamp', 'N/A')} - {data.get('action', 'N/A')}")
        if data.get('details'):
            print(f"     Details: {data.get('details')}")
else:
    print("❌ NO ACTIVITY LOGS TODAY")
    print("   → Bot may not have started properly")
    print("   → Check if you actually clicked 'Start Trading Bot'")

# Check signals generated today
print("\n3️⃣ SIGNALS GENERATED TODAY")
print("-" * 80)
signals_ref = db.collection('signals').where('timestamp', '>=', today_start).stream()
signals = list(signals_ref)

if signals:
    print(f"✅ Found {len(signals)} signals today")
    for sig in signals:
        data = sig.to_dict()
        print(f"\n   Signal: {data.get('symbol', 'N/A')}")
        print(f"   Strategy: {data.get('strategy', 'N/A')}")
        print(f"   Direction: {data.get('direction', 'N/A')}")
        print(f"   Entry Price: ₹{data.get('entry_price', 0):.2f}")
        print(f"   Confidence: {data.get('confidence', 0):.1f}%")
        print(f"   Time: {data.get('timestamp', 'N/A')}")
else:
    print("❌ NO SIGNALS GENERATED TODAY")
    print("\n   Possible Reasons:")
    print("   1. Alpha-Ensemble screening found NO qualified stocks")
    print("      - EMA200 filter rejected stocks")
    print("      - ADX < 20 (no trending stocks)")
    print("      - RSI overbought/oversold")
    print("      - Volume too low")
    print("   2. Market conditions didn't meet entry criteria")
    print("      - No clear breakouts")
    print("      - Nifty not trending strongly")
    print("   3. Bot configuration issue")
    print("      - Wrong symbols list")
    print("      - API connection problem")

# Check trades today
print("\n4️⃣ TRADES EXECUTED TODAY")
print("-" * 80)
trades_ref = db.collection('trades').where('entry_time', '>=', today_start).stream()
trades = list(trades_ref)

if trades:
    print(f"✅ Found {len(trades)} trades today")
    for trade in trades:
        data = trade.to_dict()
        print(f"\n   {data.get('symbol', 'N/A')} - {data.get('direction', 'N/A')}")
        print(f"   Entry: ₹{data.get('entry_price', 0):.2f} @ {data.get('entry_time', 'N/A')}")
        print(f"   Exit: ₹{data.get('exit_price', 0):.2f} @ {data.get('exit_time', 'N/A')}")
        print(f"   P&L: ₹{data.get('pnl', 0):.2f}")
else:
    print("❌ NO TRADES EXECUTED TODAY")

# Check if local bot is running
print("\n5️⃣ LOCAL BOT LOG CHECK")
print("-" * 80)
import os
log_file = "live_trading_20251219.log"
if os.path.exists(log_file):
    print(f"✅ Found log file: {log_file}")
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"   Total lines: {len(lines)}")
    print("\n   Last 20 lines:")
    for line in lines[-20:]:
        print(f"   {line.rstrip()}")
else:
    print(f"❌ No log file found: {log_file}")
    print("   → Bot may not have run locally")

print("\n" + "=" * 80)
print("📊 DIAGNOSIS SUMMARY")
print("=" * 80)

if not activities:
    print("🔴 CRITICAL: No bot activity detected")
    print("   → Bot was NOT actually running")
    print("   → Start bot from dashboard or run locally with start_bot.py")
elif not signals:
    print("🟡 WARNING: Bot running but NO signals generated")
    print("   → Market conditions didn't meet Alpha-Ensemble criteria today")
    print("   → This is NORMAL - not every day has setups")
    print("   → Consider running backtest to see if strategy logic is correct")
else:
    print("🟢 Bot generated signals but didn't trade")
    print("   → Check if order execution is working")
    print("   → Verify API credentials and permissions")

print("\n💡 NEXT STEPS:")
print("1. If no activity: Start the bot properly")
print("2. If no signals: Run backtest on Dec 19 to see if any setups existed")
print("3. If signals but no trades: Check order execution logs")
print("=" * 80)
