"""
Test CoinDCX API Credentials
=============================
Simple test to verify API key and secret work correctly.
"""

import requests
import hashlib
import hmac
import time
import json

# Your API credentials
API_KEY = "043dce2b3c70dc1239f0c7543cd54e5986d6dd6b2e74667d"
API_SECRET = "d8e05055508bd86500eb984dbf6eac1a1466b1984096f02704e693bedeaeb456"

def test_balance():
    """Test getting balance (authenticated endpoint)"""
    
    endpoint = '/exchange/v1/users/balances'
    url = f'https://api.coindcx.com{endpoint}'
    
    # Create timestamp
    timestamp = int(time.time() * 1000)
    
    # Create body
    body = {
        "timestamp": timestamp
    }
    
    json_body = json.dumps(body, separators=(',', ':'))
    
    # Generate HMAC SHA256 signature
    signature = hmac.new(
        API_SECRET.encode(),
        json_body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature
    }
    
    print("=" * 60)
    print("Testing CoinDCX API Authentication")
    print("=" * 60)
    print(f"Endpoint: {url}")
    print(f"Timestamp: {timestamp}")
    print(f"Body: {json_body}")
    print(f"Signature: {signature}")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! API credentials are valid")
            data = response.json()
            print(f"\nBalances:")
            for balance in data[:5]:  # Show first 5
                if float(balance.get('balance', 0)) > 0:
                    print(f"   {balance['currency']}: {balance['balance']}")
        else:
            print(f"\n❌ FAILED! Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def test_ticker():
    """Test getting ticker (public endpoint - no authentication needed)"""
    
    url = 'https://api.coindcx.com/exchange/ticker'
    
    print("\n" + "=" * 60)
    print("Testing Public API (no authentication)")
    print("=" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Public API works!")
            data = response.json()
            # Find BTC/USDT
            for ticker in data:
                if ticker['market'] == 'BTCUSDT':
                    print(f"\nBTC/USDT Price: ${ticker['last_price']}")
                    break
        else:
            print(f"❌ Public API failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    # Test public API first
    test_ticker()
    
    # Then test authenticated API
    test_balance()
