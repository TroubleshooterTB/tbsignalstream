"""
User Settings API - Complete user configuration management
"""

from flask import Blueprint, request, jsonify
import secrets
import hashlib
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

settings_api_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@settings_api_bp.route('/user', methods=['GET'])
def get_user_settings():
    """Get all user settings"""
    from main import db
    
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Get user settings from Firestore
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        # Get bot config
        bot_config_doc = db.collection('bot_configs').document(user_id).get()
        bot_config = bot_config_doc.to_dict() if bot_config_doc.exists else {}
        
        # Get API keys (masked)
        api_keys_query = db.collection('api_keys').where('user_id', '==', user_id).stream()
        api_keys = []
        for key_doc in api_keys_query:
            key_data = key_doc.to_dict()
            api_keys.append({
                'id': key_doc.id,
                'name': key_data.get('name', 'Unnamed'),
                'key_prefix': key_data.get('key_prefix', 'sk_'),
                'permissions': key_data.get('permissions', []),
                'created_at': key_data.get('created_at'),
                'last_used': key_data.get('last_used')
            })
        
        settings = {
            'user_id': user_id,
            'email': user_data.get('email'),
            'telegram_enabled': user_data.get('telegram_enabled', False),
            'telegram_chat_id': user_data.get('telegram_chat_id'),
            'tradingview_webhook_secret': user_data.get('tradingview_webhook_secret'),
            'tradingview_bypass_screening': user_data.get('tradingview_bypass_screening', False),
            'screening_mode': bot_config.get('screening_mode', 'RELAXED'),
            'api_keys': api_keys,
            'notifications': {
                'email_enabled': user_data.get('email_notifications', False),
                'telegram_enabled': user_data.get('telegram_enabled', False),
                'trade_alerts': user_data.get('trade_alerts', True),
                'daily_summary': user_data.get('daily_summary', True)
            }
        }
        
        return jsonify(settings)
        
    except Exception as e:
        logger.error(f"Error getting user settings: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@settings_api_bp.route('/user', methods=['POST'])
def update_user_settings():
    """Update user settings"""
    from main import db
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Update user document
        user_ref = db.collection('users').document(user_id)
        update_data = {}
        
        # Telegram settings
        if 'telegram_enabled' in data:
            update_data['telegram_enabled'] = data['telegram_enabled']
        if 'telegram_chat_id' in data:
            update_data['telegram_chat_id'] = data['telegram_chat_id']
        if 'telegram_bot_token' in data:
            update_data['telegram_bot_token'] = data['telegram_bot_token']
        
        # TradingView settings
        if 'tradingview_webhook_secret' in data:
            update_data['tradingview_webhook_secret'] = data['tradingview_webhook_secret']
        if 'tradingview_bypass_screening' in data:
            update_data['tradingview_bypass_screening'] = data['tradingview_bypass_screening']
        
        # Notification settings
        if 'email_notifications' in data:
            update_data['email_notifications'] = data['email_notifications']
        if 'trade_alerts' in data:
            update_data['trade_alerts'] = data['trade_alerts']
        if 'daily_summary' in data:
            update_data['daily_summary'] = data['daily_summary']
        
        if update_data:
            user_ref.update(update_data)
            logger.info(f"✅ Updated settings for user {user_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Settings updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating user settings: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@settings_api_bp.route('/api-key/generate', methods=['POST'])
def generate_api_key():
    """Generate new API key for external integrations"""
    from main import db
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        name = data.get('name', 'Unnamed API Key')
        permissions = data.get('permissions', ['read'])
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Generate secure API key
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store in Firestore
        key_doc = db.collection('api_keys').add({
            'user_id': user_id,
            'name': name,
            'key_hash': key_hash,
            'key_prefix': api_key[:10],  # For display only
            'permissions': permissions,
            'rate_limit': 100,  # 100 requests per minute
            'created_at': datetime.now(),
            'last_used': None,
            'is_active': True
        })
        
        logger.info(f"✅ Generated API key for user {user_id}: {name}")
        
        return jsonify({
            'status': 'success',
            'api_key': api_key,  # ONLY shown once!
            'key_id': key_doc[1].id,
            'name': name,
            'permissions': permissions,
            'warning': 'Save this key now. It will not be shown again.'
        })
        
    except Exception as e:
        logger.error(f"Error generating API key: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@settings_api_bp.route('/api-key/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    """Revoke an API key"""
    from main import db
    
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Verify key belongs to user
        key_doc = db.collection('api_keys').document(key_id).get()
        
        if not key_doc.exists:
            return jsonify({'error': 'API key not found'}), 404
        
        key_data = key_doc.to_dict()
        if key_data['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete key
        db.collection('api_keys').document(key_id).delete()
        
        logger.info(f"✅ Deleted API key {key_id} for user {user_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'API key deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting API key: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@settings_api_bp.route('/telegram/test', methods=['POST'])
def test_telegram():
    """Test Telegram notification"""
    import requests
    
    try:
        data = request.get_json()
        bot_token = data.get('bot_token')
        chat_id = data.get('chat_id')
        
        if not bot_token or not chat_id:
            return jsonify({'error': 'bot_token and chat_id required'}), 400
        
        # Send test message
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': '✅ SignalStream Telegram integration test successful!'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': 'Test message sent successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Telegram API error: {response.text}'
            }), 400
        
    except Exception as e:
        logger.error(f"Error testing Telegram: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
