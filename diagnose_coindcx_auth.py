"""
Diagnose CoinDCX Authentication Issue
======================================
This script tests different authentication methods to find the issue.
"""

import requests
import hashlib
import hmac
import time
import json

API_KEY = "043dce2b3c70dc1239f0c7543cd54e5986d6dd6b2e74667d"
API_SECRET = "d8e05055508bd86500eb984dbf6eac1a1466b1984096f02704e693bedeaeb456"

print("=" * 80)
print("CoinDCX Authentication Diagnostics")
print("=" * 80)
print(f"\nAPI Key: {API_KEY}")
print(f"API Secret: {API_SECRET[:20]}...")
print()

# Test 1: Public endpoint (no auth)
print("[TEST 1] Public API - Get Market Status")
print("-" * 80)
try:
    response = requests.get('https://api.coindcx.com/exchange/v1/markets_details', timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Public API works! Found {len(data)} markets")
        # Find BTCUSDT
        for market in data:
            if market.get('symbol') == 'BTCUSDT':
                print(f"   BTC/USDT: {market}")
                break
    else:
        print(f"❌ Failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: User info endpoint
print("\n[TEST 2] User Info (Authenticated)")
print("-" * 80)

endpoint = '/exchange/v1/users/info'
url = f'https://api.coindcx.com{endpoint}'
timestamp = int(time.time() * 1000)

body = {
    "timestamp": timestamp
}

json_body = json.dumps(body, separators=(',', ':'))

# Generate signature
signature = hmac.new(
    API_SECRET.encode(),
    json_body.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    'Content-Type': 'application/json',
    'X-AUTH-APIKEY': API_KEY,
    'X-AUTH-SIGNATURE': signature
}

print(f"URL: {url}")
print(f"Body: {json_body}")
print(f"Signature: {signature}")
print(f"Headers: {headers}")

try:
    response = requests.post(url, json=body, headers=headers, timeout=10)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Authentication works!")
    else:
        print(f"❌ Authentication failed")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Balance endpoint (same as our bot uses)
print("\n[TEST 3] Balance Endpoint (Same as bot)")
print("-" * 80)

endpoint = '/exchange/v1/users/balances'
url = f'https://api.coindcx.com{endpoint}'
timestamp = int(time.time() * 1000)

body = {
    "timestamp": timestamp
}

json_body = json.dumps(body, separators=(',', ':'))

signature = hmac.new(
    API_SECRET.encode(),
    json_body.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    'Content-Type': 'application/json',
    'X-AUTH-APIKEY': API_KEY,
    'X-AUTH-SIGNATURE': signature
}

print(f"URL: {url}")
print(f"Body: {json_body}")
print(f"Signature: {signature}")

try:
    response = requests.post(url, json=body, headers=headers, timeout=10)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
    if response.status_code == 200:
        print("✅ Balance API works!")
        data = response.json()
        print(f"\nFound {len(data)} balances")
        for bal in data[:5]:
            if float(bal.get('balance', 0)) > 0:
                print(f"   {bal['currency']}: {bal['balance']}")
    else:
        print(f"❌ Failed")
        
        # Try to parse error
        try:
            error_data = response.json()
            print(f"Error message: {error_data.get('message', 'N/A')}")
            print(f"Error code: {error_data.get('code', 'N/A')}")
        except:
            pass
            
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)
print("\n✅ If public API works but authenticated fails:")
print("   - API credentials are invalid/expired")
print("   - API key needs to be activated on CoinDCX")
print("   - API permissions might be restricted")
print("\n❌ If all tests fail:")
print("   - Network/firewall issue")
print("   - CoinDCX API is down")
print()
