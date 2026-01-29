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
    Change screening mode for a user
    Saves to Firestore - bot will load on next start
    """
    from main import db
    from firebase_admin import firestore
    from screening_presets import get_preset
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        mode = data.get('mode')  # RELAXED, MEDIUM, or STRICT
        
        if not user_id or not mode:
            return jsonify({'error': 'user_id and mode required'}), 400
        
        if mode not in ['RELAXED', 'MEDIUM', 'STRICT']:
            return jsonify({'error': 'Invalid mode. Must be RELAXED, MEDIUM, or STRICT'}), 400
        
        # Get preset
        preset = get_preset(mode)
        
        # Save to Firestore
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
            
        db.collection('bot_configs').document(user_id).set({
            'screening_mode': preset.name,
            'screening_mode_updated': firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        logger.info(f"✅ Screening mode changed to {preset.name} for user {user_id}")
        logger.info(f"   Bot will load this mode on next start")
        
        return jsonify({
            'status': 'success',
            'mode': preset.name,
            'description': preset.description,
            'expected_signals_per_day': preset.expected_signals_per_day,
            'expected_pass_rate': f"{preset.expected_pass_rate*100:.1f}%",
            'message': 'Screening mode saved. Restart bot to apply changes.'
        })
        
    except Exception as e:
        logger.error(f"Error setting screening mode: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@screening_api_bp.route('/current-mode', methods=['GET'])
def get_current_mode():
    """Get current screening mode for a user"""
    from main import db
    
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if not db:
            return jsonify({'error': 'Database not initialized'}), 500
        
        # Get from Firestore
        config = db.collection('bot_configs').document(user_id).get()
        
        if config.exists:
            data = config.to_dict()
            return jsonify({
                'user_id': user_id,
                'current_mode': data.get('screening_mode', 'RELAXED'),
                'updated_at': data.get('screening_mode_updated'),
                'source': 'firestore'
            })
        
        # Default
        return jsonify({
            'user_id': user_id,
            'current_mode': 'RELAXED',
            'source': 'default'
        })
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
        
        # Default
        return jsonify({
            'user_id': user_id,
            'current_mode': 'RELAXED',
            'source': 'default'
        })
        
    except Exception as e:
        logger.error(f"Error getting current mode: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
