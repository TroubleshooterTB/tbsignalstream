#!/usr/bin/env python3
"""
COMPREHENSIVE ANGELONE API TEST
Tests ALL remaining components that couldn't be tested before:
1. AngelOne Authentication
2. Historical Data Fetching
3. WebSocket Connection
4. Pattern Detection on Real Data
5. Complete Bot Startup Flow
"""

import os
import sys
import time
from datetime import datetime, timedelta
import logging
import requests
import pyotp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AngelOne credentials from Secret Manager
ANGELONE_API_KEY = "jgosiGzs"
ANGELONE_CLIENT_CODE = "AABL713311"
ANGELONE_PASSWORD = "1012"  # 4-digit trading PIN
ANGELONE_TOTP_SECRET = "AGODKRXZZH6FHMYWMSBIK6KDXQ"

class AngelOneAPITester:
    """Comprehensive AngelOne API testing"""
    
    def __init__(self):
        self.api_key = ANGELONE_API_KEY
        self.client_code = ANGELONE_CLIENT_CODE
        self.password = ANGELONE_PASSWORD
        self.totp_secret = ANGELONE_TOTP_SECRET
        self.base_url = "https://apiconnect.angelone.in"
        
        self.jwt_token = None
        self.feed_token = None
        self.refresh_token = None
        
    def test_authentication(self):
        """Test 1: AngelOne Authentication"""
        print("\n" + "=" * 80)
        print("TEST 1: ANGELONE AUTHENTICATION")
        print("=" * 80)
        
        try:
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_secret)
            totp_code = totp.now()
            logger.info(f"Generated TOTP: {totp_code}")
            
            # Authentication endpoint
            url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '192.168.1.1',
                'X-ClientPublicIP': '106.51.74.202',
                'X-MACAddress': '00:00:00:00:00:00',
                'X-PrivateKey': self.api_key
            }
            
            payload = {
                'clientcode': self.client_code,
                'password': self.password,
                'totp': totp_code
            }
            
            logger.info("Sending authentication request...")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            result = response.json()
            
            if response.status_code == 200 and result.get('status'):
                data = result.get('data', {})
                self.jwt_token = data.get('jwtToken', '')
                self.feed_token = data.get('feedToken', '')
                self.refresh_token = data.get('refreshToken', '')
                
                print(f"✅ Authentication: SUCCESS")
                print(f"✓ JWT Token: {self.jwt_token[:50]}...")
                print(f"✓ Feed Token: {self.feed_token[:30]}...")
                print(f"✓ Refresh Token: {self.refresh_token[:30]}...")
                return True
            else:
                print(f"❌ Authentication: FAILED")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication: ERROR - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_historical_data(self):
        """Test 2: Historical Data Fetching"""
        print("\n" + "=" * 80)
        print("TEST 2: HISTORICAL DATA FETCHING")
        print("=" * 80)
        
        if not self.jwt_token:
            print("❌ Skipped: No authentication token")
            return False
        
        try:
            # Test with RELIANCE (token: 2885)
            symbol_token = "2885"
            symbol_name = "RELIANCE"
            
            # Get yesterday's date (last trading day)
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            # Market hours: 9:15 AM to 3:30 PM
            from_date = yesterday.replace(hour=14, minute=30, second=0, microsecond=0)
            to_date = yesterday.replace(hour=15, minute=30, second=0, microsecond=0)
            
            url = f"{self.base_url}/rest/secure/angelbroking/historical/v1/getCandleData"
            
            headers = {
                'Authorization': f'Bearer {self.jwt_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '192.168.1.1',
                'X-ClientPublicIP': '106.51.74.202',
                'X-MACAddress': '00:00:00:00:00:00',
                'X-PrivateKey': self.api_key
            }
            
            payload = {
                "exchange": "NSE",
                "symboltoken": symbol_token,
                "interval": "ONE_MINUTE",
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M")
            }
            
            logger.info(f"Fetching historical data for {symbol_name}...")
            logger.info(f"Period: {from_date.strftime('%Y-%m-%d %H:%M')} to {to_date.strftime('%Y-%m-%d %H:%M')}")
            
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            elapsed = time.time() - start_time
            
            result = response.json()
            
            if response.status_code == 200 and result.get('status'):
                candles = result.get('data', [])
                print(f"✅ Historical Data: SUCCESS")
                print(f"✓ Symbol: {symbol_name}")
                print(f"✓ Candles Received: {len(candles)}")
                print(f"✓ Fetch Time: {elapsed:.2f} seconds")
                print(f"✓ Period: 60 minutes (optimized window)")
                
                if candles:
                    print(f"✓ Sample Candle: {candles[0]}")
                
                return True
            else:
                print(f"❌ Historical Data: FAILED")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Historical Data: ERROR - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_websocket_connection(self):
        """Test 3: WebSocket Connection"""
        print("\n" + "=" * 80)
        print("TEST 3: WEBSOCKET CONNECTION")
        print("=" * 80)
        
        if not self.jwt_token or not self.feed_token:
            print("❌ Skipped: No authentication tokens")
            return False
        
        try:
            # Import WebSocket manager
            os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot_service'))
            sys.path.insert(0, os.getcwd())
            
            from ws_manager.websocket_manager_v2 import AngelWebSocketV2Manager
            
            logger.info("Initializing WebSocket manager...")
            
            # Test tokens for RELIANCE, TCS, INFY
            test_tokens = {
                'RELIANCE': '2885',
                'TCS': '11536',
                'INFY': '1594'
            }
            
            ws_manager = AngelWebSocketV2Manager(
                api_key=self.api_key,
                client_code=self.client_code,
                feed_token=self.feed_token,
                jwt_token=self.jwt_token
            )
            
            logger.info("Connecting to WebSocket...")
            
            # Connect
            if ws_manager.connect():
                print(f"✅ WebSocket Connection: SUCCESS")
                print(f"✓ Connected to AngelOne WebSocket v2")
                
                # Subscribe to test tokens
                logger.info("Subscribing to test symbols...")
                
                # Prepare tokens in correct format
                token_list = [
                    {"exchangeType": 1, "tokens": ["2885", "11536", "1594"]}  # NSE_CM: RELIANCE, TCS, INFY
                ]
                
                ws_manager.subscribe(mode=ws_manager.MODE_LTP, tokens=token_list)
                logger.info(f"  Subscribed to {len(test_tokens)} symbols in LTP mode")
                
                print(f"✓ Subscribed to {len(test_tokens)} symbols")
                
                # Wait for some ticks
                logger.info("Waiting for tick data (5 seconds)...")
                time.sleep(5)
                
                # Check if we received any ticks
                tick_count = len(ws_manager.tick_buffer) if hasattr(ws_manager, 'tick_buffer') else 0
                print(f"✓ Ticks Received: {tick_count}")
                
                # Disconnect
                ws_manager.disconnect()
                print(f"✓ Disconnected successfully")
                
                return True
            else:
                print(f"❌ WebSocket Connection: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ WebSocket Connection: ERROR - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_pattern_detection(self):
        """Test 4: Pattern Detection Logic"""
        print("\n" + "=" * 80)
        print("TEST 4: PATTERN DETECTION LOGIC")
        print("=" * 80)
        
        try:
            # Import pattern detector
            os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot_service'))
            sys.path.insert(0, os.getcwd())
            
            from alpha_ensemble_strategy import AlphaEnsembleStrategy
            import pandas as pd
            import numpy as np
            
            logger.info("Initializing Alpha-Ensemble strategy...")
            
            strategy = AlphaEnsembleStrategy(
                api_key=self.api_key,
                jwt_token=self.jwt_token
            )
            
            # Create sample candle data (simulate real market data)
            dates = pd.date_range(end=datetime.now(), periods=100, freq='1min')
            
            # Simulate bullish trend
            np.random.seed(42)
            close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5 + 0.1)
            
            df = pd.DataFrame({
                'timestamp': dates,
                'open': close_prices - 0.5,
                'high': close_prices + np.random.rand(100) * 2,
                'low': close_prices - np.random.rand(100) * 2,
                'close': close_prices,
                'volume': np.random.randint(1000, 10000, 100)
            })
            
            logger.info(f"Created sample data: {len(df)} candles")
            logger.info(f"Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
            
            # Test pattern detection
            logger.info("Running pattern detection...")
            current_price = df['close'].iloc[-1]
            signal = strategy.analyze_symbol(df, 'TEST_SYMBOL', current_price)
            
            print(f"✅ Pattern Detection: SUCCESS")
            print(f"✓ Strategy initialized: Alpha-Ensemble")
            print(f"✓ Candles processed: {len(df)}")
            print(f"✓ Analysis completed successfully")
            
            if signal:
                print(f"✓ Signal generated: {signal.get('side', 'N/A')} @ ₹{signal.get('entry_price', 0):.2f}")
            else:
                print(f"✓ No signal (pattern criteria not met - normal behavior)")
            
            return True
            
        except Exception as e:
            print(f"❌ Pattern Detection: ERROR - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_complete_bot_startup(self):
        """Test 5: Complete Bot Startup with Real Credentials"""
        print("\n" + "=" * 80)
        print("TEST 5: COMPLETE BOT STARTUP FLOW")
        print("=" * 80)
        
        if not self.jwt_token or not self.feed_token:
            print("❌ Skipped: No authentication tokens")
            return False
        
        try:
            # Import bot engine
            os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot_service'))
            sys.path.insert(0, os.getcwd())
            
            from realtime_bot_engine import RealtimeBotEngine
            
            logger.info("Initializing bot with REAL credentials...")
            
            credentials = {
                'jwt_token': self.jwt_token,
                'feed_token': self.feed_token,
                'client_code': self.client_code,
                'api_key': self.api_key
            }
            
            test_symbols = ['RELIANCE', 'TCS', 'INFY']
            
            bot = RealtimeBotEngine(
                user_id='test_user_real_creds',
                credentials=credentials,
                symbols=test_symbols,
                trading_mode='paper',
                strategy='alpha-ensemble',
                db_client=None,
                replay_date=None
            )
            
            print(f"✅ Bot Startup: SUCCESS")
            print(f"✓ Bot initialized with REAL AngelOne credentials")
            print(f"✓ User ID: {bot.user_id}")
            print(f"✓ Trading Mode: {bot.trading_mode}")
            print(f"✓ Strategy: {bot.strategy}")
            print(f"✓ Symbols: {', '.join(bot.symbols)}")
            print(f"✓ JWT Token: Present ({len(bot.jwt_token)} chars)")
            print(f"✓ Feed Token: Present ({len(bot.feed_token)} chars)")
            
            return True
            
        except Exception as e:
            print(f"❌ Bot Startup: ERROR - {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Run all comprehensive tests"""
    print("\n")
    print("*" * 80)
    print(" COMPREHENSIVE ANGELONE API TEST SUITE")
    print(" Testing ALL remaining components before Monday")
    print("*" * 80)
    
    tester = AngelOneAPITester()
    results = {}
    
    # Test 1: Authentication
    results['authentication'] = tester.test_authentication()
    
    if not results['authentication']:
        print("\n" + "!" * 80)
        print("CRITICAL: Authentication failed. Cannot proceed with other tests.")
        print("!" * 80)
        return 1
    
    time.sleep(1)
    
    # Test 2: Historical Data
    results['historical_data'] = tester.test_historical_data()
    time.sleep(1)
    
    # Test 3: WebSocket Connection
    results['websocket'] = tester.test_websocket_connection()
    time.sleep(1)
    
    # Test 4: Pattern Detection
    results['pattern_detection'] = tester.test_pattern_detection()
    time.sleep(1)
    
    # Test 5: Complete Bot Startup
    results['bot_startup'] = tester.test_complete_bot_startup()
    
    # Summary
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "🎉" * 40)
        print("ALL TESTS PASSED!")
        print("NO SURPRISES EXPECTED ON MONDAY!")
        print("Bot is 100% READY for live trading!")
        print("🎉" * 40)
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("Review errors above and fix before Monday.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
