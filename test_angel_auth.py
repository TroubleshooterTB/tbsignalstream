#!/usr/bin/env python3
"""Test AngelOne API authentication"""
import os
import sys
import requests
import pyotp
from datetime import datetime

def test_angel_auth():
    print("=" * 80)
    print("TESTING ANGELONE API AUTHENTICATION")
    print("=" * 80)
    
    # Get credentials from environment
    api_key = os.getenv('ANGEL_API_KEY')
    client_id = os.getenv('ANGEL_CLIENT_ID')
    password = os.getenv('ANGEL_PASSWORD')
    totp_secret = os.getenv('ANGEL_TOTP_SECRET')
    
    if not all([api_key, client_id, password, totp_secret]):
        print("❌ ERROR: Missing AngelOne credentials in environment variables")
        sys.exit(1)
    
    print(f"✓ API Key: {api_key[:10]}...")
    print(f"✓ Client ID: {client_id}")
    print(f"✓ Password: ***")
    print(f"✓ TOTP Secret: {totp_secret[:10]}...")
    print()
    
    # Generate TOTP
    print("Generating TOTP...")
    totp = pyotp.TOTP(totp_secret)
    totp_code = totp.now()
    print(f"✓ TOTP Code: {totp_code}")
    print()
    
    # Test authentication
    print("Testing authentication with AngelOne API...")
    url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '192.168.1.1',
        'X-ClientPublicIP': '106.51.74.202',
        'X-MACAddress': '00:00:00:00:00:00',
        'X-PrivateKey': api_key
    }
    
    payload = {
        'clientcode': client_id,
        'password': password,
        'totp': totp_code
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        result = response.json()
        
        print()
        print("=" * 80)
        print("AUTHENTICATION RESULTS")
        print("=" * 80)
        
        if response.status_code == 200 and result.get('status') == True:
            print("✅ Authentication: SUCCESS")
            data = result.get('data', {})
            jwt_token = data.get('jwtToken', '')
            feed_token = data.get('feedToken', '')
            refresh_token = data.get('refreshToken', '')
            
            print(f"✓ JWT Token: {jwt_token[:50]}..." if jwt_token else "❌ No JWT token")
            print(f"✓ Feed Token: {feed_token[:30]}..." if feed_token else "❌ No feed token")
            print(f"✓ Refresh Token: {refresh_token[:30]}..." if refresh_token else "❌ No refresh token")
        else:
            print("❌ Authentication: FAILED")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {result}")
            sys.exit(1)
            
    except Exception as e:
        print("❌ Authentication: ERROR")
        print(f"Exception: {str(e)}")
        sys.exit(1)
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    test_angel_auth()
