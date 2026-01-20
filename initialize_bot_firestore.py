"""
FIRESTORE INITIALIZATION - Create All Required Bot Configuration
=================================================================
This script creates all necessary Firestore documents for the bot to run.

Fixes:
1. bot_config: Creates configuration with strategy, symbols, etc.
2. activity_feed: Will be populated when bot starts
3. signals: Will be populated when bot generates signals
4. orders: Will be populated when bot places orders
5. bot_status: Sets status to ready/running
6. angel_one_credentials: Saves broker credentials

Usage:
    python initialize_bot_firestore.py
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Initialize Firestore
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    # Initialize Firebase (if not already initialized)
    try:
        firebase_admin.get_app()
        print("✅ Firebase already initialized")
    except ValueError:
        # Need to initialize
        cred_path = os.path.join("..", "firestore-key.json")
        if not os.path.exists(cred_path):
            print(f"❌ ERROR: Firestore credentials not found at {cred_path}")
            sys.exit(1)
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
    
    db = firestore.client()
    print("✅ Firestore client created\n")
    
except ImportError:
    print("❌ ERROR: firebase_admin not installed")
    print("Install with: pip install firebase-admin")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Firestore: {e}")
    sys.exit(1)

print("=" * 80)
print("FIRESTORE INITIALIZATION - Creating Bot Configuration")
print("=" * 80 + "\n")

# User ID (you can change this or make it configurable)
USER_ID = "default_user"
print(f"🔑 User ID: {USER_ID}\n")

# ============================================================================
# STEP 1: Create Angel One Credentials
# ============================================================================
print("STEP 1: Setting Up Angel One Credentials")
print("-" * 80)

# Check for credentials in environment variables
angel_credentials = {
    'api_key': os.getenv('ANGEL_API_KEY', ''),
    'client_code': os.getenv('ANGEL_CLIENT_CODE', ''),
    'password': os.getenv('ANGEL_PASSWORD', ''),
    'totp_secret': os.getenv('ANGEL_TOTP_SECRET', ''),
}

# If not in environment, prompt user
if not all(angel_credentials.values()):
    print("⚠️  Angel One credentials not found in environment variables")
    print("You can set them now or skip (bot will need them to trade)\n")
    
    use_env = input("Do you want to enter credentials now? (y/n): ").lower().strip()
    
    if use_env == 'y':
        print("\nEnter Angel One credentials:")
        angel_credentials['api_key'] = input("API Key: ").strip()
        angel_credentials['client_code'] = input("Client Code: ").strip()
        angel_credentials['password'] = input("Password: ").strip()
        angel_credentials['totp_secret'] = input("TOTP Secret: ").strip()
    else:
        print("⏭️  Skipping credentials setup - you'll need to add them later")
        angel_credentials = None

if angel_credentials and all(angel_credentials.values()):
    # Save to Firestore
    db.collection('angel_one_credentials').document(USER_ID).set(angel_credentials)
    print("✅ Angel One credentials saved to Firestore")
    print(f"   API Key: {angel_credentials['api_key'][:4]}****")
    print(f"   Client Code: {angel_credentials['client_code']}")
else:
    print("⚠️  No credentials saved - bot will not be able to trade")
    print("   To add later: Update 'angel_one_credentials' collection in Firestore\n")

# ============================================================================
# STEP 2: Create Bot Configuration
# ============================================================================
print("\nSTEP 2: Creating Bot Configuration")
print("-" * 80)

# Nifty 50 symbols (full list)
NIFTY50_SYMBOLS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
    'ICICIBANK', 'KOTAKBANK', 'SBIN', 'BHARTIARTL', 'BAJFINANCE',
    'ITC', 'ASIANPAINT', 'AXISBANK', 'LT', 'MARUTI',
    'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'WIPRO',
    'HCLTECH', 'BAJAJFINSV', 'ONGC', 'NTPC', 'POWERGRID',
    'TATAMOTORS', 'M&M', 'TECHM', 'ADANIPORTS', 'COALINDIA',
    'DIVISLAB', 'DRREDDY', 'GRASIM', 'HINDALCO', 'INDUSINDBK',
    'JSWSTEEL', 'TATASTEEL', 'CIPLA', 'HEROMOTOCO', 'BAJAJ-AUTO',
    'EICHERMOT', 'BRITANNIA', 'SHREECEM', 'UPL', 'APOLLOHOSP',
    'SBILIFE', 'TATACONSUM', 'LTIM', 'ADANIENT', 'BPCL'
]

bot_config = {
    'user_id': USER_ID,
    'status': 'ready',  # Will change to 'running' when bot starts
    'trading_enabled': True,  # CRITICAL: Enable trading
    'strategy': 'alpha-ensemble',  # Options: alpha-ensemble, defining, ironclad, pattern
    'mode': 'paper',  # Start with paper trading for safety
    'symbol_universe': NIFTY50_SYMBOLS,
    'interval': '5minute',
    'max_positions': 5,  # Max concurrent positions
    'capital': 100000,  # ₹1 lakh for paper trading
    'position_size_percent': 1.5,  # 1.5% per position (AUDIT FIX)
    'risk_per_trade': 0.02,  # 2% risk per trade
    'created_at': firestore.SERVER_TIMESTAMP,
    'updated_at': firestore.SERVER_TIMESTAMP,
    
    # Strategy-specific settings
    'alpha_ensemble': {
        'htf_timeframe': '1hour',
        'mtf_timeframe': '15minute',
        'filters_enabled': True
    },
    
    # Trading rules
    'trading_rules': {
        'breakeven_at_1r': True,  # Move stop to breakeven at 1R profit
        'trailing_stop': True,  # Enable trailing stops at 50% profit lock
        'max_daily_loss': 5000,  # Max ₹5k daily loss
        'max_daily_trades': 10,  # Max 10 trades per day
        'liquidity_filter': True,  # Block 12:00-14:30 (midday trap)
        'eod_close_time': '15:15',  # Close all positions at 3:15 PM
    },
    
    # Market hours (IST)
    'market_hours': {
        'start': '09:15',
        'end': '15:30'
    }
}

db.collection('bot_config').document(USER_ID).set(bot_config)
print("✅ Bot configuration created")
print(f"   Strategy: {bot_config['strategy']}")
print(f"   Mode: {bot_config['mode']}")
print(f"   Symbols: {len(bot_config['symbol_universe'])} stocks")
print(f"   Trading Enabled: {bot_config['trading_enabled']}")
print(f"   Max Positions: {bot_config['max_positions']}")

# Also save to bot_configs (main.py uses this collection name)
db.collection('bot_configs').document(USER_ID).set(bot_config)
print("✅ Bot configuration also saved to bot_configs collection")

# ============================================================================
# STEP 3: Initialize Bot Status
# ============================================================================
print("\nSTEP 3: Initializing Bot Status")
print("-" * 80)

bot_status = {
    'user_id': USER_ID,
    'status': 'ready',  # ready, running, stopped
    'is_running': False,  # Will be True when bot starts
    'active_positions': 0,
    'trades_today': 0,
    'pnl_today': 0.0,
    'total_pnl': 0.0,
    'signals_generated_today': 0,
    'orders_placed_today': 0,
    'last_updated': firestore.SERVER_TIMESTAMP,
    'last_started': None,
    'last_stopped': None,
    
    # Market regime
    'regime': 'UNKNOWN',  # TRENDING or SIDEWAYS
    'adx_value': None,
    
    # OTR tracking
    'otr_orders_placed': 0,
    'otr_orders_executed': 0,
    'otr_ratio': 0.0,
    
    # WebSocket status
    'websocket_connected': False,
    'latest_price_update': None,
    
    # Version info
    'bot_version': 'v2.0',
    'last_deployment': firestore.SERVER_TIMESTAMP
}

db.collection('bot_status').document(USER_ID).set(bot_status)
print("✅ Bot status initialized")
print(f"   Status: {bot_status['status']}")
print(f"   Is Running: {bot_status['is_running']}")

# ============================================================================
# STEP 4: Create Initial Activity Log Entry
# ============================================================================
print("\nSTEP 4: Creating Initial Activity Log")
print("-" * 80)

initial_activity = {
    'user_id': USER_ID,
    'type': 'SYSTEM_INITIALIZED',
    'message': 'Bot system initialized and configured - ready to start',
    'timestamp': firestore.SERVER_TIMESTAMP,
    'details': {
        'strategy': bot_config['strategy'],
        'mode': bot_config['mode'],
        'symbols': len(bot_config['symbol_universe']),
        'trading_enabled': bot_config['trading_enabled']
    }
}

db.collection('activity_feed').add(initial_activity)
print("✅ Initial activity log created")
print(f"   Type: {initial_activity['type']}")
print(f"   Message: {initial_activity['message']}")

# ============================================================================
# STEP 5: Verify User Config (for frontend)
# ============================================================================
print("\nSTEP 5: Creating User Config")
print("-" * 80)

user_config = {
    'user_id': USER_ID,
    'email': 'user@tbsignalstream.com',  # Change as needed
    'created_at': firestore.SERVER_TIMESTAMP,
    'settings': {
        'notifications_enabled': True,
        'email_alerts': True,
        'telegram_alerts': False
    },
    
    # Angel One connection status
    'angel_one_connected': bool(angel_credentials and all(angel_credentials.values())),
    'angel_one_last_connected': firestore.SERVER_TIMESTAMP if angel_credentials else None,
    
    # Subscription info
    'subscription_status': 'active',
    'subscription_plan': 'pro',
    'subscription_expires': None  # Set actual date if needed
}

db.collection('user_configs').document(USER_ID).set(user_config)
print("✅ User config created")
print(f"   User ID: {user_config['user_id']}")
print(f"   Angel One Connected: {user_config['angel_one_connected']}")

# ============================================================================
# STEP 6: Summary and Next Steps
# ============================================================================
print("\n" + "=" * 80)
print("INITIALIZATION COMPLETE ✅")
print("=" * 80 + "\n")

print("Firestore Collections Created:")
print("  ✅ bot_config - Bot configuration with strategy and symbols")
print("  ✅ bot_configs - Duplicate for backward compatibility")
print("  ✅ bot_status - Bot status tracking")
print("  ✅ activity_feed - Initial activity log")
print("  ✅ user_configs - User settings")

if angel_credentials and all(angel_credentials.values()):
    print("  ✅ angel_one_credentials - Broker credentials saved")
else:
    print("  ⚠️  angel_one_credentials - NOT SET (required for trading)")

print("\nBot Configuration Summary:")
print(f"  Strategy: {bot_config['strategy']}")
print(f"  Mode: {bot_config['mode']} (paper trading)")
print(f"  Symbols: {len(bot_config['symbol_universe'])} Nifty 50 stocks")
print(f"  Trading Enabled: {bot_config['trading_enabled']}")
print(f"  Max Positions: {bot_config['max_positions']}")
print(f"  Position Size: {bot_config['position_size_percent']}% per trade")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)

print("\n1. VERIFY FIRESTORE DATA")
print("   Run: python firestore_diagnostic.py")
print("   You should now see data in all collections!")

print("\n2. START THE BOT")
print("   Option A - Via Python:")
print("   python start_bot_locally.py")
print("")
print("   Option B - Via API:")
print('   curl -X POST "http://localhost:8080/start" \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"mode":"paper","strategy":"alpha-ensemble"}\'')

print("\n3. MONITOR BOT ACTIVITY")
print("   Watch Firestore in real-time:")
print("   python firestore_diagnostic.py")
print("")
print("   Check for:")
print("   - activity_feed: Should populate with BOT_STARTED, SYMBOL_SCANNED, etc.")
print("   - signals: Should appear within 30 minutes")
print("   - orders: Should be created when signals pass screening")

print("\n4. DEPLOY TO CLOUD RUN (for production)")
print("   cd trading_bot_service")
print("   gcloud run deploy trading-bot-service --source . --region asia-south1")

if not angel_credentials or not all(angel_credentials.values()):
    print("\n⚠️  WARNING: Angel One credentials not set!")
    print("   Bot will start but cannot trade without credentials.")
    print("   To add credentials:")
    print("   1. Set environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, etc.")
    print("   2. Re-run this script")
    print("   OR")
    print("   3. Manually add to Firestore 'angel_one_credentials' collection")

print("\n" + "=" * 80)
print("Bot is now CONFIGURED and ready to start! 🚀")
print("=" * 80 + "\n")
