#!/usr/bin/env python3
"""Comprehensive Bot Engine Test - Tests initialization and basic functionality"""
import os
import sys
import time
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_bot_initialization():
    """Test bot engine initialization"""
    print("=" * 80)
    print("TESTING BOT ENGINE INITIALIZATION")
    print("=" * 80)
    print()
    
    # Import bot engine
    try:
        # Change to trading_bot_service directory for imports
        os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot_service'))
        sys.path.insert(0, os.getcwd())
        from realtime_bot_engine import RealtimeBotEngine
        print("✅ Successfully imported RealtimeBotEngine")
    except Exception as e:
        print(f"❌ Failed to import RealtimeBotEngine: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Mock credentials (bot will validate at runtime)
    credentials = {
        'jwt_token': 'test_jwt_token_placeholder',
        'feed_token': 'test_feed_token_placeholder',
        'client_code': 'TEST123',
        'api_key': 'test_api_key_placeholder'
    }
    
    # Test symbols (Nifty 50 sample)
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
    
    print(f"\nTest Configuration:")
    print(f"  User ID: test_user")
    print(f"  Trading Mode: paper")
    print(f"  Strategy: alpha-ensemble")
    print(f"  Symbols: {', '.join(test_symbols)}")
    print()
    
    # Initialize bot engine
    try:
        print("Initializing bot engine...")
        bot = RealtimeBotEngine(
            user_id='test_user',
            credentials=credentials,
            symbols=test_symbols,
            trading_mode='paper',
            strategy='alpha-ensemble',
            db_client=None,  # No Firestore for basic test
            replay_date=None
        )
        print("✅ Bot engine initialized successfully")
        print(f"  - User ID: {bot.user_id}")
        print(f"  - Trading Mode: {bot.trading_mode}")
        print(f"  - Strategy: {bot.strategy}")
        print(f"  - Symbols: {len(bot.symbols)} symbols")
        print(f"  - Replay Mode: {bot.is_replay_mode}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize bot engine: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test all critical imports"""
    print("\n" + "=" * 80)
    print("TESTING CRITICAL IMPORTS")
    print("=" * 80)
    print()
    
    # Change to trading_bot_service directory
    original_dir = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot_service'))
    sys.path.insert(0, os.getcwd())
    
    imports_to_test = [
        ('bot_errors', 'BotError'),
        ('error_handler', 'ErrorHandler'),
        ('health_monitor', 'HealthMonitor'),
        ('bot_activity_logger', 'BotActivityLogger'),
        ('realtime_bot_engine', 'RealtimeBotEngine'),
    ]
    
    all_passed = True
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")
            all_passed = False
    
    os.chdir(original_dir)
    return all_passed

def main():
    """Run all tests"""
    print("\n")
    print("*" * 80)
    print(" BOT ENGINE COMPREHENSIVE TEST SUITE")
    print("*" * 80)
    print()
    
    results = {}
    
    # Test 1: Imports
    results['imports'] = test_imports()
    
    # Test 2: Bot Initialization
    results['initialization'] = test_bot_initialization()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name.title()}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Bot engine is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
