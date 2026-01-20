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

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
        print("[OK] Firebase already initialized")
    except ValueError:
        # Try multiple possible paths for the firestore key
        possible_paths = [
            "firestore-key.json",
            "../firestore-key.json",
            os.path.join(os.path.dirname(__file__), "firestore-key.json"),
            os.path.join(os.path.dirname(__file__), "..", "firestore-key.json")
        ]
        
        cred_path = None
        for path in possible_paths:
            if os.path.exists(path):
                cred_path = path
                break
        
        if not cred_path:
            print(f"[ERROR] Firestore credentials not found. Tried:")
            for path in possible_paths:
                print(f"  - {os.path.abspath(path)}")
            sys.exit(1)
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print(f"[OK] Firebase initialized from {cred_path}")
    
    db = firestore.client()
    
except Exception as e:
    print(f"[ERROR] Failed to initialize Firestore: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Get bot configuration from Firestore
USER_ID = "default_user"

print(f"\n[CONFIG] Loading bot configuration for user: {USER_ID}...")

try:
    config_doc = db.collection('bot_config').document(USER_ID).get()
    
    if not config_doc.exists:
        print(f"[ERROR] No configuration found for user {USER_ID}")
        print("[INFO] Run initialize_bot_firestore.py first")
        sys.exit(1)
    
    config = config_doc.to_dict()
    print(f"[OK] Bot configuration loaded")
    print(f"   Strategy: {config.get('strategy', 'N/A')}")
    print(f"   Mode: {config.get('mode', 'N/A')}")
    print(f"   Symbols: {len(config.get('symbol_universe', []))} stocks")
    print(f"   Trading Enabled: {config.get('trading_enabled', False)}")
    
except Exception as e:
    print(f"[ERROR] Failed to load configuration: {e}")
    sys.exit(1)

# Get Angel One credentials
print(f"\n[BROKER] Loading Angel One credentials...")

try:
    creds_doc = db.collection('angel_one_credentials').document(USER_ID).get()
    
    if not creds_doc.exists:
        print(f"[ERROR] No Angel One credentials found")
        print("[INFO] Run initialize_bot_firestore.py first")
        sys.exit(1)
    
    credentials_data = creds_doc.to_dict()
    print(f"[OK] Angel One credentials loaded")
    print(f"   Client Code: {credentials_data.get('client_code', 'N/A')}")
    
except Exception as e:
    print(f"[ERROR] Failed to load credentials: {e}")
    sys.exit(1)

# Import the bot engine
print(f"\n[BOT] Importing bot engine...")

try:
    from realtime_bot_engine import RealtimeBotEngine
    print("[OK] Bot engine imported successfully")
except Exception as e:
    print(f"[ERROR] Failed to import bot engine: {e}")
    print("[INFO] Make sure you're in the correct directory")
    print("[INFO] Required: trading_bot_service/realtime_bot_engine.py")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create the bot instance
print(f"\n[BOT] Creating bot instance...")

try:
    bot = RealtimeBotEngine(
        user_id=USER_ID,
        credentials=credentials_data,
        symbols=config.get('symbol_universe', []),
        trading_mode=config.get('mode', 'paper'),
        strategy=config.get('strategy', 'alpha-ensemble')
    )
    print("[OK] Bot instance created")
    print(f"   User: {USER_ID}")
    print(f"   Strategy: {config.get('strategy')}")
    print(f"   Mode: {config.get('mode')}")
    print(f"   Symbols: {len(config.get('symbol_universe', []))}")
    
except Exception as e:
    print(f"[ERROR] Failed to create bot: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Update bot status in Firestore
print(f"\n[STATUS] Updating bot status...")

try:
    db.collection('bot_status').document(USER_ID).set({
        'status': 'running',
        'is_running': True,
        'start_time': datetime.now().isoformat(),
        'mode': config.get('mode', 'paper'),
        'strategy': config.get('strategy'),
        'active_positions': 0,
        'total_trades_today': 0
    }, merge=True)
    print("[OK] Bot status updated to 'running'")
    
    # Log to activity feed
    db.collection('activity_feed').add({
        'user_id': USER_ID,
        'timestamp': datetime.now(),
        'type': 'BOT_STARTED',
        'message': f'Bot started locally - {config.get("strategy")} strategy',
        'details': {
            'mode': config.get('mode'),
            'symbols': len(config.get('symbol_universe', [])),
            'trading_enabled': config.get('trading_enabled', False)
        }
    })
    print("[OK] Activity logged: BOT_STARTED")
    
except Exception as e:
    print(f"[ERROR] Failed to update status: {e}")

# Signal handler for graceful shutdown
import threading
running_flag = threading.Event()
running_flag.set()

def signal_handler(sig, frame):
    print("\n\n[SHUTDOWN] Received stop signal (Ctrl+C)")
    print("[SHUTDOWN] Stopping bot gracefully...")
    running_flag.clear()
    
    try:
        db.collection('bot_status').document(USER_ID).update({
            'status': 'stopped',
            'is_running': False,
            'stop_time': datetime.now().isoformat()
        })
        print("[OK] Bot status updated to 'stopped'")
    except:
        pass
    
    print("[SHUTDOWN] Bot stopped. Goodbye!")
    sys.exit(0)

import signal
signal.signal(signal.SIGINT, signal_handler)

# Start the bot!
print("\n" + "=" * 80)
print("STARTING BOT - Press Ctrl+C to stop")
print("=" * 80 + "\n")

try:
    bot.start(running_flag)
except KeyboardInterrupt:
    print("\n[SHUTDOWN] Keyboard interrupt received")
    running_flag.clear()
except Exception as e:
    print(f"\n[ERROR] Bot crashed: {e}")
    import traceback
    traceback.print_exc()
    
    # Update status to error
    try:
        db.collection('bot_status').document(USER_ID).update({
            'status': 'error',
            'is_running': False,
            'error': str(e),
            'error_time': datetime.now().isoformat()
        })
    except:
        pass
    
    sys.exit(1)
finally:
    print("\n[CLEANUP] Cleaning up...")
    running_flag.clear()
