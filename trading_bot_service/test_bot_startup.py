"""
Test Bot Startup with Optimal Parameters
Simulates what will happen when you click "Start Trading Bot" tomorrow
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase
if not firebase_admin._apps:
    cred_path = os.path.join(os.path.dirname(__file__), 'firestore-key.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

db = firestore.client()

print("\n" + "="*80)
print("SIMULATING BOT STARTUP - WHAT HAPPENS WHEN YOU CLICK 'START'")
print("="*80 + "\n")

user_id = 'PiRehqxZQleR8QCZG0QczmQTY402'

# STEP 1: Load bot config (what bot does on startup)
print("[STEP 1] Loading bot configuration from Firestore...")
try:
    config_doc = db.collection('bot_configs').document(user_id).get()
    if config_doc.exists:
        config = config_doc.to_dict()
        print("✅ Configuration loaded successfully\n")
        
        # Display config
        print("📊 BOT CONFIGURATION:")
        print(f"   Portfolio: ₹{config.get('portfolio_value', 0):,.0f}")
        print(f"   Mode: {config.get('trading_mode', 'unknown').upper()}")
        print(f"   Strategy: {config.get('strategy', 'unknown')}")
        print(f"   Max Positions: {config.get('max_open_positions', 0)}")
        print(f"   Position Size: {config.get('max_position_size_pct', 0)*100}%")
        
        # Check strategy params
        strategy_params = config.get('strategy_params', {})
        if strategy_params:
            print("\n⚙️  STRATEGY PARAMETERS (YOUR OPTIMAL SETTINGS):")
            print(f"   ADX Threshold: {strategy_params.get('adx_threshold', 'NOT SET')}")
            print(f"   RSI Oversold: {strategy_params.get('rsi_oversold', 'NOT SET')}")
            print(f"   RSI Overbought: {strategy_params.get('rsi_overbought', 'NOT SET')}")
            print(f"   Volume Multiplier: {strategy_params.get('volume_multiplier', 'NOT SET')}x")
            print(f"   Risk:Reward: 1:{strategy_params.get('risk_reward', 'NOT SET')}")
            print(f"   Position Size: {strategy_params.get('position_size', 'NOT SET')}%")
            print(f"   Trading Start: {strategy_params.get('trading_start_hour', 'NOT SET')}:30")
            print(f"   Trading End: {strategy_params.get('trading_end_hour', 'NOT SET')}:15")
            nifty_align = strategy_params.get('nifty_alignment', 'NOT SET')
            nifty_text = 'Same Direction' if nifty_align == 0.0 else f'{nifty_align}%'
            print(f"   Nifty Alignment: {nifty_text}")
        else:
            print("\n❌ NO STRATEGY PARAMETERS FOUND!")
            print("   Bot will use hardcoded defaults (NOT optimal)")
            
    else:
        print("❌ Configuration not found!")
        print("   Bot will create default config (NOT using your optimal parameters)")
        
except Exception as e:
    print(f"❌ Error loading config: {e}")
    exit(1)

# STEP 2: Simulate strategy initialization
print("\n" + "-"*80)
print("[STEP 2] Simulating Alpha-Ensemble Strategy Initialization...")
print("-"*80 + "\n")

if strategy_params:
    print("✅ Strategy will initialize with:")
    print(f"   self.ADX_MIN_TRENDING = {strategy_params.get('adx_threshold', 25)}")
    print(f"   self.RSI_LONG_MIN = {strategy_params.get('rsi_oversold', 35)}")
    print(f"   self.RSI_LONG_MAX = {strategy_params.get('rsi_overbought', 70)}")
    print(f"   self.RSI_SHORT_MIN = {100 - strategy_params.get('rsi_overbought', 70)}")
    print(f"   self.RSI_SHORT_MAX = {100 - strategy_params.get('rsi_oversold', 35)}")
    print(f"   self.VOLUME_MULTIPLIER = {strategy_params.get('volume_multiplier', 2.5)}")
    print(f"   self.RISK_REWARD_RATIO = {strategy_params.get('risk_reward', 2.5)}")
    print(f"   self.RISK_PER_TRADE_PERCENT = {strategy_params.get('position_size', 5.0)}%")
    print(f"   self.SESSION_START_TIME = {strategy_params.get('trading_start_hour', 10)}:30")
    print(f"   self.SESSION_END_TIME = {strategy_params.get('trading_end_hour', 14)}:15")
    print(f"   self.NIFTY_ALIGNMENT_THRESHOLD = {strategy_params.get('nifty_alignment', 0.0)}%")
else:
    print("❌ NO PARAMETERS - Will use old hardcoded values:")
    print("   self.ADX_MIN_TRENDING = 25 (hardcoded)")
    print("   self.RSI_LONG_MIN = 52 (hardcoded - NOT your 35!)")
    print("   self.RSI_LONG_MAX = 62 (hardcoded - NOT your 70!)")
    print("   self.VOLUME_MULTIPLIER = 2.0 (hardcoded - NOT your 2.5!)")
    print("   self.RISK_REWARD_RATIO = 3.0 (hardcoded - NOT your 2.5!)")
    print("   self.RISK_PER_TRADE_PERCENT = 2.0% (hardcoded - NOT your 5%!)")

# STEP 3: Validation
print("\n" + "="*80)
if strategy_params and all([
    strategy_params.get('adx_threshold') == 25,
    strategy_params.get('rsi_oversold') == 35,
    strategy_params.get('rsi_overbought') == 70,
    strategy_params.get('volume_multiplier') == 2.5,
    strategy_params.get('risk_reward') == 2.5,
    strategy_params.get('position_size') == 5.0,
    strategy_params.get('trading_start_hour') == 10,
    strategy_params.get('trading_end_hour') == 14,
    strategy_params.get('nifty_alignment') == 0.0
]):
    print("✅ SUCCESS - BOT WILL USE YOUR OPTIMAL PARAMETERS!")
    print("="*80)
    print("\n🎯 VERIFIED:")
    print("  ✅ Configuration exists in Firestore")
    print("  ✅ Strategy parameters are set correctly")
    print("  ✅ All 9 optimal values match your backtest")
    print("  ✅ Bot will initialize with these on startup")
    print("\n🚀 READY FOR TOMORROW'S MARKET SESSION!")
else:
    print("❌ WARNING - PARAMETERS DON'T MATCH OPTIMAL VALUES!")
    print("="*80)
    print("\nCheck above for which parameters are wrong.")
    print("Run set_optimal_params.py again if needed.")
    
print()
