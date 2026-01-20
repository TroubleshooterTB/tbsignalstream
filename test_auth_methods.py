"""
Test different Angel One API endpoints and authentication methods
"""
import sys
sys.path.insert(0, 'trading_bot_service')

from SmartApi import SmartConnect
import requests
import json
from firebase_admin import credentials, firestore, initialize_app

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

print("TESTING DIFFERENT AUTHENTICATION METHODS")
print("="*60)

# Test 1: Print full credential details
print(f"Client Code: {creds.get('client_code')}")
print(f"API Key: {creds.get('api_key')}")
print(f"Full JWT: {creds.get('jwt_token')}")
print(f"Full Refresh: {creds.get('refresh_token')}")
print(f"Feed Token: {creds.get('feed_token')}")

# Test 2: Raw HTTP request to profile API
print(f"\n{'='*60}")
print("Testing DIRECT HTTP Profile API call...")
print(f"{'='*60}")

try:
    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getProfile"
    
    headers = {
        'Authorization': f'Bearer {creds.get("jwt_token")}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '192.168.1.1',
        'X-ClientPublicIP': '106.193.147.98',
        'X-MACAddress': '00:00:00:00:00:00',
        'X-PrivateKey': creds.get('api_key')
    }
    
    response = requests.post(url, headers=headers, json={})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"HTTP Error: {e}")

# Test 3: Try refreshing the token
print(f"\n{'='*60}")
print("Testing token refresh...")
print(f"{'='*60}")

try:
    smart_api = SmartConnect(api_key=creds['api_key'])
    
    # Try to refresh the token
    refresh_data = smart_api.generateToken(creds['refresh_token'])
    print(f"Refresh response: {refresh_data}")
    
    if refresh_data and refresh_data.get('status'):
        new_jwt = refresh_data['data']['jwtToken']
        print(f"New JWT token: {new_jwt[:30]}...")
        
        # Test with new token
        smart_api.setAccessToken(new_jwt)
        smart_api.setRefreshToken(creds['refresh_token'])
        
        profile = smart_api.getProfile(creds['refresh_token'])
        print(f"Profile with refreshed token: {profile}")
        
except Exception as e:
    print(f"Refresh error: {e}")

# Test 4: Check if we need to activate API access
print(f"\n{'='*60}")
print("Checking Angel One API subscription status...")
print(f"{'='*60}")

try:
    # Some brokers require API activation - let's try the user info endpoint
    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getProfile"
    
    # Try with different header combination
    headers = {
        'Authorization': f'Bearer {creds.get("jwt_token")}',
        'Content-Type': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-PrivateKey': creds.get('api_key')
    }
    
    payload = {
        'refreshToken': creds.get('refresh_token')
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Profile API with payload - Status: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"API subscription check error: {e}")

print(f"\n{'='*60}")
print("ANALYSIS:")
print("- If all responses show AG8001 'Invalid Token', the account may need API activation")
print("- Check Angel One app/portal for API subscription status")
print("- Some brokers require separate API access approval")
print(f"{'='*60}")