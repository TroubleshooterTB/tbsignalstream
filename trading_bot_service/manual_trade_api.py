"""
Manual Trade API - Phase 1
Allows users to bypass all screening and place trades manually
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

manual_trade_bp = Blueprint('manual_trade', __name__, url_prefix='/api/manual')


def validate_manual_trade(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate manual trade request"""
    
    required_fields = ['user_id', 'symbol', 'action']
    for field in required_fields:
        if field not in data:
            return False, f'Missing required field: {field}'
    
    action = data.get('action')
    if action not in ['BUY', 'SELL']:
        return False, 'Action must be BUY or SELL'
    
    quantity = data.get('quantity', 1)
    if quantity < 1:
        return False, 'Quantity must be at least 1'
    
    stop_loss_pct = data.get('stop_loss_pct', 2.0)
    if stop_loss_pct < 0.5 or stop_loss_pct > 10:
        return False, 'Stop loss must be between 0.5% and 10%'
    
    target_pct = data.get('target_pct', 5.0)
    if target_pct < 1 or target_pct > 20:
        return False, 'Target must be between 1% and 20%'
    
    return True, ''


def create_manual_signal(symbol: str, action: str, price: float, 
                        quantity: int, stop_loss_pct: float, 
                        target_pct: float) -> Dict[str, Any]:
    """Create manual signal dict"""
    
    # Calculate SL and Target
    if action == 'BUY':
        stop_loss = price * (1 - stop_loss_pct/100)
        target = price * (1 + target_pct/100)
        direction = 'up'
    else:  # SELL
        stop_loss = price * (1 + stop_loss_pct/100)
        target = price * (1 - target_pct/100)
        direction = 'down'
    
    return {
        'symbol': symbol,
        'direction': direction,
        'entry_price': price,
        'stop_loss': stop_loss,
        'target': target,
        'quantity': quantity,
        'reason': f'MANUAL_OVERRIDE_{action}',
        'confidence': 1.0,  # Manual = 100% confidence
        'bypass_screening': True  # Force through
    }


@manual_trade_bp.route('/place-trade', methods=['POST'])
def place_manual_trade():
    """
    Place manual trade, bypassing all screening
    Creates signal in Firestore for bot to pick up
    """
    from main import db
    from firebase_admin import firestore
    import uuid
    
    try:
        data = request.get_json()
        
        # Validate request
        is_valid, error_msg = validate_manual_trade(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        user_id = data['user_id']
        symbol = data['symbol']
        action = data['action']
        quantity = data.get('quantity', 1)
        price = data.get('price')
        stop_loss_pct = data.get('stop_loss_pct', 2.0)
        target_pct = data.get('target_pct', 5.0)
        
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Get current price if not provided
        if not price:
            # Try to get from latest_prices collection
            price_doc = db.collection('latest_prices').document(symbol).get()
            if price_doc.exists:
                price = price_doc.to_dict().get('price')
            
            if not price:
                return jsonify({'error': f'No price data for {symbol}. Please provide price manually.'}), 400
        
        # Create manual signal
        manual_signal = create_manual_signal(
            symbol=symbol,
            action=action,
            price=price,
            quantity=quantity,
            stop_loss_pct=stop_loss_pct,
            target_pct=target_pct
        )
        
        # Save directly to Firestore
        signal_id = str(uuid.uuid4())
        signal_ref = db.collection('signals').document(signal_id)
        signal_ref.set({
            'user_id': user_id,
            'signal_id': signal_id,
            'symbol': symbol,
            'action': action,
            'entry_price': price,
            'quantity': quantity,
            'stop_loss': manual_signal['stop_loss'],
            'target': manual_signal['target'],
            'confidence': 1.0,
            'source': 'manual_trade',
            'bypass_screening': True,
            'status': 'pending',
            'created_at': firestore.SERVER_TIMESTAMP,
            'metadata': {
                'stop_loss_pct': stop_loss_pct,
                'target_pct': target_pct,
                'risk_reward': target_pct / stop_loss_pct
            }
        })
        
        logger.info(f"✅ Manual {action} placed: {symbol} @ {price:.2f} (signal_id: {signal_id})")
        
        return jsonify({
            'status': 'success',
            'message': f'Manual {action} order placed for {symbol}',
            'signal_id': signal_id,
            'details': {
                'symbol': symbol,
                'action': action,
                'entry': price,
                'stop_loss': manual_signal['stop_loss'],
                'target': manual_signal['target'],
                'quantity': quantity,
                'risk_reward': target_pct / stop_loss_pct
            }
        })
            
    except Exception as e:
        logger.error(f"Error placing manual trade: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@manual_trade_bp.route('/quick-close', methods=['POST'])
def manual_quick_close():
    """
    Manually close a specific position
    Updates position status in Firestore
    """
    from main import db
    from firebase_admin import firestore
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        symbol = data.get('symbol')
        
        if not user_id or not symbol:
            return jsonify({'error': 'user_id and symbol required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Find open position for this symbol
        positions_ref = db.collection('positions')
        query = positions_ref.where('user_id', '==', user_id).where('symbol', '==', symbol).where('status', '==', 'open').limit(1).stream()
        
        position_doc = None
        for doc in query:
            position_doc = doc
            break
        
        if not position_doc:
            return jsonify({'error': f'No open position found for {symbol}'}), 404
        
        position_data = position_doc.to_dict()
        
        # Mark position for closing
        position_doc.reference.update({
            'manual_close_requested': True,
            'manual_close_at': firestore.SERVER_TIMESTAMP,
            'status': 'closing'
        })
        
        logger.info(f"✅ Marked position {symbol} for manual close (user: {user_id})")
        
        return jsonify({
            'status': 'success',
            'message': f'Position {symbol} marked for closing',
            'details': {
                'symbol': symbol,
                'entry': position_data.get('entry_price'),
                'quantity': position_data.get('quantity')
            }
        })
        
    except Exception as e:
        logger.error(f"Error closing position: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@manual_trade_bp.route('/close-all', methods=['POST'])
def manual_close_all():
    """
    Close all open positions immediately
    Marks all positions for closing in Firestore
    """
    from main import db
    from firebase_admin import firestore
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Find all open positions for this user
        positions_ref = db.collection('positions')
        query = positions_ref.where('user_id', '==', user_id).where('status', '==', 'open').stream()
        
        closed_count = 0
        closed_symbols = []
        
        for doc in query:
            position_data = doc.to_dict()
            symbol = position_data.get('symbol')
            
            # Mark for closing
            doc.reference.update({
                'manual_close_requested': True,
                'manual_close_at': firestore.SERVER_TIMESTAMP,
                'status': 'closing'
            })
            
            closed_count += 1
            closed_symbols.append(symbol)
        
        logger.info(f"✅ Marked {closed_count} positions for manual close (user: {user_id})")
        
        if closed_count == 0:
            return jsonify({
                'status': 'success',
                'message': 'No open positions found',
                'closed_count': 0
            }), 200
        
        return jsonify({
            'status': 'success',
            'message': f'{closed_count} positions marked for closing',
            'closed_count': closed_count,
            'symbols': closed_symbols
        })
        
    except Exception as e:
        logger.error(f"Error closing all positions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
