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

# Load Angel One API key from environment
ANGEL_ONE_API_KEY = os.environ.get('ANGEL_ONE_API_KEY', '')
if not ANGEL_ONE_API_KEY:
    logger.warning("ANGEL_ONE_API_KEY environment variable not set")

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
            engine = RealtimeBotEngine(
                user_id=self.user_id,
                credentials=self.credentials,
                symbols=self.symbols,
                trading_mode=self.mode,
                strategy=self.strategy
            )
            
            # Run the bot (WebSocket-powered real-time execution)
            engine.start(running_flag=lambda: self.is_running)
            
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)
