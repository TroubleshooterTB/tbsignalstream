
import os
import requests
import json
import pyotp
from datetime import datetime, timedelta
from src.config import ANGEL_ONE_API
from src.data.historical_data_manager import HistoricalDataManager

# Firebase and Google Cloud imports
import firebase_admin
from firebase_admin import firestore, auth
from firebase_functions import options, https_fn
from google.api_core import exceptions as google_exceptions

# Import new function modules
from websocket_server import initializeWebSocket, subscribeWebSocket, closeWebSocket
from order_functions import placeOrder, modifyOrder, cancelOrder, getOrderBook, getPositions
from live_trading_bot import startLiveTradingBot, stopLiveTradingBot

# Import Ironclad Strategy (Sidecar Module)
from ironclad_logic import IroncladStrategy

# --- Firebase Admin SDK Initialization ---
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

# Export all functions so they're available as Cloud Function entry points
__all__ = [
    'directAngelLogin',
    'getMarketData',
    'initializeWebSocket',
    'subscribeWebSocket',
    'closeWebSocket',
    'placeOrder',
    'modifyOrder',
    'cancelOrder',
    'getOrderBook',
    'getPositions',
    'startLiveTradingBot',
    'stopLiveTradingBot',
    'runIroncladAnalysis'  # New Ironclad Strategy endpoint
]

