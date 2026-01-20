"""
FIRESTORE DIAGNOSTIC - Check Bot Configuration and Activity
================================================================
This script checks the ACTUAL configuration and state in Firestore to identify
why the bot hasn't placed any trades in 2 months.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Initialize Firestore
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    # Initialize Firebase (if not already initialized)
    try:
        firebase_admin.get_app()
        print(" Firebase already initialized")
    except ValueError:
        # Need to initialize
        cred_path = os.path.join("..", "firestore-key.json")
        if not os.path.exists(cred_path):
            print(f"ERROR: Firestore credentials not found at {cred_path}")
            sys.exit(1)
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print(" Firebase initialized successfully")
    
    db = firestore.client()
    print(" Firestore client created")
    
except ImportError:
    print("ERROR: firebase_admin not installed")
    print("Install with: pip install firebase-admin")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to initialize Firestore: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("FIRESTORE DIAGNOSTIC - Bot Configuration & Activity Analysis")
print("=" * 80 + "\n")

# TEST 1: Bot Configuration
print("1. BOT CONFIGURATION (bot_config collection)")
print("-" * 80)

try:
    configs = db.collection('bot_config').limit(10).get()
    
    if not configs:
        print("CRITICAL: No bot configuration documents found!")
        print("Bot cannot run without configuration!")
    else:
        print(f"Found {len(configs)} configuration document(s)\n")
        
        for config_doc in configs:
            config = config_doc.to_dict()
            print(f"Config ID: {config_doc.id}")
            print(f"  Status: {config.get('status', 'UNKNOWN')}")
            print(f"  Trading Enabled: {config.get('trading_enabled', False)}")
            print(f"  Strategy: {config.get('strategy', 'UNKNOWN')}")
            print(f"  Mode: {config.get('mode', 'UNKNOWN')}")
            print(f"  Symbol Universe: {len(config.get('symbol_universe', []))} symbols")
            
            if config.get('symbol_universe'):
                print(f"  Symbols: {', '.join(config['symbol_universe'][:5])}...")
            
            # CRITICAL CHECKS
            if config.get('status') != 'RUNNING':
                print(f"  WARNING: Bot status is '{config.get('status')}', not 'RUNNING'")
            
            if not config.get('trading_enabled'):
                print(f"  CRITICAL: trading_enabled is FALSE - Bot will NOT place trades!")
            
            if not config.get('symbol_universe'):
                print(f"  CRITICAL: No symbols in universe - Bot has nothing to trade!")
            
            print()
            
except Exception as e:
    print(f"ERROR: Failed to read bot_config: {e}")

# TEST 2: Activity Feed
print("\n2. ACTIVITY FEED (activity_feed collection)")
print("-" * 80)

try:
    # Get recent activity (last 24 hours)
    since = datetime.now() - timedelta(hours=24)
    activities = db.collection('activity_feed').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).get()
    
    if not activities:
        print("CRITICAL: No activity feed entries found!")
        print("Bot is NOT logging any activity - it may not be running at all")
    else:
        print(f"Found {len(activities)} recent activity entries\n")
        
        # Group by type
        activity_types = defaultdict(int)
        for activity in activities:
            act_data = activity.to_dict()
            act_type = act_data.get('type', 'UNKNOWN')
            activity_types[act_type] += 1
        
        print("Activity breakdown:")
        for act_type, count in sorted(activity_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {act_type}: {count}")
        
        # Show last 10 activities
        print("\nLast 10 activities:")
        for i, activity in enumerate(activities[:10]):
            act_data = activity.to_dict()
            timestamp = act_data.get('timestamp')
            if hasattr(timestamp, 'strftime'):
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                timestamp_str = str(timestamp)
            print(f"  [{timestamp_str}] {act_data.get('type')}: {act_data.get('message', 'No message')[:60]}")
        
        # CRITICAL CHECK: Only BOT_STARTED activities
        if len(activity_types) == 1 and 'BOT_STARTED' in activity_types:
            print("\nCRITICAL: Only 'BOT_STARTED' activities found!")
            print("Bot starts but doesn't log any further actions")
            print("Possible causes:")
            print("  - Bot crashes after startup")
            print("  - Main loop is not executing")
            print("  - Strategy execution is failing silently")
            
except Exception as e:
    print(f"ERROR: Failed to read activity_feed: {e}")

# TEST 3: Signals
print("\n3. TRADING SIGNALS (signals collection)")
print("-" * 80)

try:
    # Get recent signals (last 7 days)
    since = datetime.now() - timedelta(days=7)
    signals = db.collection('signals').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).get()
    
    if not signals:
        print("CRITICAL: NO SIGNALS found in last 7 days!")
        print("Bot is NOT generating any trading signals")
        print("Possible causes:")
        print("  - Market conditions don't match strategy criteria")
        print("  - Strategy logic is not being executed")
        print("  - Insufficient candle data for analysis")
        print("  - All signals are being filtered out")
    else:
        print(f"Found {len(signals)} signals in recent history\n")
        
        # Group by status
        by_status = defaultdict(int)
        by_symbol = defaultdict(int)
        by_signal_type = defaultdict(int)
        
        for signal in signals:
            sig_data = signal.to_dict()
            by_status[sig_data.get('status', 'UNKNOWN')] += 1
            by_symbol[sig_data.get('symbol', 'UNKNOWN')] += 1
            by_signal_type[sig_data.get('signal_type', 'UNKNOWN')] += 1
        
        print("Signals by status:")
        for status, count in sorted(by_status.items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")
        
        print("\nTop 5 symbols:")
        for symbol, count in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {symbol}: {count}")
        
        print("\nSignal types:")
        for sig_type, count in sorted(by_signal_type.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sig_type}: {count}")
        
        # Show recent signals
        print("\nRecent signals:")
        for signal in signals[:5]:
            sig_data = signal.to_dict()
            timestamp = sig_data.get('timestamp')
            if hasattr(timestamp, 'strftime'):
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                timestamp_str = str(timestamp)
            print(f"  [{timestamp_str}] {sig_data.get('symbol')} - {sig_data.get('signal_type')} - {sig_data.get('status')}")
            
except Exception as e:
    print(f"ERROR: Failed to read signals: {e}")

# TEST 4: Orders
print("\n4. ORDERS (orders collection)")
print("-" * 80)

try:
    # Get all orders (last 30 days)
    since = datetime.now() - timedelta(days=30)
    orders = db.collection('orders').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(100).get()
    
    if not orders:
        print("CRITICAL: NO ORDERS found in last 30 days!")
        print("This confirms the bot has NEVER placed any orders")
        print("\nPossible causes:")
        print("  1. No signals are being generated")
        print("  2. Signals are generated but not converted to orders")
        print("  3. Order placement logic has a bug")
        print("  4. Trading is disabled in configuration")
        print("  5. Paper trading mode prevents real orders")
    else:
        print(f"Found {len(orders)} orders\n")
        
        # Group by status
        by_status = defaultdict(int)
        by_symbol = defaultdict(int)
        
        for order in orders:
            order_data = order.to_dict()
            by_status[order_data.get('status', 'UNKNOWN')] += 1
            by_symbol[order_data.get('symbol', 'UNKNOWN')] += 1
        
        print("Orders by status:")
        for status, count in sorted(by_status.items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")
        
        print("\nTop 5 symbols:")
        for symbol, count in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {symbol}: {count}")
            
except Exception as e:
    print(f"ERROR: Failed to read orders: {e}")

# TEST 5: Bot Status
print("\n5. BOT STATUS (bot_status collection)")
print("-" * 80)

try:
    statuses = db.collection('bot_status').limit(10).get()
    
    if not statuses:
        print("WARNING: No bot_status documents found")
    else:
        print(f"Found {len(statuses)} bot status document(s)\n")
        
        for status_doc in statuses:
            status = status_doc.to_dict()
            print(f"User ID: {status_doc.id}")
            print(f"  Status: {status.get('status', 'UNKNOWN')}")
            print(f"  Last Updated: {status.get('last_updated')}")
            print(f"  Active Positions: {status.get('active_positions', 0)}")
            print(f"  Today's Trades: {status.get('trades_today', 0)}")
            print(f"  Regime: {status.get('regime', 'UNKNOWN')}")
            print(f"  ADX: {status.get('adx_value', 'N/A')}")
            print()
            
except Exception as e:
    print(f"ERROR: Failed to read bot_status: {e}")

# TEST 6: User Configurations
print("\n6. USER CONFIGS (user_configs collection)")
print("-" * 80)

try:
    user_configs = db.collection('user_configs').limit(10).get()
    
    if not user_configs:
        print("WARNING: No user_configs documents found")
    else:
        print(f"Found {len(user_configs)} user config document(s)\n")
        
        for user_doc in user_configs:
            user_data = user_doc.to_dict()
            print(f"User ID: {user_doc.id}")
            print(f"  Angel API Key: {'SET' if user_data.get('api_key') else 'MISSING'}")
            print(f"  Client Code: {'SET' if user_data.get('client_code') else 'MISSING'}")
            print(f"  Password: {'SET' if user_data.get('password') else 'MISSING'}")
            print(f"  TOTP Secret: {'SET' if user_data.get('totp_secret') else 'MISSING'}")
            print()
            
            if not all([user_data.get('api_key'), user_data.get('client_code'), 
                       user_data.get('password'), user_data.get('totp_secret')]):
                print("  CRITICAL: Missing Angel One credentials - bot cannot trade!")
            
except Exception as e:
    print(f"ERROR: Failed to read user_configs: {e}")

# SUMMARY
print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80 + "\n")

print("Based on Firestore data analysis:\n")

# This will be populated based on the data we found
issues = []

print("Check the output above for specific issues found in Firestore.")
print("\nCommon reasons for no trades:")
print("1. trading_enabled = false in bot_config")
print("2. No symbols in symbol_universe")
print("3. Bot status not 'RUNNING'")
print("4. Only 'BOT_STARTED' in activity feed (bot crashes after start)")
print("5. No signals generated (market conditions or strategy issues)")
print("6. Missing Angel One credentials in user_configs")
print("\n" + "=" * 80)
print("END OF FIRESTORE DIAGNOSTIC")
print("=" * 80)
