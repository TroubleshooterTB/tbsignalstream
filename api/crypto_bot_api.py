"""
Crypto Bot API Endpoints
========================
REST API endpoints for controlling and monitoring the crypto trading bot.
"""

from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
crypto_api = Blueprint('crypto_api', __name__)

# Get Firestore client
db = firestore.client()


@crypto_api.route('/api/crypto/status', methods=['GET'])
def get_crypto_status():
    """
    Get current crypto bot status.
    
    Returns:
        JSON with bot status, active pair, positions, P&L
    """
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        # Get bot status
        status_doc = db.collection('crypto_bot_status').document(user_id).get()
        
        if not status_doc.exists:
            return jsonify({
                'success': False,
                'error': 'Bot not configured'
            }), 404
        
        status = status_doc.to_dict()
        
        # Get configuration
        config_doc = db.collection('crypto_bot_config').document(user_id).get()
        config = config_doc.to_dict() if config_doc.exists else {}
        
        return jsonify({
            'success': True,
            'status': status.get('status', 'unknown'),
            'is_running': status.get('is_running', False),
            'active_pair': status.get('active_pair', 'BTC'),
            'mode': config.get('mode', 'paper'),
            'strategy_day': config.get('strategy_day', 'momentum_scalping'),
            'strategy_night': config.get('strategy_night', 'mean_reversion'),
            'open_positions': status.get('open_positions', 0),
            'daily_pnl': status.get('daily_pnl', 0),
            'total_pnl': status.get('total_pnl', 0),
            'start_time': status.get('start_time'),
            'last_update': status.get('last_update'),
            'trading_enabled': config.get('trading_enabled', False)
        })
        
    except Exception as e:
        logger.error(f"Error getting crypto status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@crypto_api.route('/api/crypto/start', methods=['POST'])
def start_crypto_bot():
    """
    Start the crypto trading bot.
    
    Body:
        user_id: User identifier
        pair: BTC or ETH
    
    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        pair = data.get('pair', 'BTC')
        
        # Validate pair
        if pair not in ['BTC', 'ETH']:
            return jsonify({
                'success': False,
                'error': 'Invalid pair. Must be BTC or ETH'
            }), 400
        
        # Check if bot is already running
        status_doc = db.collection('crypto_bot_status').document(user_id).get()
        if status_doc.exists:
            status = status_doc.to_dict()
            if status.get('is_running', False):
                return jsonify({
                    'success': False,
                    'error': 'Bot is already running'
                }), 400
        
        # Update status to starting
        db.collection('crypto_bot_status').document(user_id).set({
            'status': 'starting',
            'is_running': False,
            'active_pair': pair,
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }, merge=True)
        
        # Update config
        db.collection('crypto_bot_config').document(user_id).update({
            'active_pair': pair
        })
        
        # Log activity
        db.collection('crypto_activity_feed').add({
            'user_id': user_id,
            'timestamp': datetime.now(),
            'type': 'BOT_START_REQUESTED',
            'message': f'Bot start requested for {pair}/USDT',
            'pair': pair
        })
        
        # Note: Actual bot startup happens in Cloud Run or local script
        # This endpoint just updates the database to signal the bot should start
        
        return jsonify({
            'success': True,
            'message': f'Bot start signal sent for {pair}/USDT',
            'pair': pair
        })
        
    except Exception as e:
        logger.error(f"Error starting crypto bot: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@crypto_api.route('/api/crypto/stop', methods=['POST'])
def stop_crypto_bot():
    """
    Stop the crypto trading bot.
    
    Body:
        user_id: User identifier
    
    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        
        # Update status to stopping
        db.collection('crypto_bot_status').document(user_id).update({
            'status': 'stopping',
            'stop_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        })
        
        # Log activity
        db.collection('crypto_activity_feed').add({
            'user_id': user_id,
            'timestamp': datetime.now(),
            'type': 'BOT_STOP_REQUESTED',
            'message': 'Bot stop requested'
        })
        
        return jsonify({
            'success': True,
            'message': 'Bot stop signal sent'
        })
        
    except Exception as e:
        logger.error(f"Error stopping crypto bot: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@crypto_api.route('/api/crypto/switch-pair', methods=['POST'])
def switch_crypto_pair():
    """
    Switch between BTC and ETH trading pairs.
    
    Body:
        user_id: User identifier
        pair: BTC or ETH
    
    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        new_pair = data.get('pair')
        
        # Validate pair
        if new_pair not in ['BTC', 'ETH']:
            return jsonify({
                'success': False,
                'error': 'Invalid pair. Must be BTC or ETH'
            }), 400
        
        # Get current status
        status_doc = db.collection('crypto_bot_status').document(user_id).get()
        if not status_doc.exists:
            return jsonify({
                'success': False,
                'error': 'Bot not configured'
            }), 404
        
        current_pair = status_doc.to_dict().get('active_pair', 'BTC')
        
        # Check if already on this pair
        if current_pair == new_pair:
            return jsonify({
                'success': True,
                'message': f'Already trading {new_pair}/USDT',
                'pair': new_pair
            })
        
        # Update config and status
        db.collection('crypto_bot_config').document(user_id).update({
            'active_pair': new_pair
        })
        
        db.collection('crypto_bot_status').document(user_id).update({
            'active_pair': new_pair,
            'last_update': datetime.now().isoformat()
        })
        
        # Log activity
        db.collection('crypto_activity_feed').add({
            'user_id': user_id,
            'timestamp': datetime.now(),
            'type': 'PAIR_SWITCHED',
            'message': f'Switched from {current_pair}/USDT to {new_pair}/USDT',
            'old_pair': current_pair,
            'new_pair': new_pair
        })
        
        return jsonify({
            'success': True,
            'message': f'Switched to {new_pair}/USDT',
            'old_pair': current_pair,
            'new_pair': new_pair
        })
        
    except Exception as e:
        logger.error(f"Error switching crypto pair: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@crypto_api.route('/api/crypto/activity', methods=['GET'])
def get_crypto_activity():
    """
    Get recent crypto bot activity feed.
    
    Query params:
        user_id: User identifier
        limit: Number of activities to return (default: 50)
    
    Returns:
        JSON with activity feed
    """
    try:
        user_id = request.args.get('user_id', 'default_user')
        limit = int(request.args.get('limit', 50))
        
        # Get recent activities
        activities = db.collection('crypto_activity_feed')\
            .where('user_id', '==', user_id)\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        
        activity_list = []
        for activity in activities:
            data = activity.to_dict()
            activity_list.append({
                'id': activity.id,
                'timestamp': data.get('timestamp').isoformat() if data.get('timestamp') else None,
                'type': data.get('type'),
                'message': data.get('message'),
                'pair': data.get('pair'),
                'price': data.get('price'),
                'quantity': data.get('quantity'),
                'pnl': data.get('pnl')
            })
        
        return jsonify({
            'success': True,
            'activities': activity_list,
            'count': len(activity_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting crypto activity: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@crypto_api.route('/api/crypto/positions', methods=['GET'])
def get_crypto_positions():
    """
    Get current open positions.
    
    Query params:
        user_id: User identifier
    
    Returns:
        JSON with open positions
    """
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        # Get positions from status
        status_doc = db.collection('crypto_bot_status').document(user_id).get()
        
        if not status_doc.exists:
            return jsonify({
                'success': False,
                'error': 'Bot not configured'
            }), 404
        
        status = status_doc.to_dict()
        positions = status.get('positions', [])
        
        return jsonify({
            'success': True,
            'positions': positions,
            'count': len(positions)
        })
        
    except Exception as e:
        logger.error(f"Error getting crypto positions: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@crypto_api.route('/api/crypto/config', methods=['GET'])
def get_crypto_config():
    """
    Get crypto bot configuration.
    
    Query params:
        user_id: User identifier
    
    Returns:
        JSON with bot configuration
    """
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        # Get config
        config_doc = db.collection('crypto_bot_config').document(user_id).get()
        
        if not config_doc.exists:
            return jsonify({
                'success': False,
                'error': 'Configuration not found'
            }), 404
        
        config = config_doc.to_dict()
        
        return jsonify({
            'success': True,
            'config': {
                'active_pair': config.get('active_pair', 'BTC'),
                'mode': config.get('mode', 'paper'),
                'trading_enabled': config.get('trading_enabled', False),
                'strategy_day': config.get('strategy_day', 'momentum_scalping'),
                'strategy_night': config.get('strategy_night', 'mean_reversion'),
                'risk_params': config.get('risk_params', {})
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting crypto config: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@crypto_api.route('/api/crypto/config', methods=['POST'])
def update_crypto_config():
    """
    Update crypto bot configuration.
    
    Body:
        user_id: User identifier
        mode: paper or live
        trading_enabled: boolean
    
    Returns:
        JSON with success status
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        
        # Build update dict
        updates = {}
        
        if 'mode' in data:
            if data['mode'] not in ['paper', 'live']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid mode. Must be paper or live'
                }), 400
            updates['mode'] = data['mode']
        
        if 'trading_enabled' in data:
            updates['trading_enabled'] = bool(data['trading_enabled'])
        
        if not updates:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
        
        # Update config
        db.collection('crypto_bot_config').document(user_id).update(updates)
        
        # Log activity
        db.collection('crypto_activity_feed').add({
            'user_id': user_id,
            'timestamp': datetime.now(),
            'type': 'CONFIG_UPDATED',
            'message': f'Configuration updated: {", ".join(updates.keys())}',
            'updates': updates
        })
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated',
            'updates': updates
        })
        
    except Exception as e:
        logger.error(f"Error updating crypto config: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@crypto_api.route('/api/crypto/stats', methods=['GET'])
def get_crypto_stats():
    """
    Get crypto bot statistics.
    
    Query params:
        user_id: User identifier
        days: Number of days to look back (default: 7)
    
    Returns:
        JSON with bot statistics
    """
    try:
        user_id = request.args.get('user_id', 'default_user')
        days = int(request.args.get('days', 7))
        
        # Get status
        status_doc = db.collection('crypto_bot_status').document(user_id).get()
        
        if not status_doc.exists:
            return jsonify({
                'success': False,
                'error': 'Bot not configured'
            }), 404
        
        status = status_doc.to_dict()
        
        # Get recent trades
        since = datetime.now() - timedelta(days=days)
        trades = db.collection('crypto_activity_feed')\
            .where('user_id', '==', user_id)\
            .where('type', 'in', ['TRADE_OPENED', 'TRADE_CLOSED'])\
            .where('timestamp', '>=', since)\
            .stream()
        
        trade_count = 0
        win_count = 0
        total_pnl = 0
        
        for trade in trades:
            trade_data = trade.to_dict()
            trade_count += 1
            
            pnl = trade_data.get('pnl', 0)
            if pnl > 0:
                win_count += 1
            total_pnl += pnl
        
        win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'daily_pnl': status.get('daily_pnl', 0),
                'total_pnl': status.get('total_pnl', 0),
                'open_positions': status.get('open_positions', 0),
                'total_trades': trade_count,
                'winning_trades': win_count,
                'win_rate': round(win_rate, 2),
                'period_days': days
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting crypto stats: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
