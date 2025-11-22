import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, auth

# Load test Angel One credentials from functions/.env.local that exists in the repo
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'functions', '.env.local')
params = {}
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if '=' in line:
                k, v = line.split('=', 1)
                v = v.strip().strip('"')
                params[k.strip()] = v

CLIENT_CODE = params.get('ANGELONE_CLIENT_CODE', 'AABL713311')
PIN = params.get('ANGELONE_PASSWORD', '1012')
TOTP = params.get('ANGELONE_TOTP_TOKEN', 'AGODKRXZZH6FHMYWMSBIK6KDXQ')

# Extracted Firebase Web API key from firebase-debug.log (found in repo)
# If you prefer to set it via env, set FIREBASE_API_KEY
API_KEY = os.environ.get('FIREBASE_API_KEY') or 'AIzaSyAg6TvwNWGZwEfCP5ZVbszIIBBFHPaEinc'

# Initialize Firebase Admin (Application Default Credentials)
if not firebase_admin._apps:
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print('Failed to initialize firebase_admin:', e)
        raise

# 1) Create custom token
uid = 'test-runner-' + os.urandom(4).hex()
print('Creating custom token for uid:', uid)
custom_token = auth.create_custom_token(uid).decode('utf-8')
print('Custom token created (length):', len(custom_token))

# 2) Exchange custom token for ID token via REST API
url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}'
body = {
    'token': custom_token,
    'returnSecureToken': True
}
print('Exchanging custom token for ID token...')
res = requests.post(url, json=body, timeout=20)
print('Exchange status:', res.status_code)
print('Exchange response:', res.text)
if res.status_code != 200:
    raise SystemExit('Failed to exchange custom token for ID token')
res_json = res.json()
id_token = res_json.get('idToken')
if not id_token:
    raise SystemExit('No idToken returned from exchange')
print('Obtained idToken (length):', len(id_token))

# 3) POST authenticated request to hosting endpoint
endpoint = 'https://tbsignalstream.web.app/api/directAngelLogin'
headers = {'Authorization': 'Bearer ' + id_token, 'Content-Type': 'application/json'}
payload = {'clientCode': CLIENT_CODE, 'pin': PIN, 'totp': TOTP}
print('POSTing to', endpoint)
resp = requests.post(endpoint, json=payload, headers=headers, timeout=30)
print('Response status:', resp.status_code)
try:
    print('Response JSON:', resp.json())
except Exception:
    print('Response text:', resp.text[:1000])

# Print helpful next steps
print('\nDone. If the request failed, check Cloud Run logs for `directangellogin` service.')
