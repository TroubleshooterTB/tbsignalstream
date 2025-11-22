# ==============================================================================
# FILE 2: src/trading/trading_bot.py
# PURPOSE: Analysis & Execution Engine
# This script is designed to be triggered periodically (e.g., every 5 mins).
# It fetches recent live data, aggregates it, analyzes it, and executes trades.
# ==============================================================================

import pandas as pd
import time
import os
import requests
import json
from datetime import datetime, timedelta
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, auth
from google.api_core import exceptions as google_exceptions
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Import all real, expert modules ---
from .execution_manager import ExecutionManager
from .position_manager import PositionManager
from .price_action_engine import AdvancedPriceActionAnalyzer
from .market_connector import MarketConnector

# --- Flask App Initialization ---
app = Flask(__name__)
# Broader CORS configuration to solve the "Failed to fetch" error
CORS(app)

# --- Firebase Admin SDK Initialization ---
try:
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase Admin already initialized or error: {e}")

db = firestore.client()

# Add a root route for diagnostics
@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "success", "message": "Trading Bot Backend is running."})

@app.route("/api/directAngelLogin", methods=["POST"])
def handle_login():
    """
    Handles a user's login request to Angel One, retrieves tokens, and securely
    stores them in a Firestore document tied to the authenticated Firebase user.
    """
    print("--- SECURE ANGEL ONE LOGIN INITIATED ---")

    # 1. Get Authorization header and verify Firebase ID token
    id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    if not id_token:
        return jsonify({"error": "Authentication token is required."}), 401
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Invalid authentication token."}), 401
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {e}"}), 401

    # 2. Get user-provided credentials from the request
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400
        
    client_code = data.get('clientCode')
    pin = data.get('pin')
    totp = data.get('totp')

    if not all([client_code, pin, totp]):
        return jsonify({"error": "Client Code, PIN, and TOTP are required."}), 400

    try:
        # In a deployed App Hosting environment, secrets are available as environment variables
        api_key = os.environ.get("ANGELONE_TRADING_API_KEY")
        if not api_key:
            print("CRITICAL: ANGELONE_TRADING_API_KEY secret is not set.")
            return jsonify({"error": "Server configuration error."}), 500

        # 3. Make the login request to Angel One API
        url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
        payload = {"clientcode": client_code, "password": pin, "totp": totp}
        headers = {
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
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('status') == True:
            session_data = response_data.get('data')
            if not session_data:
                 return jsonify({"error": "API response missing 'data' field."}), 500

            jwt_token = session_data.get('jwtToken')
            feed_token = session_data.get('feedToken')
            refresh_token = session_data.get('refreshToken')

            if not all([jwt_token, feed_token, refresh_token]):
                return jsonify({"error": "Login successful, but API response is missing required tokens."}), 500

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
                return jsonify({"error": "Login succeeded, but failed to save credentials."}), 500

            return jsonify({"status": "success", "message": "Angel One account connected successfully."}), 200
        else:
            message = response_data.get('message', 'Unknown error during login.')
            error_code = response_data.get('errorcode', 'N/A')
            print(f"Angel One Login Failed for {client_code}. Reason: {message} (Code: {error_code})")
            return jsonify({"error": message, "errorCode": error_code}), 401

    except requests.exceptions.Timeout:
        print(f"Request to Angel One timed out for {client_code}.")
        return jsonify({"error": "Connection to Angel One timed out."}), 504
    except requests.exceptions.RequestException as e:
        error_message = "Could not connect to the Angel One API."
        if e.response:
            try:
                error_details = e.response.json()
                error_message = error_details.get('message', error_message)
                print(f"Angel One API connection error for {client_code}: {error_message}")
            except json.JSONDecodeError:
                 print(f"Angel One API connection error for {client_code}: {e.response.text}")
        else:
            print(f"Angel One API connection error for {client_code}: {e}")
        return jsonify({"error": error_message}), 502
    except Exception as e:
        print(f"An unexpected error occurred during login for {client_code}: {e}")
        return jsonify({"error": f"An unexpected server error occurred: {str(e)}"}), 500

class TradingBot:
    """
    Orchestrates the trading analysis and execution cycle.
    """
    def __init__(self):
        print("--- TRADING BOT ENGINE INITIALIZING ---")
        self.db = firestore.client()
        self.market_connector = MarketConnector() # Assumes keys are set in environment
        self.price_action_analyzer = AdvancedPriceActionAnalyzer()
        self.execution_manager = ExecutionManager(self.market_connector, self.db)
        self.position_manager = PositionManager(self.market_connector, self.db)
        
        # --- Bot Configuration ---
        # In a real system, these would be fetched from a config file or Firestore
        self.symbols_to_scan = ["RELIANCE-EQ"] # Add more symbols to scan here
        self.nifty_symbol = "NIFTY 50"
        self.sector_map = {"RELIANCE-EQ": "NIFTY ENERGY"} # Map stocks to their sector index

    def log_message(self, message: str, level: str = "info"):
        """Logs a message to Firestore for the Command Center UI."""
        print(f"LOG ({level.upper()}): {message}")
        timestamp = firestore.SERVER_TIMESTAMP
        self.db.collection("bot_logs").add({
            "timestamp": timestamp,
            "message": message,
            "level": level
        })

    def get_live_ohlcv(self, symbol: str, timeframe: str, lookback_hours: int) -> pd.DataFrame:
        """
        Fetches recent raw ticks from Firestore and aggregates them into OHLCV bars.
        :param symbol: The stock or index symbol (e.g., 'RELIANCE-EQ').
        :param timeframe: The timeframe to resample to (e.g., '5min', '60min').
        :param lookback_hours: How many hours of data to fetch for indicator calculation.
        :return: A pandas DataFrame with OHLCV data, or None if not enough data.
        """
        print(f"Aggregating {timeframe} OHLCV for {symbol}...")
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=lookback_hours)

            # Query Firestore for ticks within the lookback period
            ticks_ref = self.db.collection('live_ticks').where('symbol', '==', symbol).where('server_timestamp', '>=', start_time).order_by('server_timestamp')
            docs = ticks_ref.stream()

            ticks = []
            for doc in docs:
                tick_data = doc.to_dict()
                # Ensure ltp and server_timestamp exist
                if 'ltp' in tick_data and 'server_timestamp' in tick_data:
                    ticks.append(tick_data)

            if len(ticks) < 10: # Need a minimum number of ticks to build bars
                self.log_message(f"Not enough recent ticks found for {symbol} to build OHLCV.", "warning")
                return None

            # Convert to DataFrame and process
            df = pd.DataFrame(ticks)
            df['server_timestamp'] = pd.to_datetime(df['server_timestamp'])
            df = df.set_index('server_timestamp')
            
            # Resample ticks into OHLCV bars
            ohlc_rules = {'ltp': 'ohlc', 'volume': 'sum'}
            df_resampled = df.resample(timeframe).apply(ohlc_rules)
            df_resampled.columns = ['open', 'high', 'low', 'close', 'volume']
            df_resampled = df_resampled.dropna()

            print(f"Successfully created {len(df_resampled)} {timeframe} bars for {symbol}.")
            return df_resampled

        except Exception as e:
            self.log_message(f"Error aggregating OHLCV data for {symbol}: {e}", "error")
            return None

    def run_analysis_cycle(self):
        """
        The main orchestration cycle. Designed to be run by a scheduler (e.g., every 5 mins).
        """
        self.log_message("--- Starting New Analysis Cycle ---")

        # First, manage any open positions
        self.position_manager.manage_open_positions()

        # Fetch fresh data for Nifty (broader market context)
        nifty_data = self.get_live_ohlcv(self.nifty_symbol, '5min', lookback_hours=24)
        if nifty_data is None:
            self.log_message("Could not get Nifty data. Skipping cycle.", "warning")
            return

        # Scan each symbol in our list
        for symbol in self.symbols_to_scan:
            # Check if we already have a position in this symbol
            if self.position_manager.is_position_open(symbol):
                self.log_message(f"Already have an open position for {symbol}. Skipping new signal scan.")
                continue

            self.log_message(f"--- Analyzing {symbol} ---")
            
            # Fetch data for the stock and its sector
            stock_data = self.get_live_ohlcv(symbol, '5min', lookback_hours=24)
            sector_symbol = self.sector_map.get(symbol)
            sector_data = self.get_live_ohlcv(sector_symbol, '5min', lookback_hours=24) if sector_symbol else nifty_data

            if stock_data is None or sector_data is None:
                self.log_message(f"Insufficient data for {symbol} or its sector. Skipping.", "warning")
                continue

            # Generate the trade signal using the advanced analyzer
            trade_signal = self.price_action_analyzer.generate_trade_signal(
                stock_data=stock_data,
                market_data=nifty_data,
                sector_data=sector_data
            )

            # Execute the trade if a signal is generated
            if trade_signal:
                self.log_message(f"High-confidence signal found for {symbol}: {trade_signal}", "info")
                self.execution_manager.execute_trade(symbol, trade_signal)
            else:
                self.log_message(f"No high-confidence signal found for {symbol}.")
        
        self.log_message("--- Analysis Cycle Complete ---")

# --- Cloud Functions Entry Point ---
def main(request):
    """
    Cloud Function entry point, triggered by Cloud Scheduler.
    """
    bot = TradingBot()
    bot.run_analysis_cycle()
    return 'Trading bot analysis cycle executed successfully.', 200

# This allows the script to be run directly for local testing.
if __name__ == '__main__':
    # This will run when the script is executed directly, not when deployed to App Hosting
    app.run(debug=True)
