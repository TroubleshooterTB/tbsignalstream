"""
Test script to diagnose replay mode issues
Checks if the bot can fetch historical data for replay simulation
"""

import os
import sys
from datetime import datetime, timedelta
from SmartApi import SmartConnect
import pyotp

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'trading_bot_service', '.env'))

# Add service directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'trading_bot_service'))

def test_replay_data_fetch():
    """Test if we can fetch historical data for replay mode"""
    
    print("=" * 80)
    print("🔄 REPLAY MODE DATA FETCH TEST")
    print("=" * 80)
    
    # Get credentials from environment (same as bot uses)
    api_key = os.environ.get('ANGELONE_TRADING_API_KEY', '').strip()
    client_code = os.environ.get('ANGELONE_CLIENT_CODE', '').strip()
    password = os.environ.get('ANGELONE_PASSWORD', '').strip()
    totp_secret = os.environ.get('ANGELONE_TOTP_SECRET', '').strip()  # CRITICAL: Strip whitespace
    
    if not all([api_key, client_code, password, totp_secret]):
        print("❌ Missing credentials")
        print(f"  API Key: {'✅' if api_key else '❌'}")
        print(f"  Client Code: {'✅' if client_code else '❌'}")
        print(f"  Password: {'✅' if password else '❌'}")
        print(f"  TOTP Secret: {'✅' if totp_secret else '❌'}")
        return False
    
    print(f"✅ Credentials found")
    print(f"   API Key: {api_key}")
    print(f"   Client Code: {client_code}")
    
    # Step 1: Authenticate
    print("\n🔐 Step 1: Authenticating...")
    try:
        smart_api = SmartConnect(api_key=api_key)
        totp = pyotp.TOTP(totp_secret).now()
        
        session_data = smart_api.generateSession(client_code, password, totp)
        
        if session_data and session_data.get('status'):
            jwt_token = session_data['data']['jwtToken']
            feed_token = session_data['data']['feedToken']
            print(f"✅ Authentication successful")
            print(f"   JWT Token: {jwt_token[:20]}...")
            print(f"   Feed Token: {feed_token[:20]}...")
        else:
            print(f"❌ Authentication failed: {session_data}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Get a test symbol token
    print("\n📋 Step 2: Getting symbol token for RELIANCE...")
    try:
        from nifty200_watchlist import NIFTY200_WATCHLIST
        
        # Find RELIANCE
        reliance = None
        for stock in NIFTY200_WATCHLIST:
            if stock['symbol'] == 'RELIANCE-EQ':
                reliance = stock
                break
        
        if not reliance:
            print("❌ RELIANCE not found in watchlist")
            return False
        
        symbol_token = reliance['token']
        print(f"✅ Symbol token: {symbol_token}")
        
    except Exception as e:
        print(f"❌ Error getting symbol token: {e}")
        return False
    
    # Step 3: Test replay date data fetch
    print("\n📊 Step 3: Fetching historical data for replay date...")
    
    # Use a recent weekday (not weekend/holiday)
    test_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    
    # If that's weekend, go back more
    test_date_dt = datetime.strptime(test_date, '%Y-%m-%d')
    while test_date_dt.weekday() >= 5:  # Saturday=5, Sunday=6
        test_date_dt -= timedelta(days=1)
    test_date = test_date_dt.strftime('%Y-%m-%d')
    
    print(f"   Testing with date: {test_date}")
    
    try:
        params = {
            "exchange": "NSE",
            "symboltoken": symbol_token,
            "interval": "ONE_MINUTE",
            "fromdate": f"{test_date} 09:15",
            "todate": f"{test_date} 15:30"
        }
        
        print(f"   Fetching candles with params: {params}")
        hist_data = smart_api.getCandleData(params)
        
        print(f"\n   API Response:")
        print(f"   - Type: {type(hist_data)}")
        print(f"   - Keys: {hist_data.keys() if hist_data else 'None'}")
        
        if hist_data and hist_data.get('status'):
            candles = hist_data.get('data', [])
            print(f"✅ Data fetch successful")
            print(f"   - Status: {hist_data.get('status')}")
            print(f"   - Message: {hist_data.get('message')}")
            print(f"   - Candles: {len(candles)}")
            
            if candles:
                print(f"\n   Sample candles (first 3):")
                for i, candle in enumerate(candles[:3]):
                    print(f"   [{i}] {candle}")
                
                return True
            else:
                print(f"⚠️  No candle data returned (might be holiday/weekend)")
                print(f"   Full response: {hist_data}")
                return False
        else:
            print(f"❌ Data fetch failed")
            print(f"   Response: {hist_data}")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching historical data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_replay_data_fetch()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ REPLAY MODE: Historical data fetch WORKING")
        print("   Replay mode should work correctly")
    else:
        print("❌ REPLAY MODE: Historical data fetch FAILED")
        print("   Replay mode will not work - need to fix data fetch issue")
    print("=" * 80)
    
    sys.exit(0 if success else 1)
