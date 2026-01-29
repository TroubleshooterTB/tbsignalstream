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
    Only works in PAPER mode
    """
    from main import user_bots
    from test_signal_injector import TestSignalInjector
    
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
        
        # Check bot running
        if user_id not in user_bots:
            return jsonify({'error': 'Bot not running'}), 400
        
        bot_instance = user_bots[user_id]
        
        # Verify paper mode
        if bot_instance.mode != 'paper':
            return jsonify({'error': 'Manual trades only work in PAPER mode'}), 403
        
        # Get current price if not provided
        if not price:
            with bot_instance.engine._lock:
                price = bot_instance.engine.latest_prices.get(symbol)
            
            if not price:
                return jsonify({'error': f'No price data for {symbol}'}), 400
        
        # Create manual signal
        manual_signal = create_manual_signal(
            symbol=symbol,
            action=action,
            price=price,
            quantity=quantity,
            stop_loss_pct=stop_loss_pct,
            target_pct=target_pct
        )
        
        # Inject via test injector
        injector = TestSignalInjector(bot_instance.engine)
        success = injector.inject_via_api(manual_signal)
        
        if success:
            logger.info(f"✅ Manual {action} placed: {symbol} @ {price:.2f}")
            return jsonify({
                'status': 'success',
                'message': f'Manual {action} order placed for {symbol}',
                'details': {
                    'symbol': symbol,
                    'action': action,
                    'entry': price,
                    'stop_loss': manual_signal['stop_loss'],
                    'target': manual_signal['target'],
                    'quantity': quantity
                }
            })
        else:
            return jsonify({'error': 'Failed to place manual order'}), 500
            
    except Exception as e:
        logger.error(f"Error placing manual trade: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@manual_trade_bp.route('/quick-close', methods=['POST'])
def manual_quick_close():
    """
    Manually close a specific position
    """
    from main import user_bots
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        symbol = data.get('symbol')
        
        if not user_id or user_id not in user_bots:
            return jsonify({'error': 'Bot not running'}), 400
        
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        bot_instance = user_bots[user_id]
        
        # Get position
        positions = bot_instance.engine._position_manager.get_all_positions()
        
        if symbol not in positions:
            return jsonify({'error': f'No open position for {symbol}'}), 404
        
        position = positions[symbol]
        
        # Get current price
        with bot_instance.engine._lock:
            current_price = bot_instance.engine.latest_prices.get(symbol, position['entry_price'])
        
        # Close position
        bot_instance.engine._close_position(
            symbol=symbol,
            position=position,
            exit_price=current_price,
            reason='MANUAL_CLOSE'
        )
        
        logger.info(f"✅ Manual close: {symbol} @ {current_price:.2f}")
        
        return jsonify({
            'status': 'success',
            'message': f'Position closed for {symbol}',
            'exit_price': current_price
        })
        
    except Exception as e:
        logger.error(f"Error closing position: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@manual_trade_bp.route('/close-all', methods=['POST'])
def manual_close_all():
    """
    Close all open positions immediately
    """
    from main import user_bots
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id or user_id not in user_bots:
            return jsonify({'error': 'Bot not running'}), 400
        
        bot_instance = user_bots[user_id]
        
        # Get all positions
        positions = bot_instance.engine._position_manager.get_all_positions()
        
        if not positions:
            return jsonify({'message': 'No open positions'}), 200
        
        closed_positions = []
        
        # Close each position
        for symbol, position in positions.items():
            try:
                with bot_instance.engine._lock:
                    current_price = bot_instance.engine.latest_prices.get(symbol, position['entry_price'])
                
                bot_instance.engine._close_position(
                    symbol=symbol,
                    position=position,
                    exit_price=current_price,
                    reason='MANUAL_CLOSE_ALL'
                )
                
                closed_positions.append({
                    'symbol': symbol,
                    'exit_price': current_price
                })
                
                logger.info(f"✅ Manual close: {symbol} @ {current_price:.2f}")
                
            except Exception as e:
                logger.error(f"Failed to close {symbol}: {e}")
        
        return jsonify({
            'status': 'success',
            'message': f'Closed {len(closed_positions)} positions',
            'closed': closed_positions
        })
        
    except Exception as e:
        logger.error(f"Error closing all positions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
