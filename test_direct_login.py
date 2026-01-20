"""
Test direct SmartAPI login to verify account status
"""
import sys
import pyotp
import requests
import json
sys.path.insert(0, 'trading_bot_service')

from firebase_admin import credentials, firestore, initialize_app

try:
    initialize_app(credentials.Certificate('../firestore-key.json'))
except:
    pass

db = firestore.client()
creds = db.collection('angel_one_credentials').document('default_user').get().to_dict()

print("TESTING DIRECT SMARTAPI LOGIN")
print("=" * 60)

# Generate fresh TOTP
totp = pyotp.TOTP(creds['totp_secret'])
fresh_totp = totp.now()
print(f"Generated TOTP: {fresh_totp}")

# Test login with raw HTTP request
login_url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"

login_payload = {
    "clientcode": creds['client_code'],
    "password": creds['password'], 
    "totp": fresh_totp
}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-UserType": "USER",
    "X-SourceID": "WEB",
    "X-ClientLocalIP": "192.168.1.1",
    "X-ClientPublicIP": "106.193.147.98", 
    "X-MACAddress": "00:00:00:00:00:00",
    "X-PrivateKey": creds['api_key']
}

print(f"Attempting login to: {login_url}")
print(f"Client Code: {creds['client_code']}")
print(f"API Key: {creds['api_key']}")

try:
    response = requests.post(login_url, json=login_payload, headers=headers, timeout=30)
    
    print(f"\nLogin Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text[:500]}...")
    
    if response.status_code == 200:
        try:
            response_data = response.json()
            if response_data.get('status') == True:
                print("✅ LOGIN SUCCESS!")
                print(f"JWT Token received: {response_data['data']['jwtToken'][:30]}...")
                
                # Try a simple API call with new token
                profile_url = "https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getProfile"
                
                profile_headers = {
                    "Authorization": f"Bearer {response_data['data']['jwtToken']}",
                    "Content-Type": "application/json",
                    "X-PrivateKey": creds['api_key']
                }
                
                profile_response = requests.post(profile_url, headers=profile_headers, json={})
                print(f"\nProfile API Test:")
                print(f"Status: {profile_response.status_code}")
                print(f"Response: {profile_response.text[:200]}...")
                
            else:
                print(f"❌ LOGIN FAILED: {response_data.get('message')}")
                
        except json.JSONDecodeError:
            print("❌ Invalid JSON response")
            
    else:
        print(f"❌ HTTP ERROR: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ REQUEST ERROR: {e}")

print(f"\n{'='*60}")
print("DIAGNOSIS:")
print("If login succeeds but profile fails = API access issue")
print("If login fails = Credential or account issue") 
print("If 'Request Rejected' = IP restriction or firewall")
print(f"{'='*60}")