@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"])
)
def directAngelLogin(request: https_fn.Request) -> https_fn.Response:
    """
    Handles a user's login request to Angel One, retrieves tokens, and securely
    stores them in a Firestore document tied to the authenticated Firebase user.
    """
    print("--- SECURE ANGEL ONE LOGIN INITIATED ---")

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

    # 2. Get user-provided credentials from the request
    data = request.get_json()
    client_code = data.get('clientCode')
    pin = data.get('pin')
    totp = data.get('totp')  # Optional - if not provided, we'll generate it

    if not all([client_code, pin]):
        return https_fn.Response(json.dumps({"error": "Client Code and PIN are required."}), status=400)

    try:
        # Read API key from normalized config (supports multiple env var names)
        api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        if not api_key:
            print("CRITICAL: ANGELONE_TRADING_API_KEY secret is not set.")
            return https_fn.Response(json.dumps({"error": "Server configuration error."}), status=500)
        
        # Generate TOTP if not provided by user
        if not totp:
            totp_secret = ANGEL_ONE_API.get('TOTP_SECRET')
            if not totp_secret:
                print("CRITICAL: ANGELONE_TOTP_SECRET is not set and TOTP was not provided.")
                return https_fn.Response(json.dumps({"error": "TOTP configuration error."}), status=500)
            try:
                totp_generator = pyotp.TOTP(totp_secret)
                totp = totp_generator.now()
                print(f"Auto-generated TOTP code: {totp}")
            except Exception as e:
                print(f"CRITICAL: Failed to generate TOTP: {e}")
                return https_fn.Response(json.dumps({"error": "TOTP generation failed."}), status=500)

        # 3. Make the login request to Angel One API
        url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
        payload = {"clientcode": client_code, "password": pin, "totp": totp}
        api_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': request.remote_addr or '127.0.0.1',
            'X-ClientPublicIP': request.remote_addr or '127.0.0.1',
            'X-MACAddress': '00:00:00:00:00:00',
            'X-PrivateKey': api_key
        }

        print(f"Attempting login for client code: {client_code}")
        print(f"Request URL: {url}")
        print(f"Request payload: {json.dumps(payload)}")
        print(f"Request headers (API key masked): {dict((k, '***' if k == 'X-PrivateKey' else v) for k, v in api_headers.items())}")
        
        try:
            response = requests.post(url, headers=api_headers, json=payload, timeout=15)
            print(f"Angel One API responded with status: {response.status_code}")
            print(f"Response content: {response.text[:500]}")  # First 500 chars
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.Timeout as timeout_err:
            print(f"CRITICAL: Request to Angel One timed out after 15s: {timeout_err}")
            return https_fn.Response(json.dumps({"error": "Connection to Angel One timed out."}), status=504)
        except requests.exceptions.RequestException as req_err:
            print(f"CRITICAL: Request to Angel One failed: {req_err}")
            if hasattr(req_err, 'response') and req_err.response is not None:
                print(f"Angel One error response: {req_err.response.text[:500]}")
            raise  # Re-raise to be caught by outer except block

        if response_data.get('status') == True:
            session_data = response_data.get('data')
            if not session_data:
                 return https_fn.Response(json.dumps({"error": "API response missing 'data' field."}), status=500)

            jwt_token = session_data.get('jwtToken')
            feed_token = session_data.get('feedToken')
            refresh_token = session_data.get('refreshToken')

            if not all([jwt_token, feed_token, refresh_token]):
                return https_fn.Response(json.dumps({"error": "Login successful, but API response is missing required tokens."}), status=500)

            # 4. Securely store tokens in Firestore for the specific user
            try:
                print(f"Saving tokens to Firestore for user: {uid}")
                user_doc_ref = db.collection('angel_one_credentials').document(uid)
                user_doc_ref.set({
                    'client_code': client_code,
                    'jwt_token': jwt_token,
                    'feed_token': feed_token,
                    'refresh_token': refresh_token,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }, merge=True)
                print("Tokens saved successfully.")
            except google_exceptions.GoogleAPICallError as e:
                print(f"CRITICAL: Firestore error for user {uid}: {e}")
                return https_fn.Response(json.dumps({"error": "Login succeeded, but failed to save credentials."}), status=500)

            return https_fn.Response(json.dumps({"status": "success", "message": "Angel One account connected successfully."}), status=200)
        else:
            message = response_data.get('message', 'Unknown error during login.')
            return https_fn.Response(json.dumps({"error": message}), status=401)

    except requests.exceptions.Timeout:
        return https_fn.Response(json.dumps({"error": "Connection to Angel One timed out."}), status=504)
    except requests.exceptions.RequestException as e:
        error_message = "Could not connect to the Angel One API."
        if e.response:
            try:
                error_details = e.response.json()
                error_message = error_details.get('message', error_message)
            except json.JSONDecodeError:
                pass
        return https_fn.Response(json.dumps({"error": error_message}), status=502)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return https_fn.Response(json.dumps({"error": f"An unexpected server error occurred: {str(e)}"}), status=500)


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"])
)
def getMarketData(request: https_fn.Request) -> https_fn.Response:
    """
    Fetches live market data for specified symbols using user's Angel One credentials.
    """
    print("--- MARKET DATA REQUEST INITIATED ---")

    # 1. Verify Firebase ID token
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
    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'LTP')  # LTP, OHLC, or FULL
    exchange_tokens = data.get('exchangeTokens', {"NSE": ["3045"]})  # Default: SBIN

    # 3. Retrieve user's Angel One credentials from Firestore
    try:
        user_doc_ref = db.collection('angel_one_credentials').document(uid)
        user_doc = user_doc_ref.get()
        
        if not user_doc.exists:
            return https_fn.Response(json.dumps({"error": "Angel One account not connected."}), status=403)
        
        user_data = user_doc.to_dict()
        jwt_token = user_data.get('jwt_token')
        
        if not jwt_token:
            return https_fn.Response(json.dumps({"error": "Invalid credentials. Please reconnect."}), status=403)
    
    except google_exceptions.GoogleAPICallError as e:
        print(f"CRITICAL: Firestore error for user {uid}: {e}")
        return https_fn.Response(json.dumps({"error": "Failed to retrieve credentials."}), status=500)

    # 4. Get API key
    api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
    if not api_key:
        print("CRITICAL: ANGELONE_TRADING_API_KEY secret is not set.")
        return https_fn.Response(json.dumps({"error": "Server configuration error."}), status=500)

    # 5. Fetch market data from Angel One
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

        print(f"Fetching market data: mode={mode}, tokens={exchange_tokens}")
        response = requests.post(url, headers=api_headers, json=payload, timeout=10)
        print(f"Angel One Market Data API responded: {response.status_code}")
        
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('status') == True:
            return https_fn.Response(json.dumps(response_data), status=200)
        else:
            message = response_data.get('message', 'Unknown error')
            return https_fn.Response(json.dumps({"error": message}), status=400)

    except requests.exceptions.Timeout:
        return https_fn.Response(json.dumps({"error": "Connection timeout."}), status=504)
    except requests.exceptions.RequestException as e:
        error_message = "Could not fetch market data."
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_message = error_details.get('message', error_message)
            except json.JSONDecodeError:
                pass
        print(f"CRITICAL: Market data request failed: {e}")
        return https_fn.Response(json.dumps({"error": error_message}), status=502)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return https_fn.Response(json.dumps({"error": str(e)}), status=500)


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["post"]),
    memory=options.MemoryOption.GB_1,
    timeout_sec=300
)
def runIroncladAnalysis(request: https_fn.Request) -> https_fn.Response:
    """
    Run Ironclad Strategy analysis on specified symbols.
    
    This is a standalone endpoint that demonstrates the Ironclad Strategy
    without modifying the existing live trading bot infrastructure.
    
    Request body:
    {
        "symbols": ["RELIANCE", "TCS"],  // Symbols to analyze
        "niftySymbol": "NIFTY50"          // Optional, defaults to NIFTY50
    }
    
    Returns:
    {
        "status": "success",
        "signals": {
            "RELIANCE": {
                "signal": "BUY",
                "entry_price": 2850.50,
                "stop_loss": 2820.00,
                "target": 2895.75,
                "regime": "BULLISH",
                "dr_high": 2855.00,
                "dr_low": 2830.00
            }
        }
    }
    """
    print("--- IRONCLAD STRATEGY ANALYSIS INITIATED ---")
    
    # 1. Verify Firebase ID token
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
    data = request.get_json(silent=True) or {}
    symbols = data.get('symbols', ['RELIANCE'])
    nifty_symbol = data.get('niftySymbol', 'NIFTY50')
    
    if not isinstance(symbols, list) or len(symbols) == 0:
        return https_fn.Response(json.dumps({"error": "Please provide at least one symbol"}), status=400)
    
    try:
        # 3. Get user's Angel One credentials
        user_doc_ref = db.collection('angel_one_credentials').document(uid)
        user_doc = user_doc_ref.get()
        
        if not user_doc.exists:
            return https_fn.Response(json.dumps({"error": "Angel One account not connected. Please connect first."}), status=403)
        
        user_data = user_doc.to_dict()
        jwt_token = user_data.get('jwt_token')
        api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        
        if not jwt_token or not api_key:
            return https_fn.Response(json.dumps({"error": "Invalid credentials or API key missing"}), status=403)
        
        # 4. Initialize Ironclad Strategy and Historical Data Manager
        strategy = IroncladStrategy(db)
        hist_manager = HistoricalDataManager(api_key, jwt_token)
        print(f"[Ironclad] Initialized strategy for {len(symbols)} symbols")
        
        # 5. Fetch historical data for NIFTY (used for regime detection)
        nifty_token, nifty_exchange = _get_symbol_token(nifty_symbol, api_key, jwt_token)
        if not nifty_token:
            return https_fn.Response(json.dumps({"error": f"Could not find token for {nifty_symbol}"}), status=400)
        
        # Fetch 30 days of 5-minute candles for NIFTY
        nifty_df = hist_manager.fetch_historical_data(
            symbol=nifty_symbol,
            token=nifty_token,
            exchange=nifty_exchange,
            interval="FIVE_MINUTE",
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now()
        )
        
        if nifty_df is None or len(nifty_df) == 0:
            return https_fn.Response(json.dumps({"error": f"No historical data available for {nifty_symbol}"}), status=500)
        
        # 6. Run analysis for each symbol
        signals = {}
        
        for symbol in symbols:
            try:
                print(f"[Ironclad] Analyzing {symbol}...")
                
                # Get token for this symbol
                stock_token, stock_exchange = _get_symbol_token(symbol, api_key, jwt_token)
                if not stock_token:
                    print(f"[Ironclad] Warning: Could not find token for {symbol}, skipping")
                    signals[symbol] = {
                        'signal': 'ERROR',
                        'message': f'Symbol token not found for {symbol}'
                    }
                    continue
                
                # Fetch stock historical data (30 days, 5-minute candles)
                stock_df = hist_manager.fetch_historical_data(
                    symbol=symbol,
                    token=stock_token,
                    exchange=stock_exchange,
                    interval="FIVE_MINUTE",
                    from_date=datetime.now() - timedelta(days=30),
                    to_date=datetime.now()
                )
                
                if stock_df is None or len(stock_df) == 0:
                    print(f"[Ironclad] Warning: No data for {symbol}")
                    signals[symbol] = {
                        'signal': 'ERROR',
                        'message': f'No historical data available for {symbol}'
                    }
                    continue
                
                # Run Ironclad analysis
                decision = strategy.run_analysis_cycle(nifty_df, stock_df, symbol)
                
                signals[symbol] = decision
                print(f"[Ironclad] {symbol} signal: {decision.get('signal')}")
                
            except Exception as e:
                print(f"[Ironclad] Error analyzing {symbol}: {e}")
                signals[symbol] = {
                    'signal': 'ERROR',
                    'message': str(e)
                }
        
        # 7. Return results
        return https_fn.Response(
            json.dumps({
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "signals": signals
            }),
            status=200
        )
        
    except Exception as e:
        print(f"[Ironclad] Unexpected error: {e}")
        return https_fn.Response(
            json.dumps({"error": f"Analysis failed: {str(e)}"}),
            status=500
        )


