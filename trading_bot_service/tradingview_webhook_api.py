"""
TradingView Webhook API - Phase 2
Receives webhook signals from TradingView alerts
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)

tradingview_webhook_bp = Blueprint('tradingview', __name__, url_prefix='/webhook')


def validate_tradingview_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validate TradingView webhook signature
    TradingView sends HMAC-SHA256 signature in X-TradingView-Signature header
    """
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Signature validation error: {e}")
        return False


def parse_tradingview_alert(data: Dict[str, Any]) -> tuple[bool, Dict[str, Any], str]:
    """
    Parse TradingView alert payload
    
    Expected format:
    {
        "symbol": "NSE:RELIANCE",
        "action": "BUY" or "SELL",
        "price": 2500.50,
        "stop_loss": 2450.00,  # Optional
        "target": 2625.00,     # Optional
        "stop_loss_pct": 2.0,  # Optional (used if stop_loss not provided)
        "target_pct": 5.0,     # Optional (used if target not provided)
        "quantity": 1,         # Optional
        "strategy": "MyStrategy",  # Optional
        "timestamp": "2026-01-30T09:30:00Z"  # Optional
    }
    """
    try:
        # Required fields
        if 'symbol' not in data or 'action' not in data:
            return False, {}, 'Missing required fields: symbol and action'
        
        symbol = data['symbol']
        action = data['action'].upper()
        
        # Clean symbol (remove exchange prefix if present)
        if ':' in symbol:
            symbol = symbol.split(':')[1]
        
        # Validate action
        if action not in ['BUY', 'SELL', 'CLOSE']:
            return False, {}, f'Invalid action: {action}. Must be BUY, SELL, or CLOSE'
        
        # Get price (required for BUY/SELL)
        price = data.get('price', 0)
        if action in ['BUY', 'SELL'] and not price:
            return False, {}, 'Price required for BUY/SELL actions'
        
        # Get or calculate stop loss and target
        stop_loss = data.get('stop_loss')
        target = data.get('target')
        
        if action in ['BUY', 'SELL']:
            # Calculate SL/Target if not provided
            if not stop_loss:
                stop_loss_pct = data.get('stop_loss_pct', 2.0)
                if action == 'BUY':
                    stop_loss = price * (1 - stop_loss_pct/100)
                else:
                    stop_loss = price * (1 + stop_loss_pct/100)
            
            if not target:
                target_pct = data.get('target_pct', 5.0)
                if action == 'BUY':
                    target = price * (1 + target_pct/100)
                else:
                    target = price * (1 - target_pct/100)
        
        # Build parsed signal
        parsed_signal = {
            'symbol': symbol,
            'action': action,
            'price': price,
            'stop_loss': stop_loss,
            'target': target,
            'quantity': data.get('quantity', 1),
            'strategy': data.get('strategy', 'TradingView'),
            'timestamp': data.get('timestamp'),
            'raw_data': data
        }
        
        return True, parsed_signal, ''
        
    except Exception as e:
        logger.error(f"Error parsing TradingView alert: {e}", exc_info=True)
        return False, {}, str(e)


