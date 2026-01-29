"""
Test script to validate first trade execution
Run BEFORE market open to verify pipeline works
"""

import requests
import json
import time
import sys

# Configuration
TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app'

def get_user_id_token():
    """Get user ID and token from environment or prompt"""
    print("\n" + "="*80)
    print("🔐 AUTHENTICATION REQUIRED")
    print("="*80)
    print("\nYou need your Firebase ID token to test the bot.")
    print("Get it from: Browser DevTools → Application → Storage → IndexedDB → firebaseLocalStorage")
    print("\nOr use Firebase Admin SDK to generate a test token.")
    print()
    
    user_id = input("Enter your User ID: ").strip()
    id_token = input("Enter your ID Token: ").strip()
    
    return user_id, id_token

def test_inject_signal(user_id, id_token):
    """Test signal injection endpoint"""
    print("\n" + "="*80)
    print("🧪 TEST 1: Signal Injection")
    print("="*80)
    
    payload = {
        'symbol': 'RELIANCE'
    }
    
    headers = {
        'Authorization': f'Bearer {id_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{TRADING_BOT_SERVICE_URL}/api/test/inject-signal",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("\n✅ TEST PASSED: Signal injection working")
            return True, data
        else:
            print(f"Response: {response.text}")
            print("\n❌ TEST FAILED: Signal injection broken")
            return False, None
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False, None

def check_bot_status(user_id, id_token):
    """Check if bot is running"""
    print("\n" + "="*80)
    print("🤖 TEST 2: Bot Status Check")
    print("="*80)
    
    headers = {
        'Authorization': f'Bearer {id_token}'
    }
    
    try:
        response = requests.get(
            f"{TRADING_BOT_SERVICE_URL}/status",
            headers=headers,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            is_running = data.get('is_running', False)
            active_positions = data.get('active_positions', 0)
            
            print(f"\nBot Running: {is_running}")
            print(f"Active Positions: {active_positions}")
            
            if is_running:
                print("\n✅ TEST PASSED: Bot is running")
                return True, data
            else:
                print("\n⚠️  WARNING: Bot not running - start it first")
                return False, data
        else:
            print(f"Response: {response.text}")
            print("\n❌ TEST FAILED: Status check failed")
            return False, None
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False, None

def wait_for_position(user_id, id_token, timeout=10):
    """Wait for position to be created after signal injection"""
    print("\n" + "="*80)
    print("⏳ TEST 3: Position Creation (waiting 10 seconds...)")
    print("="*80)
    
    headers = {
        'Authorization': f'Bearer {id_token}'
    }
    
    for i in range(timeout):
        time.sleep(1)
        print(f"Checking... ({i+1}/{timeout})", end='\r')
        
        try:
            response = requests.get(
                f"{TRADING_BOT_SERVICE_URL}/status",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                active_positions = data.get('active_positions', 0)
                
                if active_positions > 0:
                    print(f"\n\n✅ TEST PASSED: Position created! ({active_positions} positions)")
                    return True, active_positions
                    
        except Exception as e:
            print(f"\nWarning: {e}")
            
    print(f"\n\n❌ TEST FAILED: No position created after {timeout} seconds")
    return False, 0

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 SIGNALSTREAM FIRST TRADE VALIDATION")
    print("="*80)
    print(f"Target: {TRADING_BOT_SERVICE_URL}")
    print(f"Mode: PAPER (safe testing)")
    print("="*80 + "\n")
    
    # Get authentication
    user_id, id_token = get_user_id_token()
    
    if not user_id or not id_token:
        print("\n❌ ERROR: Authentication required")
        sys.exit(1)
    
    # Run tests
    print("\n📋 RUNNING PRE-LAUNCH TESTS...")
    
    # Test 1: Check bot status first
    test1_passed, bot_data = check_bot_status(user_id, id_token)
    
    if not test1_passed:
        print("\n❌ CRITICAL: Bot not running!")
        print("   Action: Start the bot from dashboard first")
        sys.exit(1)
    
    # Test 2: Inject test signal
    test2_passed, signal_data = test_inject_signal(user_id, id_token)
    
    if not test2_passed:
        print("\n❌ CRITICAL: Signal injection failed!")
        print("   Action: Check Cloud Run logs for errors")
        sys.exit(1)
    
    # Test 3: Wait for position creation
    test3_passed, position_count = wait_for_position(user_id, id_token)
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Bot Status Check:   {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Signal Injection:   {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"Position Creation:  {'✅ PASS' if test3_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n" + "="*80)
        print("🎉 SUCCESS: First trade pipeline validated!")
        print("="*80)
        print("\n✅ READY FOR LIVE MARKET TESTING")
        print("\nNext Steps:")
        print("1. Monitor Cloud Run logs during market hours")
        print("2. Check dashboard for signals and positions")
        print("3. Target: 10+ paper trades today")
        print("="*80 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ FAILURE: Pipeline broken - DO NOT LAUNCH")
        print("="*80)
        print("\n⚠️  FIX ISSUES BEFORE MARKET OPEN")
        print("\nTroubleshooting:")
        print("1. Check Cloud Run logs: gcloud run services logs read trading-bot-service")
        print("2. Verify bot is in PAPER mode")
        print("3. Check Firestore bot_configs collection")
        print("4. Test again after fixes")
        print("="*80 + "\n")
        sys.exit(1)
