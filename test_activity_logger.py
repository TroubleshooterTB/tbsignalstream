#!/usr/bin/env python3
"""Test Activity Logger Firestore Writes"""
import os
import sys
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_activity_logger():
    """Test activity logger writing to Firestore"""
    print("=" * 80)
    print("TESTING ACTIVITY LOGGER FIRESTORE WRITES")
    print("=" * 80)
    print()
    
    # Change to trading_bot_service directory
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot_service'))
    sys.path.insert(0, os.getcwd())
    
    # Import Firebase Admin
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        from bot_activity_logger import BotActivityLogger
        print("✅ Imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Initialize Firebase (if not already initialized)
    try:
        if not firebase_admin._apps:
            # Look for service account key
            key_path = '../key.json'
            if not os.path.exists(key_path):
                print(f"❌ Service account key not found at: {key_path}")
                print("   Using default credentials...")
                firebase_admin.initialize_app()
            else:
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized")
        else:
            print("✅ Firebase already initialized")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False
    
    # Get Firestore client
    try:
        db = firestore.client()
        print("✅ Firestore client created")
    except Exception as e:
        print(f"❌ Firestore client creation failed: {e}")
        return False
    
    # Initialize Activity Logger
    try:
        logger_obj = BotActivityLogger(user_id='test_user', db_client=db)
        print("✅ Activity Logger initialized")
    except Exception as e:
        print(f"❌ Activity Logger initialization failed: {e}")
        return False
    
    # Test writing activities
    print("\nTesting Activity Writes:")
    print("-" * 80)
    
    tests = []
    
    # Test 1: Bot Started
    try:
        print("\n1. Testing log_bot_started()...")
        logger_obj.log_bot_started(
            strategy='alpha-ensemble',
            mode='paper',
            symbols_count=3
        )
        print("   ✅ Bot started logged")
        tests.append(('log_bot_started', True))
    except Exception as e:
        print(f"   ❌ Bot started failed: {e}")
        tests.append(('log_bot_started', False))
    
    time.sleep(1)
    
    # Test 2: Scan Progress
    try:
        print("\n2. Testing log_scan_progress()...")
        logger_obj.log_scan_progress(
            current=5,
            total=10,
            symbol='RELIANCE'
        )
        print("   ✅ Scan progress logged")
        tests.append(('log_scan_progress', True))
    except Exception as e:
        print(f"   ❌ Scan progress failed: {e}")
        tests.append(('log_scan_progress', False))
    
    time.sleep(1)
    
    # Test 3: Pattern Detection
    try:
        print("\n3. Testing log_pattern_detected()...")
        logger_obj.log_pattern_detected(
            symbol='RELIANCE',
            pattern='Bullish Engulfing',
            confidence=85.5,
            rr_ratio=2.5,
            details={'timeframe': '15m', 'price': 2450.75}
        )
        print("   ✅ Pattern detection logged")
        tests.append(('log_pattern_detected', True))
    except Exception as e:
        print(f"   ❌ Pattern detection failed: {e}")
        tests.append(('log_pattern_detected', False))
    
    time.sleep(1)
    
    # Test 4: Signal Generated
    try:
        print("\n4. Testing log_signal_generated()...")
        logger_obj.log_signal_generated(
            symbol='RELIANCE',
            pattern='Bullish Engulfing',
            confidence=85.5,
            rr_ratio=2.5,
            entry_price=2450.75,
            stop_loss=2400.00,
            profit_target=2550.00
        )
        print("   ✅ Signal generation logged")
        tests.append(('log_signal_generated', True))
    except Exception as e:
        print(f"   ❌ Signal generation failed: {e}")
        tests.append(('log_signal_generated', False))
    
    # Verify data in Firestore
    print("\n" + "=" * 80)
    print("VERIFYING DATA IN FIRESTORE")
    print("=" * 80)
    
    try:
        activities = db.collection('bot_activity')\
            .where('user_id', '==', 'test_user')\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(10)\
            .stream()
        
        count = 0
        for activity in activities:
            count += 1
            data = activity.to_dict()
            print(f"\n{count}. {data.get('activity_type', 'Unknown')}")
            print(f"   Time: {data.get('timestamp', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')[:80]}...")
        
        if count > 0:
            print(f"\n✅ Found {count} activity entries in Firestore")
            tests.append(('firestore_verification', True))
        else:
            print("\n❌ No activity entries found in Firestore")
            tests.append(('firestore_verification', False))
            
    except Exception as e:
        print(f"\n❌ Firestore verification failed: {e}")
        tests.append(('firestore_verification', False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = test_activity_logger()
    sys.exit(0 if success else 1)