@tradingview_webhook_bp.route('/tradingview', methods=['POST'])
def tradingview_webhook():
    """
    Receive TradingView webhook alerts
    
    Security:
    - Validates signature (if configured)
    - Requires API key in Authorization header
    - Validates alert format
    """
    from main import db
    from firebase_admin import firestore
    import uuid
    
    try:
        # Get API key from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        
        api_key = auth_header.replace('Bearer ', '')
        
        # Verify API key and get user_id from Firestore
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Query user by API key
        users_ref = db.collection('users')
        query = users_ref.where('trading_api_key', '==', api_key).limit(1).stream()
        
        user_doc = None
        for doc in query:
            user_doc = doc
            break
        
        if not user_doc:
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            return jsonify({'error': 'Invalid API key'}), 401
        
        user_id = user_doc.id
        user_data = user_doc.to_dict()
        
        # Validate signature (if webhook secret configured)
        webhook_secret = user_data.get('tradingview_webhook_secret')
        if webhook_secret:
            signature = request.headers.get('X-TradingView-Signature', '')
            if not signature:
                return jsonify({'error': 'Missing signature'}), 401
            
            if not validate_tradingview_signature(request.get_data(), signature, webhook_secret):
                logger.warning(f"Invalid webhook signature for user: {user_id}")
                return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse alert data
        alert_data = request.get_json()
        is_valid, parsed_signal, error_msg = parse_tradingview_alert(alert_data)
        
        if not is_valid:
            return jsonify({'error': f'Invalid alert format: {error_msg}'}), 400
        
        logger.info(f"📡 TradingView alert received: {parsed_signal['symbol']} {parsed_signal['action']}")
        
        # Handle CLOSE action
        if parsed_signal['action'] == 'CLOSE':
            symbol = parsed_signal['symbol']
            
            # Find open position
            positions_ref = db.collection('positions')
            query = positions_ref.where('user_id', '==', user_id).where('symbol', '==', symbol).where('status', '==', 'open').limit(1).stream()
            
            position_doc = None
            for doc in query:
                position_doc = doc
                break
            
            if not position_doc:
                return jsonify({'error': f'No open position for {symbol}'}), 404
            
            # Mark for closing
            position_doc.reference.update({
                'manual_close_requested': True,
                'close_source': 'tradingview',
                'manual_close_at': firestore.SERVER_TIMESTAMP,
                'status': 'closing'
            })
            
            return jsonify({
                'status': 'success',
                'action': 'CLOSE',
                'symbol': symbol,
                'message': 'Position marked for closing'
            })
        
        # Handle BUY/SELL actions
        # Convert to internal signal format
        direction = 'up' if parsed_signal['action'] == 'BUY' else 'down'
        
        # Create signal in Firestore
        signal_id = str(uuid.uuid4())
        signal_data = {
            'user_id': user_id,
            'signal_id': signal_id,
            'symbol': parsed_signal['symbol'],
            'action': parsed_signal['action'],
            'direction': direction,
            'entry_price': parsed_signal['price'],
            'stop_loss': parsed_signal['stop_loss'],
            'target': parsed_signal['target'],
            'quantity': parsed_signal['quantity'],
            'reason': f"TRADINGVIEW_{parsed_signal['strategy']}",
            'confidence': 0.85,  # TradingView signals = 85% confidence
            'source': 'tradingview',
            'status': 'pending',
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        # Check if user wants to bypass screening for TradingView
        if user_data.get('tradingview_bypass_screening', False):
            signal_data['bypass_screening'] = True
            logger.info(f"⚠️ TradingView signal bypassing screening (user preference)")
        else:
            signal_data['bypass_screening'] = False
        
        # Save signal to Firestore
        db.collection('signals').document(signal_id).set(signal_data)
        
        logger.info(f"✅ TradingView signal created: {signal_id} for {parsed_signal['symbol']}")
        
        return jsonify({
            'status': 'success',
            'signal_id': signal_id,
            'action': parsed_signal['action'],
            'symbol': parsed_signal['symbol'],
            'entry': parsed_signal['price'],
            'stop_loss': parsed_signal['stop_loss'],
            'target': parsed_signal['target'],
            'message': 'Signal created. Bot will process when running.'
        })
        
    except Exception as e:
        logger.error(f"TradingView webhook error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@tradingview_webhook_bp.route('/test', methods=['POST'])
def test_tradingview_webhook():
    """
    Test TradingView webhook integration
    No authentication required - for testing only
    """
    try:
        alert_data = request.get_json()
        is_valid, parsed_signal, error_msg = parse_tradingview_alert(alert_data)
        
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Alert format valid',
            'parsed_signal': parsed_signal
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
