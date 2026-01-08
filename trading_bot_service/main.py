"""
Live Trading Bot Service - Cloud Run
Manages persistent WebSocket connections and live trading operations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth
import logging
import os
import threading
from typing import Dict
import json
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, origins=[
    'https://studio--tbsignalstream.us-central1.hosted.app',  # App Hosting (PRIMARY)
    'https://tbsignalstream.web.app',
    'https://tbsignalstream.firebaseapp.com',
    'http://localhost:3000'
], supports_credentials=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin with Workload Identity (ADC)
# Cloud Run automatically provides credentials via its service account
db = None
firestore_error = None

def initialize_firestore():
    """Initialize Firestore client with Workload Identity support"""
    global db, firestore_error
    
    if db is not None:
        return db
    
    try:
        if not firebase_admin._apps:
            # Use Application Default Credentials (works on Cloud Run, local with gcloud auth)
            # No need for explicit key file - Cloud Run provides credentials automatically
            firebase_admin.initialize_app()
            logger.info("✅ Firebase initialized with Application Default Credentials (Workload Identity)")
        
        db = firestore.client()
        logger.info("✅ Firestore client initialized successfully")
        firestore_error = None
        return db
        
    except Exception as e:
        error_msg = f"Failed to initialize Firestore: {str(e)}"
        logger.error(f"❌ {error_msg}")
        firestore_error = error_msg
        # Don't raise - let the app start so we can report the error via health endpoints
        return None

# Initialize Firestore at startup
initialize_firestore()

# Load Angel One API key from environment (check multiple possible names)
ANGEL_ONE_API_KEY = (
    os.environ.get('ANGELONE_TRADING_API_KEY', '') or 
    os.environ.get('ANGELONE_API_KEY', '') or 
    os.environ.get('ANGEL_ONE_API_KEY', '')
)
if not ANGEL_ONE_API_KEY:
    logger.warning("ANGELONE_TRADING_API_KEY environment variable not set")

# Store active bot instances
active_bots: Dict[str, 'TradingBotInstance'] = {}


def _get_symbols_from_universe(universe: str) -> list:
    """Get symbol list based on universe selection"""
    # Nifty 50 symbols (default)
    nifty50 = [
        'RELIANCE-EQ', 'TCS-EQ', 'HDFCBANK-EQ', 'INFY-EQ', 'ICICIBANK-EQ',
        'HINDUNILVR-EQ', 'ITC-EQ', 'BHARTIARTL-EQ', 'KOTAKBANK-EQ', 'BAJFINANCE-EQ',
        'LT-EQ', 'ASIANPAINT-EQ', 'AXISBANK-EQ', 'HCLTECH-EQ', 'MARUTI-EQ',
        'SUNPHARMA-EQ', 'TITAN-EQ', 'NESTLEIND-EQ', 'ULTRACEMCO-EQ', 'WIPRO-EQ',
        'NTPC-EQ', 'TATAMOTORS-EQ', 'BAJAJFINSV-EQ', 'TATASTEEL-EQ', 'TECHM-EQ',
        'ADANIENT-EQ', 'ONGC-EQ', 'COALINDIA-EQ', 'HINDALCO-EQ', 'INDUSINDBK-EQ',
        'EICHERMOT-EQ', 'DIVISLAB-EQ', 'BRITANNIA-EQ', 'DRREDDY-EQ', 'APOLLOHOSP-EQ',
        'CIPLA-EQ', 'GRASIM-EQ', 'HEROMOTOCO-EQ', 'ADANIPORTS-EQ', 'HINDZINC-EQ',
        'M&M-EQ', 'BPCL-EQ', 'TRENT-EQ', 'ADANIGREEN-EQ', 'LTIM-EQ',
        'SBIN-EQ', 'POWERGRID-EQ', 'JSWSTEEL-EQ', 'SHRIRAMFIN-EQ'
    ]
    
    if universe == 'NIFTY50':
        return nifty50
    elif universe == 'NIFTY100':
        # For now, return Nifty 50 (can be expanded later)
        return nifty50
    elif universe == 'NIFTY200':
        # For now, return Nifty 50 (can be expanded later)  
        return nifty50
    else:
        # Default to Nifty 50
        return nifty50


class TradingBotInstance:
    """Manages a single user's trading bot instance"""
    
    def __init__(self, user_id: str, symbols: list, interval: str, credentials: dict, mode: str = 'paper', strategy: str = 'pattern'):
        self.user_id = user_id
        self.symbols = symbols
        self.interval = interval
        self.credentials = credentials
        self.mode = mode
        self.strategy = strategy
        self.is_running = False
        self.thread = None
        self.engine = None  # Store engine reference for market data access
        
        logger.info(f"TradingBotInstance created for user {user_id} - Mode: {mode}, Strategy: {strategy}")
    
    def start(self):
        """Start the trading bot in a background thread"""
        if self.is_running:
            logger.warning(f"Bot already running for user {self.user_id}")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_bot, daemon=True)
        self.thread.start()
        
        logger.info(f"Bot started for user {self.user_id}")
        return True
    
    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info(f"Bot stopped for user {self.user_id}")
    
    def _run_bot(self):
        """Main bot execution loop - runs in background thread"""
        logger.info(f"Bot loop started for user {self.user_id}")
        
        try:
            # Check if replay mode
            is_replay = self.mode == 'replay'
            replay_date = self.credentials.get('replay_date') if is_replay else None
            
            if is_replay:
                logger.info(f"🔄 REPLAY MODE: Running bot simulation for {replay_date}")
            
            # Import REAL-TIME bot engine
            from realtime_bot_engine import RealtimeBotEngine
            
            # Initialize real-time bot engine with WebSocket
            self.engine = RealtimeBotEngine(
                user_id=self.user_id,
                credentials=self.credentials,
                symbols=self.symbols,
                trading_mode=self.mode,
                strategy=self.strategy,
                db_client=db,  # Pass Firestore client for Activity Logger
                replay_date=replay_date  # Pass replay date if in replay mode
            )
            
            # Run the bot (WebSocket-powered real-time execution)
            self.engine.start(running_flag=lambda: self.is_running)
            
        except Exception as e:
            logger.error(f"Bot error for user {self.user_id}: {e}", exc_info=True)
            self.is_running = False
            
            # Update status in Firestore
            try:
                db.collection('bot_configs').document(self.user_id).update({
                    'status': 'error',
                    'error_message': str(e),
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
            except Exception as firestore_err:
                logger.error(f"Failed to update error status: {firestore_err}")


@app.route('/system-status', methods=['GET'])
def system_status():
    """System status endpoint for dashboard error reporting"""
    global firestore_error
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'backend_operational': True,
        'firestore_connected': db is not None,
        'errors': [],
        'warnings': []
    }
    
    if firestore_error:
        status['errors'].append({
            'type': 'FIRESTORE_INITIALIZATION',
            'severity': 'CRITICAL',
            'message': firestore_error,
            'impact': 'Bot operations unavailable - cannot store signals or activity logs',
            'resolution': 'Check Cloud Run service account has Firestore permissions (roles/datastore.user)'
        })
    
    if not ANGEL_ONE_API_KEY:
        status['warnings'].append({
            'type': 'MISSING_API_KEY',
            'severity': 'WARNING',
            'message': 'Angel One API key not configured',
            'impact': 'Live trading unavailable'
        })
    
    return jsonify(status), 200


@app.route('/health-detailed', methods=['GET'])
def health_detailed():
    """Detailed health check with comprehensive bot status"""
    try:
        from health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        
        # Get detailed health status
        health_status = health_monitor.get_detailed_status()
        
        # Add active bot information
        health_status['active_bots'] = len(active_bots)
        health_status['bot_ids'] = list(active_bots.keys())
        
        # Add individual bot health if any bots are running
        if active_bots:
            health_status['bots'] = {}
            for user_id, bot_instance in active_bots.items():
                try:
                    bot_engine = bot_instance.bot
                    if bot_engine and hasattr(bot_engine, 'error_handler'):
                        error_summary = bot_engine.error_handler.get_error_summary()
                        health_status['bots'][user_id] = {
                            'running': bot_engine.is_running,
                            'strategy': bot_engine.strategy,
                            'mode': bot_engine.trading_mode,
                            'symbols': len(bot_engine.symbols),
                            'errors': error_summary
                        }
                except Exception as e:
                    health_status['bots'][user_id] = {
                        'error': f'Failed to get bot health: {str(e)}'
                    }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Failed to get detailed health: {e}")
        return jsonify({
            'error': 'Failed to get health status',
            'message': str(e),
            'active_bots': len(active_bots)
        }), 500


@app.route('/check-credentials', methods=['GET'])
def check_credentials():
    """Diagnostic endpoint to verify Angel One credentials are loaded"""
    try:
        # Check for credentials with multiple naming variants
        api_key = (
            os.environ.get('ANGELONE_TRADING_API_KEY', '') or
            os.environ.get('ANGELONE_API_KEY', '') or
            os.environ.get('ANGEL_ONE_API_KEY', '')
        )
        api_secret = (
            os.environ.get('ANGELONE_TRADING_SECRET', '') or
            os.environ.get('ANGELONE_API_SECRET', '') or
            os.environ.get('ANGEL_ONE_API_SECRET', '')
        )
        client_code = (
            os.environ.get('ANGELONE_CLIENT_CODE', '') or
            os.environ.get('ANGEL_ONE_CLIENT_CODE', '')
        )
        password = (
            os.environ.get('ANGELONE_PASSWORD', '') or
            os.environ.get('ANGEL_ONE_PASSWORD', '')
        )
        totp_secret = (
            os.environ.get('ANGELONE_TOTP_SECRET', '') or
            os.environ.get('ANGEL_ONE_TOTP_SECRET', '')
        )
        
        credentials_status = {
            'ANGELONE_TRADING_API_KEY': 'SET' if api_key else 'MISSING',
            'ANGELONE_TRADING_SECRET': 'SET' if api_secret else 'MISSING',
            'ANGELONE_CLIENT_CODE': 'SET' if client_code else 'MISSING',
            'ANGELONE_PASSWORD': 'SET' if password else 'MISSING',
            'ANGELONE_TOTP_SECRET': 'SET' if totp_secret else 'MISSING',
        }
        
        # Show first 4 chars of API key for verification (safely)
        api_key_preview = f"{api_key[:4]}..." if len(api_key) >= 4 else "EMPTY"
        
        all_set = all(status == 'SET' for status in credentials_status.values())
        
        from datetime import datetime
        
        return jsonify({
            'status': 'OK' if all_set else 'INCOMPLETE',
            'credentials': credentials_status,
            'api_key_preview': api_key_preview,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking credentials: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/start', methods=['POST'])
def start_bot():
    """Start trading bot for a user"""
    global firestore_error, db
    
    try:
        # Check if Firestore is available
        if db is None:
            error_response = {
                'error': 'Backend initialization failed',
                'details': firestore_error or 'Firestore not available',
                'severity': 'CRITICAL',
                'action': 'Please contact support - backend cannot connect to database'
            }
            logger.error(f"Bot start rejected: {error_response}")
            return jsonify(error_response), 503
        
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Get request data
        data = request.get_json() or {}
        symbol_universe = data.get('symbols', 'NIFTY50')  # 'NIFTY50', 'NIFTY100', 'NIFTY200'
        interval = data.get('interval', '5minute')
        mode = data.get('mode', 'paper')  # 'paper' or 'live'
        strategy = data.get('strategy', 'alpha-ensemble')  # Strategy selection
        
        # PHASE 3: Replay Mode Support
        replay_date = data.get('replay_date')  # Format: 'YYYY-MM-DD' e.g., '2024-12-20'
        is_replay_mode = replay_date is not None
        
        if is_replay_mode:
            logger.info(f"🔄 Starting bot in REPLAY MODE for date: {replay_date}")
            mode = 'replay'  # Override mode
        
        # Convert symbol universe to actual symbol list
        # For Alpha-Ensemble and other strategies with built-in screening,
        # we pass the universe name and let the strategy filter internally
        if strategy == 'alpha-ensemble':
            # Alpha-Ensemble does its own intelligent screening
            symbols = symbol_universe  # Pass universe name, not symbol list
            logger.info(f"Alpha-Ensemble will screen from {symbol_universe}")
        else:
            # Other strategies get the full symbol list from the universe
            symbols = _get_symbols_from_universe(symbol_universe)
            logger.info(f"Using {len(symbols)} symbols from {symbol_universe}")
        
        # Check if bot already running
        if user_id in active_bots and active_bots[user_id].is_running:
            return jsonify({'error': 'Trading bot already running'}), 400
        
        # Fetch user credentials from Firestore
        creds_doc = db.collection('angel_one_credentials').document(user_id).get()
        if not creds_doc.exists:
            return jsonify({'error': 'Angel One credentials not found. Please connect your account.'}), 400
        
        credentials = creds_doc.to_dict()
        required_fields = ['jwt_token', 'feed_token', 'client_code']
        if not all(credentials.get(field) for field in required_fields):
            return jsonify({'error': 'Incomplete credentials. Please reconnect your Angel One account.'}), 400
        
        # Add API key to credentials
        credentials['api_key'] = ANGEL_ONE_API_KEY
        
        # Add replay mode config if applicable
        if is_replay_mode:
            credentials['replay_date'] = replay_date
        
        # Create and start bot instance
        bot = TradingBotInstance(user_id, symbols, interval, credentials, mode, strategy)
        if bot.start():
            active_bots[user_id] = bot
            
            # Update Firestore status
            status_data = {
                'status': 'running',
                'is_running': True,  # CRITICAL: Add this flag for frontend bot status check
                'symbols': symbols,
                'interval': interval,
                'mode': mode,
                'strategy': strategy,
                'started_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'last_started': firestore.SERVER_TIMESTAMP
            }
            
            if is_replay_mode:
                status_data['replay_date'] = replay_date
                status_data['replay_mode'] = True
            
            db.collection('bot_configs').document(user_id).set(status_data, merge=True)
            
            return jsonify({
                'status': 'success',
                'message': f'Trading bot started for {len(symbols)} symbols (Mode: {mode}, Strategy: {strategy})',
                'symbols': symbols,
                'interval': interval,
                'mode': mode,
                'strategy': strategy
            }), 200
        else:
            return jsonify({'error': 'Failed to start bot'}), 500
    
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/stop', methods=['POST'])
def stop_bot():
    """Stop trading bot for a user"""
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Check if bot exists
        if user_id not in active_bots:
            return jsonify({'error': 'No active trading bot found'}), 404
        
        # Stop the bot
        bot = active_bots[user_id]
        bot.stop()
        del active_bots[user_id]
        
        # Update Firestore status
        db.collection('bot_configs').document(user_id).update({
            'status': 'stopped',
            'is_running': False,  # CRITICAL: Set to False when bot stops
            'stopped_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'last_stopped': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Trading bot stopped successfully'
        }), 200
    
    except Exception as e:
        logger.error(f"Error stopping bot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/status', methods=['GET'])
def bot_status():
    """Get status of all running bots"""
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Get bot status
        if user_id in active_bots:
            bot = active_bots[user_id]
            return jsonify({
                'running': bot.is_running,  # Boolean for frontend
                'status': 'running' if bot.is_running else 'stopped',
                'symbols': bot.symbols,
                'interval': bot.interval
            }), 200
        else:
            return jsonify({
                'running': False,  # Boolean for frontend
                'status': 'stopped'
            }), 200
    
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/market_data', methods=['POST'])
def market_data():
    """Get current market data for symbols"""
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Get request data
        data = request.get_json()
        exchange_tokens = data.get('exchangeTokens', [])
        
        if not exchange_tokens:
            return jsonify({'error': 'Invalid request: exchangeTokens array required'}), 400
        
        # Check if bot is running for this user
        if user_id not in active_bots:
            return jsonify({'data': {}}), 200  # Return empty data if bot not running
        
        bot = active_bots[user_id]
        
        # Get latest data from bot's WebSocket manager
        market_data_response = {}
        
        if hasattr(bot, 'engine') and bot.engine and hasattr(bot.engine, 'websocket_manager') and bot.engine.websocket_manager:
            ws_manager = bot.engine.websocket_manager
            
            for token in exchange_tokens:
                # Get latest tick data for this token
                if hasattr(ws_manager, 'latest_ticks') and token in ws_manager.latest_ticks:
                    tick = ws_manager.latest_ticks[token]
                    market_data_response[token] = {
                        'ltp': tick.get('last_traded_price', 0),
                        'open': tick.get('open_price_of_the_day', 0),
                        'high': tick.get('high_price_of_the_day', 0),
                        'low': tick.get('low_price_of_the_day', 0),
                        'close': tick.get('close_price_of_the_day', 0),
                        'volume': tick.get('volume_trade_for_the_day', 0),
                        'change': tick.get('last_traded_price', 0) - tick.get('close_price_of_the_day', 0),
                        'changePercent': ((tick.get('last_traded_price', 0) - tick.get('close_price_of_the_day', 0)) / tick.get('close_price_of_the_day', 1)) * 100 if tick.get('close_price_of_the_day', 0) > 0 else 0
                    }
        
        return jsonify({'data': market_data_response}), 200
    
    except Exception as e:
        logger.error(f"Error getting market data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health-check', methods=['GET'])
def bot_health_check():
    """Comprehensive bot health check"""
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Check if bot exists
        if user_id not in active_bots:
            return jsonify({
                'status': 'not_running',
                'running': False
            }), 200
        
        bot = active_bots[user_id]
        
        # Gather health metrics
        health = {
            'running': bot.is_running,
            'has_engine': bot.engine is not None,
            'websocket_connected': False,
            'num_prices': 0,
            'num_candles': 0,
            'num_symbols': 0,
            'warnings': [],
            'errors': []
        }
        
        if bot.engine:
            # WebSocket check
            if hasattr(bot.engine, 'ws_manager') and bot.engine.ws_manager:
                health['websocket_connected'] = getattr(bot.engine.ws_manager, 'is_connected', False)
            
            # Data checks
            if hasattr(bot.engine, 'latest_prices'):
                health['num_prices'] = len(bot.engine.latest_prices)
            if hasattr(bot.engine, 'candle_data'):
                health['num_candles'] = len(bot.engine.candle_data)
            if hasattr(bot.engine, 'symbol_tokens'):
                health['num_symbols'] = len(bot.engine.symbol_tokens)
        
        # Determine overall status
        if not health['websocket_connected']:
            health['errors'].append('WebSocket not connected - no real-time data')
        if health['num_prices'] == 0:
            health['errors'].append('No price data available')
        if health['num_candles'] == 0:
            health['errors'].append('No historical candle data')
        elif health['num_candles'] < health['num_symbols'] * 0.5:
            health['warnings'].append(f'Only {health["num_candles"]}/{health["num_symbols"]} symbols have data')
        
        # Overall status
        if health['errors']:
            health['overall_status'] = 'error'
        elif health['warnings']:
            health['overall_status'] = 'degraded'
        else:
            health['overall_status'] = 'healthy'
        
        return jsonify(health), 200
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/test-analysis', methods=['POST'])
def test_analysis():
    """
    TEST ENDPOINT: Manually trigger analysis for debugging
    Use this to verify bot analysis works even when market is closed
    """
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Check if bot is running
        if user_id not in active_bots or not active_bots[user_id].is_running:
            return jsonify({
                'error': 'Bot is not running. Please start the bot first.',
                'hint': 'Click "Start Trading Bot" in the dashboard'
            }), 400
        
        bot = active_bots[user_id]
        
        return jsonify({
            'status': 'success',
            'message': 'Bot is running! Check Cloud Run logs for analysis output.',
            'instructions': [
                '1. Wait 5-10 seconds',
                '2. Run: gcloud logging read ... (see USER_GUIDE.md)',
                '3. Look for: "📊 [DEBUG] Scanning X symbols..."',
                '4. If you see scanning logs, bot is working correctly!',
                '5. No signals during closed market is NORMAL'
            ],
            'bot_info': {
                'symbols': bot.symbols,
                'mode': bot.mode,
                'strategy': bot.strategy,
                'running': bot.is_running
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in test-analysis: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/positions', methods=['GET'])
def get_positions():
    """Get all open positions from the trading bot"""
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Check if bot is running for this user
        if user_id not in active_bots:
            return jsonify({'positions': []}), 200  # Return empty if bot not running
        
        bot = active_bots[user_id]
        
        # Get positions from bot's engine
        positions_list = []
        
        if hasattr(bot, 'engine') and bot.engine and hasattr(bot.engine, '_position_manager'):
            position_manager = bot.engine._position_manager
            
            if hasattr(position_manager, 'get_all_positions'):
                positions_dict = position_manager.get_all_positions()
                
                # Get latest prices for P&L calculation
                latest_prices = {}
                if hasattr(bot.engine, 'latest_prices'):
                    with bot.engine._lock:
                        latest_prices = bot.engine.latest_prices.copy()
                
                # Convert positions dict to list format for frontend
                for symbol, position in positions_dict.items():
                    entry_price = position.get('entry_price', 0)
                    quantity = position.get('quantity', 0)
                    current_price = latest_prices.get(symbol, entry_price)
                    
                    # Calculate P&L
                    pnl_rupees = (current_price - entry_price) * quantity
                    pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                    
                    positions_list.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'averagePrice': entry_price,
                        'currentPrice': current_price,
                        'pnl': pnl_rupees,
                        'pnlPercent': pnl_percent,
                        'stopLoss': position.get('stop_loss', 0),
                        'target': position.get('target', 0),
                        'orderId': position.get('order_id', ''),
                        'timestamp': position.get('timestamp', '').isoformat() if hasattr(position.get('timestamp', ''), 'isoformat') else str(position.get('timestamp', ''))
                    })
        
        return jsonify({'positions': positions_list}), 200
    
    except Exception as e:
        logger.error(f"Error getting positions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/orders', methods=['GET'])
def get_orders():
    """Get order history (both executed and pending)"""
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Fetch orders from Firestore (logged by bot)
        orders_ref = db.collection('order_history').where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50)
        docs = orders_ref.stream()
        
        orders_list = []
        for doc in docs:
            order_data = doc.to_dict()
            orders_list.append({
                'orderId': doc.id,
                'symbol': order_data.get('symbol', ''),
                'quantity': order_data.get('quantity', 0),
                'price': order_data.get('price', 0),
                'orderType': order_data.get('order_type', 'MARKET'),
                'transactionType': order_data.get('transaction_type', 'BUY'),
                'status': order_data.get('status', 'unknown'),
                'timestamp': order_data.get('timestamp', '').isoformat() if hasattr(order_data.get('timestamp', ''), 'isoformat') else str(order_data.get('timestamp', ''))
            })
        
        return jsonify({'orders': orders_list}), 200
    
    except Exception as e:
        logger.error(f"Error getting orders: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/signals', methods=['GET'])
def get_signals():
    """Get recent trading signals generated by bot"""
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Fetch recent signals from Firestore
        signals_ref = db.collection('trading_signals').where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20)
        docs = signals_ref.stream()
        
        signals_list = []
        for doc in docs:
            signal_data = doc.to_dict()
            signals_list.append({
                'id': doc.id,
                'symbol': signal_data.get('symbol', ''),
                'type': signal_data.get('type', 'BUY'),
                'price': signal_data.get('price', 0),
                'confidence': signal_data.get('confidence', 0),
                'signal_type': signal_data.get('signal_type', 'Breakout'),
                'rationale': signal_data.get('rationale', ''),
                'stop_loss': signal_data.get('stop_loss', 0),
                'target': signal_data.get('target', 0),
                'status': signal_data.get('status', 'open'),
                'timestamp': signal_data.get('timestamp', '').isoformat() if hasattr(signal_data.get('timestamp', ''), 'isoformat') else str(signal_data.get('timestamp', ''))
            })
        
        return jsonify({'signals': signals_list}), 200
    
    except Exception as e:
        logger.error(f"Error getting signals: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/clear-old-signals', methods=['POST'])
def clear_old_signals():
    """Close all old/stale trading signals"""
    try:
        # Verify Firebase ID token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        # Get all open signals for this user
        signals_ref = db.collection('trading_signals').where('user_id', '==', user_id).where('status', '==', 'open')
        docs = list(signals_ref.stream())
        
        count = 0
        for doc in docs:
            doc.reference.update({'status': 'closed'})
            count += 1
        
        logger.info(f"Closed {count} old signals for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully closed {count} old signals',
            'count': count
        }), 200
    
    except Exception as e:
        logger.error(f"Error clearing old signals: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/backtest', methods=['POST'])
def run_backtest():
    """
    Run backtest on historical data
    Independent of live trading - can run while bot is trading live
    """
    try:
        data = request.get_json()
        strategy = data.get('strategy', 'defining')
        start_date = data.get('start_date')  # Format: YYYY-MM-DD
        end_date = data.get('end_date')      # Format: YYYY-MM-DD
        symbols = data.get('symbols', 'NIFTY50')
        capital = data.get('capital', 100000)  # Default to ₹1L if not provided
        custom_params = data.get('custom_params')  # Custom strategy parameters
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Validate capital
        try:
            capital = float(capital)
            if capital <= 0:
                return jsonify({'error': 'Capital must be positive'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid capital amount'}), 400
        
        logger.info(f"Starting backtest: {strategy} from {start_date} to {end_date} with capital ₹{capital:,.0f}, symbols={symbols}")
        if custom_params:
            logger.info(f"Using custom parameters: {custom_params}")
        
        # Warn about NIFTY200 timeout risk with custom params
        if symbols == 'NIFTY200' and custom_params:
            logger.warning("⚠️ NIFTY200 with custom params may timeout. Consider using NIFTY100 instead.")
        
        # Import backtest runner
        from run_backtest_defining_order import run_backtest as execute_backtest
        
        # Run backtest (this is synchronous and may take time)
        logger.info("Executing backtest...")
        results = execute_backtest(
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            symbols=symbols,
            capital=capital,
            custom_params=custom_params
        )
        
        logger.info(f"Backtest completed. Results type: {type(results)}, Keys: {results.keys() if isinstance(results, dict) else 'N/A'}")
        logger.info(f"Total trades in results: {results.get('total_trades', 0)}")
        
        # Format results for frontend
        trades = []
        trades_data = results.get('trades', [])
        
        # Handle pandas DataFrame
        if hasattr(trades_data, 'to_dict'):
            trades_data = trades_data.to_dict('records')
        
        for trade in trades_data:
            trades.append({
                'symbol': trade.get('symbol', ''),
                'entry_time': str(trade.get('entry_time', '')),
                'entry_price': float(trade.get('entry_price', 0)),
                'exit_time': str(trade.get('exit_time', '')),
                'exit_price': float(trade.get('exit_price', 0)),
                'direction': trade.get('direction', 'BUY'),
                'pnl': float(trade.get('pnl', 0)),
                'pnl_pct': float(trade.get('pnl_pct', 0)),
                'win': float(trade.get('pnl', 0)) > 0,
                'reason': trade.get('reason', '')
            })
        
        # Calculate summary statistics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['win'])
        losing_trades = total_trades - winning_trades
        total_pnl = sum(t['pnl'] for t in trades)
        pnl_percentage = (total_pnl / capital * 100) if capital > 0 else 0
        
        wins = [t['pnl'] for t in trades if t['win']]
        losses = [abs(t['pnl']) for t in trades if not t['win']]
        
        summary = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'pnl_percentage': round(pnl_percentage, 2),
            'avg_win': sum(wins) / len(wins) if wins else 0,
            'avg_loss': sum(losses) / len(losses) if losses else 0,
            'max_win': max(wins) if wins else 0,
            'max_loss': max(losses) if losses else 0,
            'profit_factor': (sum(wins) / sum(losses)) if losses and sum(losses) > 0 else 0
        }
        
        return jsonify({
            'trades': trades,
            'summary': summary,
            'strategy': strategy,
            'start_date': start_date,
            'end_date': end_date
        }), 200
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Backtest error: {error_msg}", exc_info=True)
        
        # Provide helpful message for timeout errors
        if 'timeout' in error_msg.lower() or 'deadline' in error_msg.lower():
            error_msg = f"Backtest timeout - processing {data.get('symbols', 'NIFTY50')} takes too long. Try NIFTY50 or NIFTY100 instead."
        
        return jsonify({'error': error_msg}), 500


@app.route('/backtest/export/pdf', methods=['POST'])
def export_backtest_pdf():
    """
    Export backtest results to PDF with detailed trade log
    """
    try:
        data = request.get_json()
        
        # Get backtest results from request
        trades = data.get('trades', [])
        summary = data.get('summary', {})
        strategy = data.get('strategy', 'alpha-ensemble')
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        
        if not trades:
            return jsonify({'error': 'No trades data provided'}), 400
        
        # Import PDF exporter
        from backtest_pdf_export import export_backtest_to_pdf
        
        # Prepare results in expected format
        backtest_results = {
            'strategy_name': f"{strategy.replace('-', ' ').title()} Strategy",
            'initial_capital': summary.get('initial_capital', 100000),
            'capital': summary.get('initial_capital', 100000) + summary.get('total_pnl', 0),
            'win_rate': summary.get('win_rate', 0),
            'profit_factor': summary.get('profit_factor', 0),
            'trades': trades
        }
        
        # Generate PDF
        filename = f"backtest_{strategy}_{start_date}_{end_date}.pdf"
        pdf_path = export_backtest_to_pdf(backtest_results, filename)
        
        # Send file as response
        from flask import send_file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"PDF export error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK ENDPOINTS (for Cloud Run, Kubernetes, monitoring)
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Liveness probe - Is the service alive?
    Used by Cloud Run/Kubernetes to restart unhealthy containers
    
    Returns 200 if service is running, 503 if critical issues detected
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'trading-bot-service',
        'checks': {
            'firestore': db is not None,
            'active_bots': len(active_bots),
        }
    }
    
    # If Firestore is down, service is unhealthy
    if db is None:
        health_status['status'] = 'unhealthy'
        health_status['error'] = firestore_error or 'Firestore not initialized'
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200


@app.route('/readiness', methods=['GET'])
def readiness_check():
    """
    Readiness probe - Is the service ready to handle requests?
    Used by load balancers to route traffic
    
    Returns 200 when ready, 503 when not ready
    """
    if db is None:
        return jsonify({
            'status': 'not_ready',
            'reason': 'Firestore not initialized',
            'timestamp': datetime.now().isoformat()
        }), 503
    
    return jsonify({
        'status': 'ready',
        'timestamp': datetime.now().isoformat(),
        'active_bots': len(active_bots)
    }), 200


@app.route('/status', methods=['GET'])
def service_status():
    """
    Detailed service status for monitoring/debugging
    Not used for health checks - returns 200 even with issues
    """
    status = {
        'service': 'trading-bot-service',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': None,  # Could track this with start time
        'firestore': {
            'connected': db is not None,
            'error': firestore_error
        },
        'bots': {
            'active_count': len(active_bots),
            'active_users': list(active_bots.keys())
        },
        'environment': {
            'api_key_configured': bool(ANGEL_ONE_API_KEY),
            'port': int(os.environ.get('PORT', 8080)),
        }
    }
    
    return jsonify(status), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)
