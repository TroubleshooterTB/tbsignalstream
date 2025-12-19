"""
Comprehensive diagnostic to understand why the bot hasn't placed any trades
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from google.cloud import firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("🔍 BOT DIAGNOSTIC - Why No Trades?")
print("="*80)

# Initialize Firestore
try:
    db = firestore.Client()
    print("✅ Firestore connection established")
except Exception as e:
    print(f"❌ Firestore connection failed: {e}")
    sys.exit(1)

print("\n" + "-"*80)
print("📊 CHECKING BOT STATUS & CONFIGURATION")
print("-"*80)

# Check bot status collection
try:
    bot_status_ref = db.collection('bot_status')
    bot_status_docs = list(bot_status_ref.limit(10).stream())
    
    if not bot_status_docs:
        print("❌ NO BOT STATUS DOCUMENTS FOUND")
        print("   → Bot may have never been started from dashboard")
    else:
        print(f"✅ Found {len(bot_status_docs)} bot status document(s)")
        for doc in bot_status_docs:
            data = doc.to_dict()
            print(f"\n   Bot ID: {doc.id}")
            print(f"   User: {data.get('user_id', 'N/A')}")
            print(f"   Running: {data.get('is_running', False)}")
            print(f"   Last Updated: {data.get('last_updated', 'N/A')}")
            print(f"   Strategy: {data.get('strategy', 'N/A')}")
            print(f"   Mode: {data.get('mode', 'N/A')}")
            print(f"   Symbols: {data.get('symbols', [])}")
except Exception as e:
    print(f"❌ Error checking bot status: {e}")

print("\n" + "-"*80)
print("📈 CHECKING SIGNALS GENERATED")
print("-"*80)

# Check signals collection
try:
    # Check last 7 days
    since = datetime.now() - timedelta(days=7)
    
    signals_ref = db.collection('signals').where('timestamp', '>=', since).limit(100)
    signals = list(signals_ref.stream())
    
    print(f"✅ Found {len(signals)} signals in last 7 days")
    
    if len(signals) == 0:
        print("\n❌ NO SIGNALS GENERATED!")
        print("   Possible reasons:")
        print("   1. Bot is not running")
        print("   2. Market conditions don't match strategy criteria")
        print("   3. Pattern Detector or Ironclad not finding setups")
        print("   4. Filters are too strict")
    else:
        # Group by symbol
        by_symbol = {}
        for sig in signals:
            data = sig.to_dict()
            symbol = data.get('symbol', 'Unknown')
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
        
        print("\n   Signals by symbol:")
        for symbol, count in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {symbol}: {count} signals")
            
        # Check most recent signal
        recent_signals = sorted(signals, key=lambda s: s.to_dict().get('timestamp', datetime.min), reverse=True)[:3]
        print("\n   Most recent signals:")
        for sig in recent_signals:
            data = sig.to_dict()
            print(f"   • {data.get('symbol', 'N/A')} @ {data.get('timestamp', 'N/A')}")
            print(f"     Pattern: {data.get('pattern_type', 'N/A')}")
            print(f"     Confidence: {data.get('confidence', 0):.1f}%")
            print(f"     Entry: ₹{data.get('entry_price', 0):.2f}")
            
except Exception as e:
    print(f"❌ Error checking signals: {e}")

print("\n" + "-"*80)
print("📝 CHECKING TRADES EXECUTED")
print("-"*80)

# Check trades collection
try:
    since = datetime.now() - timedelta(days=7)
    
    trades_ref = db.collection('trades').where('entry_time', '>=', since).limit(100)
    trades = list(trades_ref.stream())
    
    print(f"✅ Found {len(trades)} trades in last 7 days")
    
    if len(trades) == 0:
        print("\n❌ NO TRADES EXECUTED!")
        print("   Possible reasons:")
        print("   1. No signals being generated (check above)")
        print("   2. Signals generated but not converted to orders")
        print("   3. Order placement failing")
        print("   4. Risk management blocking trades")
    else:
        # Analyze trades
        paper_trades = sum(1 for t in trades if t.to_dict().get('mode', '') == 'paper')
        live_trades = sum(1 for t in trades if t.to_dict().get('mode', '') == 'live')
        
        print(f"\n   Paper Trades: {paper_trades}")
        print(f"   Live Trades: {live_trades}")
        
        # Show recent trades
        recent_trades = sorted(trades, key=lambda t: t.to_dict().get('entry_time', datetime.min), reverse=True)[:3]
        print("\n   Most recent trades:")
        for trade in recent_trades:
            data = trade.to_dict()
            print(f"   • {data.get('symbol', 'N/A')} @ {data.get('entry_time', 'N/A')}")
            print(f"     Mode: {data.get('mode', 'N/A')}")
            print(f"     Entry: ₹{data.get('entry_price', 0):.2f}")
            print(f"     Status: {data.get('status', 'N/A')}")
            
except Exception as e:
    print(f"❌ Error checking trades: {e}")

print("\n" + "-"*80)
print("🔌 CHECKING WEBSOCKET STATUS")
print("-"*80)

# Check WebSocket status
try:
    ws_status_ref = db.collection('websocket_status')
    ws_docs = list(ws_status_ref.limit(10).stream())
    
    if not ws_docs:
        print("❌ NO WEBSOCKET STATUS DOCUMENTS")
        print("   → WebSocket may not be initialized")
    else:
        print(f"✅ Found {len(ws_docs)} WebSocket status document(s)")
        for doc in ws_docs:
            data = doc.to_dict()
            print(f"\n   WS ID: {doc.id}")
            print(f"   Connected: {data.get('connected', False)}")
            print(f"   Last Heartbeat: {data.get('last_heartbeat', 'N/A')}")
            print(f"   Subscribed Symbols: {len(data.get('subscribed_symbols', []))}")
            
except Exception as e:
    print(f"❌ Error checking WebSocket status: {e}")

print("\n" + "-"*80)
print("🔐 CHECKING BROKER CONNECTION")
print("-"*80)

# Check user profiles for Angel One connection
try:
    users_ref = db.collection('users')
    users = list(users_ref.limit(10).stream())
    
    if not users:
        print("❌ NO USER DOCUMENTS FOUND")
    else:
        for user_doc in users:
            data = user_doc.to_dict()
            print(f"\n   User: {data.get('email', 'N/A')}")
            
            # Check Angel One connection
            angel_data = data.get('angelone', {})
            if not angel_data:
                print("   ❌ No Angel One connection data")
                continue
                
            print(f"   Angel One Connected: {'✅' if angel_data.get('connected') else '❌'}")
            print(f"   Client Code: {angel_data.get('clientCode', 'N/A')}")
            print(f"   Last Login: {angel_data.get('lastLogin', 'N/A')}")
            
            # Check session expiry
            last_login = angel_data.get('lastLogin')
            if last_login:
                if isinstance(last_login, str):
                    try:
                        last_login = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                    except:
                        pass
                        
                if isinstance(last_login, datetime):
                    hours_since = (datetime.now() - last_login.replace(tzinfo=None)).total_seconds() / 3600
                    print(f"   Hours Since Login: {hours_since:.1f}h")
                    
                    if hours_since > 24:
                        print("   ⚠️ SESSION LIKELY EXPIRED! Re-login required.")
                    elif hours_since > 12:
                        print("   ⚠️ Session may expire soon")
                    else:
                        print("   ✅ Session should be active")
            
except Exception as e:
    print(f"❌ Error checking broker connection: {e}")

print("\n" + "-"*80)
print("📋 CHECKING ACTIVITY LOGS")
print("-"*80)

# Check activity feed
try:
    since = datetime.now() - timedelta(days=1)  # Last 24 hours
    
    activity_ref = db.collection('bot_activity').where('timestamp', '>=', since).limit(50)
    activities = list(activity_ref.stream())
    
    print(f"✅ Found {len(activities)} activity logs in last 24 hours")
    
    if len(activities) == 0:
        print("\n❌ NO BOT ACTIVITY IN LAST 24 HOURS!")
        print("   → Bot is likely not running or not processing data")
    else:
        # Count by type
        by_type = {}
        for act in activities:
            data = act.to_dict()
            act_type = data.get('activity_type', 'Unknown')
            by_type[act_type] = by_type.get(act_type, 0) + 1
        
        print("\n   Activity by type:")
        for act_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {act_type}: {count}")
            
        # Show recent activities
        recent_activities = sorted(activities, key=lambda a: a.to_dict().get('timestamp', datetime.min), reverse=True)[:5]
        print("\n   Most recent activities:")
        for act in recent_activities:
            data = act.to_dict()
            print(f"   • [{data.get('activity_type', 'N/A')}] {data.get('message', 'N/A')}")
            print(f"     @ {data.get('timestamp', 'N/A')}")
            
except Exception as e:
    print(f"❌ Error checking activity logs: {e}")

print("\n" + "="*80)
print("💡 DIAGNOSIS SUMMARY")
print("="*80)

# Provide diagnosis
diagnosis = []

# Check if bot is running
if not bot_status_docs or not any(doc.to_dict().get('is_running', False) for doc in bot_status_docs):
    diagnosis.append("❌ BOT IS NOT RUNNING - Start bot from dashboard")

# Check if signals are being generated
if 'signals' in locals() and len(signals) == 0:
    diagnosis.append("❌ NO SIGNALS GENERATED - Market conditions may not match strategy, or filters too strict")

# Check if WebSocket is connected
if not ws_docs or not any(doc.to_dict().get('connected', False) for doc in ws_docs):
    diagnosis.append("⚠️ WEBSOCKET NOT CONNECTED - May not receive real-time data")

# Check broker session
if 'users' in locals():
    for user_doc in users:
        angel_data = user_doc.to_dict().get('angelone', {})
        last_login = angel_data.get('lastLogin')
        if last_login and isinstance(last_login, datetime):
            hours_since = (datetime.now() - last_login.replace(tzinfo=None)).total_seconds() / 3600
            if hours_since > 24:
                diagnosis.append("❌ BROKER SESSION EXPIRED - Re-login to Angel One required")

# Check activity
if 'activities' in locals() and len(activities) == 0:
    diagnosis.append("❌ NO BOT ACTIVITY - Bot not processing data")

if not diagnosis:
    diagnosis.append("✅ System appears healthy - May be waiting for valid trade signals")

print()
for issue in diagnosis:
    print(f"   {issue}")

print("\n" + "="*80)
print("🔧 RECOMMENDED ACTIONS:")
print("="*80)

print("""
1. CHECK BOT STATUS:
   → Go to dashboard and verify bot is showing as "Running"
   → If not, click "Start Bot"

2. CHECK BROKER CONNECTION:
   → Go to Angel One connection page
   → Re-login if session has expired (>24 hours)
   → Verify green "Connected" status

3. CHECK WEBSOCKET:
   → Dashboard should show "WebSocket Connected"
   → If not, click "Connect WebSocket"

4. CHECK STRATEGY SETTINGS:
   → Verify correct strategy is selected (Alpha-Ensemble recommended)
   → Check that symbols list is not empty
   → Ensure paper/live mode is set correctly

5. MONITOR ACTIVITY FEED:
   → Activity feed should show bot is scanning symbols
   → Look for "Pattern detected" or "Signal generated" messages
   → If no activity, bot may not be running

6. CHECK MARKET HOURS:
   → Bot only trades during 9:15 AM - 3:30 PM IST
   → Outside market hours, bot is idle

7. VERIFY FIRESTORE RULES:
   → Ensure user has read/write permissions
   → Check browser console for permission errors
""")

print("="*80)
print()
