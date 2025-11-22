import os
import requests
import json
from src.config import ANGEL_ONE_API

# Firebase and Google Cloud imports
import firebase_admin
from firebase_admin import firestore, auth
from firebase_functions import options, https_fn
from google.api_core import exceptions as google_exceptions

# --- Firebase Admin SDK Initialization ---
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"])
)
def getMarketData(request: https_fn.Request) -> https_fn.Response:
    """
    Fetches live market data for specified symbols using user's Angel One credentials.
    """
    print("--- MARKET DATA REQUEST INITIATED ---")

    # 1. Get Authorization header and verify Firebase ID token
    id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    if not id_token:
        return https_fn.Response(json.dumps({"error": "Authentication token is required."}), status=401)
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
    except auth.InvalidIdTokenError:
        return https_fn.Response(json.dumps({"error": "Invalid authentication token."}), status=401)
    except Exception as e:
        return https_fn.Response(json.dumps({"error": f"Token verification failed: {e}"}), status=401)

    # 2. Get request parameters
    data = request.get_json() if request.method == 'POST' else {}
    mode = data.get('mode', 'LTP')  # LTP, OHLC, or FULL
    exchange_tokens = data.get('exchangeTokens', {"NSE": ["3045"]})  # Default: SBIN

    # 3. Retrieve user's Angel One credentials from Firestore
    try:
        user_doc_ref = db.collection('angel_one_credentials').document(uid)
        user_doc = user_doc_ref.get()
        
        if not user_doc.exists:
            return https_fn.Response(json.dumps({"error": "Angel One account not connected. Please connect your account first."}), status=403)
        
        user_data = user_doc.to_dict()
        jwt_token = user_data.get('jwt_token')
        
        if not jwt_token:
            return https_fn.Response(json.dumps({"error": "Invalid credentials. Please reconnect your Angel One account."}), status=403)
    
    except google_exceptions.GoogleAPICallError as e:
        print(f"CRITICAL: Firestore error for user {uid}: {e}")
        return https_fn.Response(json.dumps({"error": "Failed to retrieve credentials."}), status=500)

    # 4. Get API key from config
    api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
    if not api_key:
        print("CRITICAL: ANGELONE_TRADING_API_KEY secret is not set.")
        return https_fn.Response(json.dumps({"error": "Server configuration error."}), status=500)

    # 5. Make request to Angel One Market Data API
    try:
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/quote/"
        payload = {
            "mode": mode,
            "exchangeTokens": exchange_tokens
        }
        
        api_headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': request.remote_addr or '127.0.0.1',
            'X-ClientPublicIP': request.remote_addr or '127.0.0.1',
            'X-MACAddress': '00:00:00:00:00:00',
            'X-PrivateKey': api_key
        }

        print(f"Fetching market data for mode={mode}, tokens={exchange_tokens}")
        response = requests.post(url, headers=api_headers, json=payload, timeout=10)
        print(f"Angel One API responded with status: {response.status_code}")
        
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('status') == True:
            return https_fn.Response(json.dumps(response_data), status=200)
        else:
            message = response_data.get('message', 'Unknown error while fetching market data.')
            return https_fn.Response(json.dumps({"error": message}), status=400)

    except requests.exceptions.Timeout:
        return https_fn.Response(json.dumps({"error": "Connection to Angel One timed out."}), status=504)
    except requests.exceptions.RequestException as e:
        error_message = "Could not connect to the Angel One API."
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_message = error_details.get('message', error_message)
            except json.JSONDecodeError:
                pass
        print(f"CRITICAL: Market data request failed: {e}")
        return https_fn.Response(json.dumps({"error": error_message}), status=502)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return https_fn.Response(json.dumps({"error": f"An unexpected server error occurred: {str(e)}"}), status=500)
