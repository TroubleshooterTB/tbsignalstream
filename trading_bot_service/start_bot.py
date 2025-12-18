"""
Run Live Trading Bot - Using Firestore Credentials
Reads API key, client code, and TOTP from Firestore
Only prompts for password
"""

import sys
sys.path.append('.')

from live_bot_v32 import LiveTradingBot
from getpass import getpass
import firebase_admin
from firebase_admin import firestore

def main():
    print("="*80)
    print("LIVE TRADING BOT - Alpha-Ensemble Strategy")
    print("="*80)
    print()
    
    # Initialize Firebase
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    
    db = firestore.client()
    
    # Get credentials from Firestore
    print("Loading credentials from Firestore...")
    creds_ref = db.collection('angel_one_credentials').limit(1).get()
    
    if len(creds_ref) == 0:
        print("ERROR: No credentials found in Firestore")
        return
    
    cred_doc = creds_ref[0].to_dict()
    api_key = cred_doc.get('api_key')
    client_code = cred_doc.get('client_code')
    
    print(f"API Key: {api_key}")
    print(f"Client Code: {client_code}")
    print()
    
    if not api_key or not client_code:
        print("ERROR: Missing API key or client code in Firestore")
        return
    
    # Always ask for password and TOTP code (they're not stored in Firestore for security)
    print("Enter your Angel One credentials:")
    password = getpass("Password: ").strip()
    totp_code = getpass("TOTP Code (6-digit code from authenticator app): ").strip()
    
    print()
    print("Select trading mode:")
    print("1. PAPER TRADING (Recommended for testing)")
    print("2. LIVE TRADING (Real money - use with caution!)")
    mode_choice = input("Enter choice (1 or 2): ").strip()
    
    paper_trade = mode_choice != "2"
    
    print()
    print(f"Mode: {'PAPER TRADING' if paper_trade else 'LIVE TRADING'}")
    print()
    
    if not paper_trade:
        confirm = input("You selected LIVE TRADING. Type 'CONFIRM' to proceed: ")
        if confirm != 'CONFIRM':
            print("Cancelled.")
            return
    
    # Initialize and run bot
    try:
        bot = LiveTradingBot(
            api_key=api_key,
            client_code=client_code,
            password=password,
            totp_code=totp_code,
            initial_capital=100000,
            paper_trade=paper_trade
        )
        
        # NIFTY 50 symbols (same as backtest)
        symbols = [
            {'symbol': 'RELIANCE-EQ', 'token': '2885'},
            {'symbol': 'TCS-EQ', 'token': '11536'},
            {'symbol': 'HDFCBANK-EQ', 'token': '1333'},
            {'symbol': 'INFY-EQ', 'token': '1594'},
            {'symbol': 'ICICIBANK-EQ', 'token': '4963'},
            {'symbol': 'HINDUNILVR-EQ', 'token': '1394'},
            {'symbol': 'ITC-EQ', 'token': '424'},
            {'symbol': 'BHARTIARTL-EQ', 'token': '10604'},
            {'symbol': 'KOTAKBANK-EQ', 'token': '1922'},
            {'symbol': 'BAJFINANCE-EQ', 'token': '317'},
            {'symbol': 'LT-EQ', 'token': '11483'},
            {'symbol': 'ASIANPAINT-EQ', 'token': '236'},
            {'symbol': 'AXISBANK-EQ', 'token': '5900'},
            {'symbol': 'HCLTECH-EQ', 'token': '7229'},
            {'symbol': 'MARUTI-EQ', 'token': '10999'},
            {'symbol': 'SUNPHARMA-EQ', 'token': '3351'},
            {'symbol': 'TITAN-EQ', 'token': '3506'},
            {'symbol': 'NESTLEIND-EQ', 'token': '17963'},
            {'symbol': 'ULTRACEMCO-EQ', 'token': '11532'},
            {'symbol': 'WIPRO-EQ', 'token': '3787'},
            {'symbol': 'NTPC-EQ', 'token': '11630'},
            {'symbol': 'TATAMOTORS-EQ', 'token': '3456'},
            {'symbol': 'BAJAJFINSV-EQ', 'token': '16675'},
            {'symbol': 'TATASTEEL-EQ', 'token': '3499'},
            {'symbol': 'TECHM-EQ', 'token': '13538'},
            {'symbol': 'ADANIENT-EQ', 'token': '25'},
            {'symbol': 'ONGC-EQ', 'token': '2475'},
            {'symbol': 'COALINDIA-EQ', 'token': '20374'},
            {'symbol': 'HINDALCO-EQ', 'token': '1363'},
            {'symbol': 'INDUSINDBK-EQ', 'token': '5258'},
            {'symbol': 'EICHERMOT-EQ', 'token': '910'},
            {'symbol': 'DIVISLAB-EQ', 'token': '10940'},
            {'symbol': 'BRITANNIA-EQ', 'token': '547'},
            {'symbol': 'DRREDDY-EQ', 'token': '881'},
            {'symbol': 'APOLLOHOSP-EQ', 'token': '157'},
            {'symbol': 'CIPLA-EQ', 'token': '694'},
            {'symbol': 'GRASIM-EQ', 'token': '1232'},
            {'symbol': 'HEROMOTOCO-EQ', 'token': '1348'},
            {'symbol': 'ADANIPORTS-EQ', 'token': '15083'},
            {'symbol': 'HINDZINC-EQ', 'token': '364'},
            {'symbol': 'M&M-EQ', 'token': '2031'},
            {'symbol': 'BPCL-EQ', 'token': '526'},
            {'symbol': 'TRENT-EQ', 'token': '1964'},
            {'symbol': 'ADANIGREEN-EQ', 'token': '25615'},
            {'symbol': 'LTIM-EQ', 'token': '17818'},
        ]
        
        # Start trading
        print()
        print("Starting bot...")
        print("NOTE: Market hours are 9:15 AM - 3:30 PM IST")
        print("Bot will wait until market opens if started outside market hours")
        print()
        bot.run(symbols, check_interval=300)  # Check every 5 minutes
        
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
