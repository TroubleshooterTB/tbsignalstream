"""
Screening Mode API - Phase 3
Dynamic screening configuration
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

screening_api_bp = Blueprint('screening', __name__, url_prefix='/api/screening')


@screening_api_bp.route('/modes', methods=['GET'])
def get_screening_modes():
    """Get all available screening modes with statistics"""
    from screening_presets import get_current_mode_stats
    
    try:
        stats = get_current_mode_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting screening modes: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@screening_api_bp.route('/set-mode', methods=['POST'])
def set_screening_mode():
    """
    Change screening mode for a running bot
    Applies both screening and strategy parameter changes
    """
    from main import user_bots
    from screening_presets import get_preset, apply_preset_to_screening, apply_preset_to_strategy
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        mode = data.get('mode')  # RELAXED, MEDIUM, or STRICT
        
        if not user_id or not mode:
            return jsonify({'error': 'user_id and mode required'}), 400
        
        if user_id not in user_bots:
            return jsonify({'error': 'Bot not running'}), 400
        
        bot_instance = user_bots[user_id]
        
        # Get preset
        preset = get_preset(mode)
        
        # Apply to screening manager
        if bot_instance.engine._advanced_screening:
            apply_preset_to_screening(
                bot_instance.engine._advanced_screening,
                preset
            )
        
        # Apply to active strategies
        for strategy in bot_instance.engine.active_strategies:
            strategy_name = strategy.__class__.__name__
            
            if strategy_name == 'AlphaEnsembleStrategy':
                apply_preset_to_strategy(strategy, preset)
        
        # Save preference to Firestore
        from main import db
        from firebase_admin import firestore
        if db:
            db.collection('bot_configs').document(user_id).update({
                'screening_mode': preset.name,
                'screening_mode_updated': firestore.SERVER_TIMESTAMP
            })
        
        logger.info(f"✅ Screening mode changed to {preset.name} for user {user_id}")
        
        return jsonify({
            'status': 'success',
            'mode': preset.name,
            'description': preset.description,
            'expected_signals_per_day': preset.expected_signals_per_day,
            'expected_pass_rate': f"{preset.expected_pass_rate*100:.1f}%"
        })
        
    except Exception as e:
        logger.error(f"Error setting screening mode: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@screening_api_bp.route('/current-mode', methods=['GET'])
def get_current_mode():
    """Get current screening mode for a user"""
    from main import user_bots, db
    
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Try to get from bot first
        if user_id in user_bots:
            bot_instance = user_bots[user_id]
            
            if bot_instance.engine._advanced_screening:
                screening = bot_instance.engine._advanced_screening
                
                # Detect current mode based on enabled checks
                enabled_count = sum([
                    screening.enable_ma_crossover,
                    screening.enable_bb_squeeze,
                    screening.enable_sr_confluence,
                    screening.enable_gap_analysis,
                    screening.enable_nrb_trigger,
                    screening.enable_tick_indicator,
                    screening.enable_ml_filter,
                    screening.enable_retest_logic
                ])
                
                if enabled_count == 0:
                    detected_mode = 'RELAXED'
                elif enabled_count >= 7:
                    detected_mode = 'STRICT'
                else:
                    detected_mode = 'MEDIUM'
                
                return jsonify({
                    'mode': detected_mode,
                    'enabled_checks': enabled_count,
                    'max_var': f"{screening.max_portfolio_var_percent}%"
                })
        
        # Fall back to Firestore
        if db:
            config_doc = db.collection('bot_configs').document(user_id).get()
            if config_doc.exists:
                config_data = config_doc.to_dict()
                return jsonify({
                    'mode': config_data.get('screening_mode', 'MEDIUM')
                })
        
        # Default
        return jsonify({'mode': 'MEDIUM'})
        
    except Exception as e:
        logger.error(f"Error getting current mode: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
