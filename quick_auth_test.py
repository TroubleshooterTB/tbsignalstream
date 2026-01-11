#!/usr/bin/env python3
"""Quick authentication verification"""
import requests
import pyotp

totp = pyotp.TOTP('AGODKRXZZH6FHMYWMSBIK6KDXQ')
code = totp.now()
print(f'TOTP Generated: {code}')

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': '192.168.1.1',
    'X-ClientPublicIP': '106.51.74.202',
    'X-MACAddress': '00:00:00:00:00:00',
    'X-PrivateKey': 'jgosiGzs'
}

payload = {
    'clientcode': 'AABL713311',
    'password': '1012',
    'totp': code
}

r = requests.post('https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword', 
                  json=payload, headers=headers, timeout=10)

print(f'Status Code: {r.status_code}')
print(f'Response Text: {r.text[:200]}')

try:
    result = r.json()
    print(f'Authentication Success: {result.get("status")}')
    if result.get('status'):
        jwt = result.get('data', {}).get('jwtToken', 'N/A')
        print(f'JWT Token: {jwt[:50]}... ({len(jwt)} chars)')
    else:
        print(f'Error: {result.get("message", "Unknown error")}')
except:
    print(f'Could not parse JSON response')
