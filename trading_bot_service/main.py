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

# Initialize Firebase Admin
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

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
            # Import REAL-TIME bot engine
            from realtime_bot_engine import RealtimeBotEngine
            
            # Initialize real-time bot engine with WebSocket
            self.engine = RealtimeBotEngine(
                user_id=self.user_id,
                credentials=self.credentials,
                symbols=self.symbols,
                trading_mode=self.mode,
                strategy=self.strategy
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


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'active_bots': len(active_bots)
    }), 200


@app.route('/check-credentials', methods=['GET'])
def check_credentials():
    """Diagnostic endpoint to verify Angel One credentials are loaded"""
    try:
        credentials_status = {
            'ANGEL_ONE_API_KEY': 'SET' if os.environ.get('ANGEL_ONE_API_KEY') else 'MISSING',
            'ANGEL_ONE_API_SECRET': 'SET' if os.environ.get('ANGEL_ONE_API_SECRET') else 'MISSING',
            'ANGEL_ONE_CLIENT_CODE': 'SET' if os.environ.get('ANGEL_ONE_CLIENT_CODE') else 'MISSING',
            'ANGEL_ONE_PASSWORD': 'SET' if os.environ.get('ANGEL_ONE_PASSWORD') else 'MISSING',
            'ANGEL_ONE_TOTP_SECRET': 'SET' if os.environ.get('ANGEL_ONE_TOTP_SECRET') else 'MISSING',
        }
        
        # Show first 4 chars of API key for verification (safely)
        api_key = os.environ.get('ANGEL_ONE_API_KEY', '')
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
        
        # Get request data
        data = request.get_json() or {}
        symbols = data.get('symbols', ['RELIANCE', 'HDFCBANK', 'INFY'])
        interval = data.get('interval', '5minute')
        mode = data.get('mode', 'paper')  # 'paper' or 'live'
        strategy = data.get('strategy', 'pattern')  # 'pattern', 'ironclad', or 'both'
        
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
        
        # Create and start bot instance
        bot = TradingBotInstance(user_id, symbols, interval, credentials, mode, strategy)
        if bot.start():
            active_bots[user_id] = bot
            
            # Update Firestore status
            db.collection('bot_configs').document(user_id).set({
                'status': 'running',
                'symbols': symbols,
                'interval': interval,
                'mode': mode,
                'strategy': strategy,
                'started_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
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
            'stopped_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)
