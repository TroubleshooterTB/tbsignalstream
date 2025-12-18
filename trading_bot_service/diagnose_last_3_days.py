"""
Extended diagnostic - Check last 3 days of bot activity
"""

import os
import sys
from datetime import datetime, timedelta
from google.cloud import firestore

db = firestore.Client()

print("\n" + "="*80)
print("🔍 EXTENDED BOT DIAGNOSTIC - Last 3 Days")
print("="*80)

# Check last 3 days instead of 7
since = datetime.now() - timedelta(days=3)

print(f"\n📅 Checking activity since: {since.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print("\n" + "-"*80)
print("📊 BOT STATUS - Last 3 Days")
print("-"*80)

try:
    bot_status_ref = db.collection('bot_status').where('last_updated', '>=', since).limit(50)
    bot_statuses = list(bot_status_ref.stream())
    
    if not bot_statuses:
        print("❌ NO BOT STATUS UPDATES in last 3 days")
        print("   → Bot UI may show 'Running' but backend never initialized")
        print("   → Possible issues:")
        print("     • Firestore permissions blocking writes")
        print("     • Bot crashed during startup")
        print("     • Frontend-backend connection issue")
    else:
        print(f"✅ Found {len(bot_statuses)} bot status update(s)")
        for doc in sorted(bot_statuses, key=lambda d: d.to_dict().get('last_updated', datetime.min), reverse=True)[:10]:
            data = doc.to_dict()
            print(f"\n   [{data.get('last_updated', 'N/A')}]")
            print(f"   User: {data.get('user_id', 'N/A')}")
            print(f"   Running: {data.get('is_running', False)}")
            print(f"   Strategy: {data.get('strategy', 'N/A')}")
            print(f"   Mode: {data.get('mode', 'N/A')}")
            print(f"   Symbols: {len(data.get('symbols', []))}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "-"*80)
print("🔌 WEBSOCKET ACTIVITY - Last 3 Days")
print("-"*80)

try:
    ws_ref = db.collection('websocket_status').where('last_heartbeat', '>=', since).limit(50)
    ws_statuses = list(ws_ref.stream())
    
    if not ws_statuses:
        print("❌ NO WEBSOCKET ACTIVITY in last 3 days")
        print("   → WebSocket never connected")
        print("   → Bot cannot receive market data without WebSocket")
    else:
        print(f"✅ Found {len(ws_statuses)} WebSocket heartbeat(s)")
        for doc in sorted(ws_statuses, key=lambda d: d.to_dict().get('last_heartbeat', datetime.min), reverse=True)[:5]:
            data = doc.to_dict()
            print(f"\n   Last Heartbeat: {data.get('last_heartbeat', 'N/A')}")
            print(f"   Connected: {data.get('connected', False)}")
            print(f"   Symbols Subscribed: {len(data.get('subscribed_symbols', []))}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "-"*80)
print("📋 ACTIVITY FEED - Last 3 Days")
print("-"*80)

try:
    activity_ref = db.collection('bot_activity').where('timestamp', '>=', since).limit(100)
    activities = list(activity_ref.stream())
    
    if not activities:
        print("❌ NO BOT ACTIVITY LOGS in last 3 days")
        print("   → Bot never logged any actions")
        print("   → This confirms bot backend is NOT running")
    else:
        print(f"✅ Found {len(activities)} activity log(s)")
        
        # Count by type
        by_type = {}
        by_date = {}
        for act in activities:
            data = act.to_dict()
            act_type = data.get('activity_type', 'Unknown')
            by_type[act_type] = by_type.get(act_type, 0) + 1
            
            # Group by date
            ts = data.get('timestamp')
            if ts:
                date_key = ts.strftime('%Y-%m-%d') if isinstance(ts, datetime) else str(ts)[:10]
                by_date[date_key] = by_date.get(date_key, 0) + 1
        
        print("\n   Activity by Type:")
        for act_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {act_type}: {count}")
        
        print("\n   Activity by Date:")
        for date, count in sorted(by_date.items(), reverse=True):
            print(f"   • {date}: {count} actions")
        
        print("\n   Most Recent 10 Activities:")
        recent = sorted(activities, key=lambda a: a.to_dict().get('timestamp', datetime.min), reverse=True)[:10]
        for act in recent:
            data = act.to_dict()
            print(f"\n   [{data.get('timestamp', 'N/A')}]")
            print(f"   Type: {data.get('activity_type', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')[:100]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "-"*80)
print("🎯 SIGNALS - Last 3 Days")
print("-"*80)

try:
    signals_ref = db.collection('signals').where('timestamp', '>=', since).limit(100)
    signals = list(signals_ref.stream())
    
    if not signals:
        print("❌ NO SIGNALS GENERATED in last 3 days")
        print("   → No trading opportunities detected")
        print("   → Possible reasons:")
        print("     • Bot not running (no data processing)")
        print("     • Filters too strict (rejecting all setups)")
        print("     • Market conditions not matching strategy")
    else:
        print(f"✅ Found {len(signals)} signal(s)")
        
        by_symbol = {}
        by_date = {}
        for sig in signals:
            data = sig.to_dict()
            symbol = data.get('symbol', 'Unknown')
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
            
            ts = data.get('timestamp')
            if ts:
                date_key = ts.strftime('%Y-%m-%d') if isinstance(ts, datetime) else str(ts)[:10]
                by_date[date_key] = by_date.get(date_key, 0) + 1
        
        print("\n   Signals by Symbol:")
        for symbol, count in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {symbol}: {count}")
        
        print("\n   Signals by Date:")
        for date, count in sorted(by_date.items(), reverse=True):
            print(f"   • {date}: {count} signals")
        
        print("\n   Most Recent 5 Signals:")
        recent = sorted(signals, key=lambda s: s.to_dict().get('timestamp', datetime.min), reverse=True)[:5]
        for sig in recent:
            data = sig.to_dict()
            print(f"\n   [{data.get('timestamp', 'N/A')}]")
            print(f"   Symbol: {data.get('symbol', 'N/A')}")
            print(f"   Pattern: {data.get('pattern_type', 'N/A')}")
            print(f"   Entry: ₹{data.get('entry_price', 0):.2f}")
            print(f"   Confidence: {data.get('confidence', 0):.1f}%")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "-"*80)
print("💼 TRADES - Last 3 Days")
print("-"*80)

try:
    trades_ref = db.collection('trades').where('entry_time', '>=', since).limit(100)
    trades = list(trades_ref.stream())
    
    if not trades:
        print("❌ NO TRADES EXECUTED in last 3 days")
    else:
        print(f"✅ Found {len(trades)} trade(s)")
        
        paper = sum(1 for t in trades if t.to_dict().get('mode') == 'paper')
        live = sum(1 for t in trades if t.to_dict().get('mode') == 'live')
        
        print(f"\n   Paper Trades: {paper}")
        print(f"   Live Trades: {live}")
        
        print("\n   Most Recent 5 Trades:")
        recent = sorted(trades, key=lambda t: t.to_dict().get('entry_time', datetime.min), reverse=True)[:5]
        for trade in recent:
            data = trade.to_dict()
            print(f"\n   [{data.get('entry_time', 'N/A')}]")
            print(f"   Symbol: {data.get('symbol', 'N/A')}")
            print(f"   Entry: ₹{data.get('entry_price', 0):.2f}")
            print(f"   Mode: {data.get('mode', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "-"*80)
print("👤 USER SESSION - Last Login")
print("-"*80)

try:
    users_ref = db.collection('users').limit(10)
    users = list(users_ref.stream())
    
    if not users:
        print("❌ NO USER DOCUMENTS")
        print("   → User authentication never completed")
    else:
        for user_doc in users:
            data = user_doc.to_dict()
            print(f"\n   User: {data.get('email', 'N/A')}")
            
            angel = data.get('angelone', {})
            if angel:
                print(f"   Angel One Connected: {angel.get('connected', False)}")
                print(f"   Last Login: {angel.get('lastLogin', 'N/A')}")
                
                last_login = angel.get('lastLogin')
                if last_login and isinstance(last_login, datetime):
                    hours_ago = (datetime.now() - last_login.replace(tzinfo=None)).total_seconds() / 3600
                    print(f"   Hours Since Login: {hours_ago:.1f}h")
                    if hours_ago > 24:
                        print("   ⚠️ SESSION EXPIRED (>24 hours)")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)
print("💡 DIAGNOSIS FOR LAST 3 DAYS")
print("="*80)

# Determine what happened
if not bot_statuses and not activities:
    print("""
❌ ROOT CAUSE: BOT BACKEND NEVER STARTED

The bot UI may show "Running" but the backend service never initialized.

CRITICAL ISSUE:
   • No bot_status documents created
   • No activity logs generated
   • No WebSocket connection established
   • Frontend and backend are disconnected

MOST LIKELY CAUSES:
   1. Firestore Security Rules blocking writes
   2. Bot startup code has bugs/crashes silently
   3. Cloud Function not deployed/not triggering
   4. Environment variables missing (credentials)

NEXT STEPS TO FIX:
   1. Check browser console (F12) for errors
   2. Check Cloud Function logs:
      gcloud functions logs read startLiveTradingBot --limit=100
   3. Verify Firestore rules allow authenticated writes
   4. Test bot locally to see actual error messages
""")

elif bot_statuses and not activities:
    print("""
⚠️ BOT STATUS CREATED BUT NO ACTIVITY

Bot successfully wrote status to Firestore but never processed data.

POSSIBLE CAUSES:
   1. WebSocket failed to connect (no market data)
   2. Bot loop crashed after initialization
   3. Symbol fetching failed (no tokens retrieved)
   4. Market was closed during runtime

CHECK:
   • WebSocket connection logs
   • Symbol token retrieval
   • Bot error logs in Cloud Functions
""")

elif activities:
    print(f"""
✅ BOT WAS ACTIVE ({len(activities)} activities logged)

Bot is/was running and processing data.

ANALYSIS:
   • Activity Logs: {len(activities)}
   • Signals Generated: {len(signals) if 'signals' in locals() else 0}
   • Trades Executed: {len(trades) if 'trades' in locals() else 0}

If signals generated but no trades:
   → Check order placement logs
   → Verify risk manager not blocking all trades
   → Check if Angel One API is rejecting orders

If no signals despite activity:
   → Filters may be too strict
   → Market conditions not matching strategy
   → Pattern detection not finding setups
""")

print("\n" + "="*80)
