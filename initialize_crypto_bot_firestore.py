"""
Initialize Crypto Bot in Firestore
==================================
Run this script ONCE to set up Firestore collections for crypto bot.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from cryptography.fernet import Fernet
import os

print("="*70)
print("CRYPTO BOT - FIRESTORE INITIALIZATION")
print("="*70)

# Initialize Firebase
try:
    firebase_admin.get_app()
    print("[OK] Firebase already initialized")
except ValueError:
    cred = credentials.Certificate('firestore-key.json')
    firebase_admin.initialize_app(cred)
    print("[OK] Firebase initialized")

db = firestore.client()

# ========================================
# USER CONFIGURATION
# ========================================
USER_ID = "default_user"  # Change this to your user ID

# Get your CoinDCX API credentials
print("\n" + "="*70)
print("STEP 1: Enter Your CoinDCX API Credentials")
print("="*70)
print("(Get these from CoinDCX → Settings → API Management)")
print()

COINDCX_API_KEY = input("Enter your CoinDCX API Key: ").strip()
COINDCX_API_SECRET = input("Enter your CoinDCX API Secret: ").strip()

if not COINDCX_API_KEY or not COINDCX_API_SECRET:
    print("\n[ERROR] API key and secret are required!")
    exit(1)

print(f"\n[OK] Credentials received")
print(f"   API Key: {COINDCX_API_KEY[:8]}...")

# ========================================
# ENCRYPT AND SAVE CREDENTIALS
# ========================================
print("\n" + "="*70)
print("STEP 2: Encrypting and Saving Credentials")
print("="*70)

# Generate encryption key (store this securely in production!)
ENCRYPTION_KEY = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key()
    print(f"\n⚠️  WARNING: Generated new encryption key")
    print(f"   Save this key securely: {ENCRYPTION_KEY.decode()}")
    print(f"   Set as environment variable: CREDENTIALS_ENCRYPTION_KEY")
else:
    print(f"[OK] Using existing encryption key from environment")

# Encrypt API secret
fernet = Fernet(ENCRYPTION_KEY)
encrypted_secret = fernet.encrypt(COINDCX_API_SECRET.encode()).decode()

# Save to Firestore
doc_ref = db.collection('coindcx_credentials').document(USER_ID)
doc_ref.set({
    'api_key': COINDCX_API_KEY,
    'api_secret_encrypted': encrypted_secret,
    'enabled': True,
    'created_at': firestore.SERVER_TIMESTAMP,
    'last_updated': firestore.SERVER_TIMESTAMP
})

print(f"[OK] Credentials saved to Firestore")
print(f"   Collection: coindcx_credentials")
print(f"   Document: {USER_ID}")

# ========================================
# CREATE CRYPTO BOT CONFIGURATION
# ========================================
print("\n" + "="*70)
print("STEP 3: Creating Crypto Bot Configuration")
print("="*70)

bot_config = {
    'user_id': USER_ID,
    'active_pair': 'BTC',  # Start with BTC
    'trading_enabled': True,
    'mode': 'paper',  # Start with paper trading for safety
    'strategy_day': 'momentum_scalping',
    'strategy_night': 'mean_reversion',
    'risk_params': {
        'target_volatility': 0.25,
        'max_position_weight': 2.0,
        'max_daily_loss_pct': 0.05,
        'rebalance_threshold': 0.20,
        'fee_barrier_pct': 0.0015,
        'min_daily_volume_usd': 1000000
    },
    'created_at': firestore.SERVER_TIMESTAMP,
    'last_updated': firestore.SERVER_TIMESTAMP
}

db.collection('crypto_bot_config').document(USER_ID).set(bot_config)
print(f"[OK] Crypto bot configuration created")

# ========================================
# CREATE INITIAL BOT STATUS
# ========================================
print("\n" + "="*70)
print("STEP 4: Creating Initial Bot Status")
print("="*70)

bot_status = {
    'user_id': USER_ID,
    'status': 'stopped',
    'is_running': False,
    'active_pair': 'BTC',
    'open_positions': 0,
    'total_trades_today': 0,
    'daily_pnl': 0,
    'last_updated': firestore.SERVER_TIMESTAMP
}

db.collection('crypto_bot_status').document(USER_ID).set(bot_status)
print(f"[OK] Initial bot status created")

# ========================================
# CREATE ACTIVITY FEED ENTRY
# ========================================
print("\n" + "="*70)
print("STEP 5: Logging Initial Setup")
print("="*70)

db.collection('crypto_activity_feed').add({
    'user_id': USER_ID,
    'timestamp': firestore.SERVER_TIMESTAMP,
    'type': 'CRYPTO_BOT_INITIALIZED',
    'message': 'Crypto bot initialized successfully',
    'details': {
        'active_pair': 'BTC',
        'mode': 'paper',
        'strategies': ['momentum_scalping', 'mean_reversion']
    }
})

print(f"[OK] Activity logged")

# ========================================
# SUMMARY
# ========================================
print("\n" + "="*70)
print("✅ INITIALIZATION COMPLETE!")
print("="*70)
print(f"\nFirestore Collections Created:")
print(f"  ✅ coindcx_credentials/{USER_ID}")
print(f"  ✅ crypto_bot_config/{USER_ID}")
print(f"  ✅ crypto_bot_status/{USER_ID}")
print(f"  ✅ crypto_activity_feed (collection)")

print(f"\nNext Steps:")
print(f"  1. Verify credentials in Firebase Console")
print(f"  2. Start bot locally:")
print(f"     python start_crypto_bot_locally.py --user {USER_ID} --pair BTC")
print(f"  3. Monitor logs for signals")
print(f"  4. After successful testing, switch to live mode")

print("\n" + "="*70)
print("Ready to trade! 🚀")
print("="*70)
