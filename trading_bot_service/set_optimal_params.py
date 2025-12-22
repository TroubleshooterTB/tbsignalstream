"""
Set Optimal Trading Parameters to Firestore
Run this to apply backtested optimal parameters to live trading bot
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

# Initialize Firebase
if not firebase_admin._apps:
    # Check for local credentials first
    cred_path = os.path.join(os.path.dirname(__file__), 'firestore-key.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized with service account key")
    else:
        firebase_admin.initialize_app()
        print("✅ Firebase initialized with ADC")

db = firestore.client()

# USER'S OPTIMAL PARAMETERS (From Backtesting)
OPTIMAL_PARAMS = {
    # Strategy Parameters
    'strategy_params': {
        'adx_threshold': 25,
        'rsi_oversold': 35,
        'rsi_overbought': 70,
        'volume_multiplier': 2.5,
        'risk_reward': 2.5,
        'position_size': 5.0,  # 5% per trade
        'nifty_alignment': 0.0,  # Same direction
        'trading_start_hour': 10,  # 10:30 AM
        'trading_end_hour': 14,    # 14:15 PM
    },
    
    # Risk Management
    'portfolio_value': 100000.0,
    'trading_mode': 'paper',
    'max_position_size_pct': 0.05,  # 5% max position size
    'max_daily_loss_pct': 0.03,
    'max_portfolio_heat': 0.20,
    'max_open_positions': 5,
    'emergency_stop': False,
    
    # Default Settings
    'symbols': 'NIFTY100',
    'interval': '5minute',
    'strategy': 'alpha-ensemble',
}

def set_user_config(user_id: str):
    """Set optimal parameters for a specific user"""
    try:
        doc_ref = db.collection('bot_configs').document(user_id)
        doc_ref.set(OPTIMAL_PARAMS, merge=True)
        print(f"✅ Optimal parameters set for user: {user_id}")
        print(f"\n📊 Applied Configuration:")
        print(f"   Strategy: Alpha-Ensemble")
        print(f"   Universe: NIFTY100")
        print(f"   ADX: {OPTIMAL_PARAMS['strategy_params']['adx_threshold']}")
        print(f"   RSI: {OPTIMAL_PARAMS['strategy_params']['rsi_oversold']}-{OPTIMAL_PARAMS['strategy_params']['rsi_overbought']}")
        print(f"   Volume: {OPTIMAL_PARAMS['strategy_params']['volume_multiplier']}x")
        print(f"   R:R: 1:{OPTIMAL_PARAMS['strategy_params']['risk_reward']}")
        print(f"   Position Size: {OPTIMAL_PARAMS['strategy_params']['position_size']}%")
        print(f"   Max Positions: {OPTIMAL_PARAMS['max_open_positions']}")
        print(f"   Trading Hours: 10:30-14:15")
        print(f"   Nifty Alignment: Same Direction")
        return True
    except Exception as e:
        print(f"❌ Error setting config: {e}")
        return False

def get_all_users():
    """Get all user IDs from angel_one_credentials collection"""
    try:
        users = db.collection('angel_one_credentials').stream()
        user_ids = [user.id for user in users]
        return user_ids
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        return []

if __name__ == '__main__':
    print("\n" + "="*70)
    print("OPTIMAL TRADING PARAMETERS SETUP")
    print("="*70 + "\n")
    
    # Get all users
    users = get_all_users()
    
    if not users:
        print("❌ No users found in database")
        print("\nTo add a user manually, provide user ID:")
        user_id = input("Enter User ID (or press Enter to skip): ").strip()
        if user_id:
            set_user_config(user_id)
    else:
        print(f"Found {len(users)} user(s):\n")
        for i, user_id in enumerate(users, 1):
            print(f"{i}. {user_id}")
        
        print("\nApplying optimal parameters to all users...")
        success_count = 0
        for user_id in users:
            if set_user_config(user_id):
                success_count += 1
            print()
        
        print("="*70)
        print(f"✅ Successfully configured {success_count}/{len(users)} users")
        print("="*70)
        print("\n🚀 NEXT STEPS:")
        print("1. Run backend health check: .\\check_backend_health.ps1")
        print("2. Start the bot from dashboard")
        print("3. Verify parameters in Activity Feed")
        print("4. Monitor trades in Paper mode first")