def _get_symbol_token(symbol: str, api_key: str, jwt_token: str):
    """
    Search for a symbol and get its token and exchange from Angel One API.
    
    Args:
        symbol: Trading symbol (e.g., 'RELIANCE', 'NIFTY50')
        api_key: Angel One API key
        jwt_token: User's JWT token
        
    Returns:
        Tuple of (token, exchange) or (None, None) if not found
    """
    try:
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/searchScrip"
        
        # Handle index symbols
        search_symbol = symbol
        if symbol == "NIFTY50":
            search_symbol = "NIFTY 50"
        elif symbol == "BANKNIFTY":
            search_symbol = "NIFTY BANK"
        
        payload = {
            "exchange": "NSE",
            "searchscrip": search_symbol
        }
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': '127.0.0.1',
            'X-ClientPublicIP': '127.0.0.1',
            'X-MACAddress': '00:00:00:00:00:00',
            'X-PrivateKey': api_key
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('status') and result.get('data'):
            # Get the first match
            data = result['data']
            if isinstance(data, list) and len(data) > 0:
                match = data[0]
                token = match.get('symboltoken')
                exchange = match.get('exch_seg', 'NSE')
                print(f"[Token Search] Found {symbol}: token={token}, exchange={exchange}")
                return token, exchange
        
        print(f"[Token Search] No match found for {symbol}")
        return None, None
        
    except Exception as e:
        print(f"[Token Search] Error searching for {symbol}: {e}")
        return None, None

