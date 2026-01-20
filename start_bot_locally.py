"""
LOCAL BOT STARTER - Start the trading bot locally for testing
============================================================
This script starts the bot engine directly without needing the API server.
Perfect for testing and development.
"""

import os
import sys
import time
from datetime import datetime

# Add trading_bot_service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'trading_bot_service'))

print("=" * 80)
print("LOCAL BOT STARTER - Testing Trading Bot")
print("=" * 80 + "\n")

# Initialize Firestore
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    try:
        firebase_admin.get_app()
        print("✅ Firebase already initialized")
    except ValueError:
        cred_path = os.path.join("..", "firestore-key.json")
        if not os.path.exists(cred_path):
            print(f"❌ ERROR: Firestore credentials not found at {cred_path}")
            sys.exit(1)
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized")
    
    db = firestore.client()
    
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Firestore: {e}")
    sys.exit(1)

# Get bot configuration from Firestore
USER_ID = "default_user"

print(f"📋 Loading bot configuration for user: {USER_ID}...")

try:
    config_doc = db.collection('bot_config').document(USER_ID).get()
    
    if not config_doc.exists:
        print(f"❌ ERROR: Bot configuration not found!")
        print(f"   Run: python initialize_bot_firestore.py")
        sys.exit(1)
    
    config = config_doc.to_dict()
    print("✅ Bot configuration loaded")
    print(f"   Strategy: {config.get('strategy')}")
    print(f"   Mode: {config.get('mode')}")
    print(f"   Symbols: {len(config.get('symbol_universe', []))} stocks")
    print(f"   Trading Enabled: {config.get('trading_enabled')}")
    
except Exception as e:
    print(f"❌ ERROR: Failed to load configuration: {e}")
    sys.exit(1)

# Get Angel One credentials
print("\n🔐 Loading Angel One credentials...")

try:
    creds_doc = db.collection('angel_one_credentials').document(USER_ID).get()
    
    if not creds_doc.exists:
        print("⚠️  WARNING: Angel One credentials not found!")
        print("   Bot will start in demo mode (no real trading)")
        print("   To add credentials: python initialize_bot_firestore.py")
        
        # Create dummy credentials for testing
        credentials_data = {
            'api_key': os.getenv('ANGEL_API_KEY', 'dummy_key'),
            'client_code': os.getenv('ANGEL_CLIENT_CODE', 'dummy_code'),
            'jwt_token': 'dummy_jwt',
            'feed_token': 'dummy_feed',
            'refresh_token': 'dummy_refresh',
        }
    else:
        credentials_data = creds_doc.to_dict()
        print("✅ Angel One credentials loaded")
        print(f"   Client Code: {credentials_data.get('client_code')}")
    
except Exception as e:
    print(f"❌ ERROR: Failed to load credentials: {e}")
    sys.exit(1)

# Import bot engine
print("\n🤖 Importing bot engine...")

try:
    from realtime_bot_engine import RealtimeBotEngine
    print("✅ Bot engine imported successfully")
except ImportError as e:
    print(f"❌ ERROR: Failed to import bot engine: {e}")
    print("   Make sure you're in the correct directory")
    sys.exit(1)

# Create bot instance
print("\n🚀 Creating bot instance...")
print(f"   User ID: {USER_ID}")
print(f"   Strategy: {config.get('strategy')}")
print(f"   Mode: {config.get('mode')}")
print(f"   Symbols: {len(config.get('symbol_universe', []))} stocks")

try:
    bot = RealtimeBotEngine(
        user_id=USER_ID,
        credentials=credentials_data,
        symbols=config.get('symbol_universe', []),
        trading_mode=config.get('mode', 'paper'),
        strategy=config.get('strategy', 'alpha-ensemble'),
        db_client=db,
        replay_date=None  # Real-time mode
    )
    print("✅ Bot instance created")
    
except Exception as e:
    print(f"❌ ERROR: Failed to create bot: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Update bot status to running
print("\n📊 Updating bot status...")

try:
    db.collection('bot_status').document(USER_ID).update({
        'status': 'running',
        'is_running': True,
        'last_started': firestore.SERVER_TIMESTAMP,
        'last_updated': firestore.SERVER_TIMESTAMP
    })
    print("✅ Bot status updated to RUNNING")
    
    # Log to activity feed
    db.collection('activity_feed').add({
        'user_id': USER_ID,
        'type': 'BOT_STARTED',
        'message': f'Bot started locally - Strategy: {config.get("strategy")}, Mode: {config.get("mode")}',
        'timestamp': firestore.SERVER_TIMESTAMP,
        'details': {
            'strategy': config.get('strategy'),
            'mode': config.get('mode'),
            'symbols': len(config.get('symbol_universe', [])),
            'started_from': 'local_script'
        }
    })
    print("✅ Activity logged: BOT_STARTED")
    
except Exception as e:
    print(f"⚠️  WARNING: Failed to update status: {e}")

# Start the bot
print("\n" + "=" * 80)
print("STARTING BOT ENGINE")
print("=" * 80)
print("\nThe bot will now:")
print("  1. Connect to Angel One WebSocket")
print("  2. Bootstrap historical candle data")
print("  3. Subscribe to symbol price updates")
print("  4. Start scanning for trading signals")
print("  5. Place orders when signals are detected")
print("\nMonitor progress in Firestore activity_feed collection")
print("Press Ctrl+C to stop the bot\n")
print("=" * 80 + "\n")

# Running flag
is_running = True

def running_flag():
    return is_running

try:
    # Start bot
    bot.start(running_flag)
    
except KeyboardInterrupt:
    print("\n\n⚠️  Bot stopped by user (Ctrl+C)")
    is_running = False
    
except Exception as e:
    print(f"\n\n❌ ERROR: Bot crashed: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Update bot status to stopped
    print("\n📊 Updating bot status to STOPPED...")
    
    try:
        db.collection('bot_status').document(USER_ID).update({
            'status': 'stopped',
            'is_running': False,
            'last_stopped': firestore.SERVER_TIMESTAMP,
            'last_updated': firestore.SERVER_TIMESTAMP
        })
        print("✅ Bot status updated to STOPPED")
        
        # Log to activity feed
        db.collection('activity_feed').add({
            'user_id': USER_ID,
            'type': 'BOT_STOPPED',
            'message': 'Bot stopped',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'details': {
                'stopped_from': 'local_script'
            }
        })
        print("✅ Activity logged: BOT_STOPPED")
        
    except Exception as e:
        print(f"⚠️  WARNING: Failed to update status: {e}")
    
    print("\n" + "=" * 80)
    print("BOT STOPPED")
    print("=" * 80)
    print("\nCheck Firestore for:")
    print("  - activity_feed: All bot actions")
    print("  - signals: Trading signals generated")
    print("  - orders: Orders placed")
    print("  - bot_status: Final status")
    print("\nRun: python firestore_diagnostic.py\n")
