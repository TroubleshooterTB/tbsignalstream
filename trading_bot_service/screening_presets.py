"""
Screening Mode Presets - Phase 3
Configurable screening levels: RELAXED, MEDIUM, STRICT
"""

from dataclasses import dataclass
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScreeningPreset:
    """Screening configuration preset"""
    name: str
    description: str
    
    # Screening layer enables
    enable_ma_crossover: bool
    enable_bb_squeeze: bool
    enable_var_limit: bool
    enable_sr_confluence: bool
    enable_gap_analysis: bool
    enable_nrb_trigger: bool
    enable_tick_indicator: bool
    enable_ml_filter: bool
    enable_retest_logic: bool
    
    # Risk limits
    max_portfolio_var_percent: float
    max_position_size_percent: float
    max_correlation_factor: float
    
    # Strategy parameters
    nifty_alignment_threshold: float
    vix_max_threshold: float
    adx_min_trending: float
    volume_multiplier: float
    rsi_long_min: float
    rsi_long_max: float
    rsi_short_min: float
    rsi_short_max: float
    max_distance_from_50ema: float
    atr_min_percent: float
    atr_max_percent: float
    
    # Expected outcomes
    expected_signals_per_day: int
    expected_pass_rate: float


# PRESET DEFINITIONS

RELAXED_PRESET = ScreeningPreset(
    name="RELAXED",
    description="Minimal screening - Maximum signal generation. Use for testing or aggressive trading.",
    
    # Screening - Only safety checks
    enable_ma_crossover=False,
    enable_bb_squeeze=False,
    enable_var_limit=True,
    enable_sr_confluence=False,
    enable_gap_analysis=False,
    enable_nrb_trigger=False,
    enable_tick_indicator=False,
    enable_ml_filter=False,
    enable_retest_logic=False,
    
    # Risk - Relaxed
    max_portfolio_var_percent=20.0,
    max_position_size_percent=10.0,
    max_correlation_factor=0.8,
    
    # Strategy - Loose parameters
    nifty_alignment_threshold=0.0,   # No market regime filter
    vix_max_threshold=35.0,          # Allow high volatility
    adx_min_trending=20.0,           # Lower trend requirement
    volume_multiplier=1.5,           # Lower volume requirement
    rsi_long_min=50.0,              # Wider RSI range
    rsi_long_max=70.0,
    rsi_short_min=30.0,
    rsi_short_max=50.0,
    max_distance_from_50ema=3.0,    # More flexibility
    atr_min_percent=0.08,           # Lower volatility threshold
    atr_max_percent=6.0,            # Higher volatility allowed
    
    expected_signals_per_day=20,
    expected_pass_rate=0.50         # 50% pass rate
)


MEDIUM_PRESET = ScreeningPreset(
    name="MEDIUM",
    description="Balanced screening - Quality signals with reasonable frequency.",
    
    # Screening - Partial enabled
    enable_ma_crossover=True,
    enable_bb_squeeze=False,
    enable_var_limit=True,
    enable_sr_confluence=True,
    enable_gap_analysis=False,
    enable_nrb_trigger=True,
    enable_tick_indicator=False,
    enable_ml_filter=True,
    enable_retest_logic=False,       # Direct breakout
    
    # Risk - Balanced
    max_portfolio_var_percent=15.0,
    max_position_size_percent=8.0,
    max_correlation_factor=0.6,
    
    # Strategy - Moderate parameters
    nifty_alignment_threshold=0.2,   # Partial market regime
    vix_max_threshold=25.0,          # Moderate volatility
    adx_min_trending=23.0,           # Moderate trend requirement
    volume_multiplier=2.0,           # Moderate volume
    rsi_long_min=52.0,
    rsi_long_max=65.0,
    rsi_short_min=35.0,
    rsi_short_max=48.0,
    max_distance_from_50ema=2.0,
    atr_min_percent=0.12,
    atr_max_percent=4.5,
    
    expected_signals_per_day=8,
    expected_pass_rate=0.15          # 15% pass rate
)


STRICT_PRESET = ScreeningPreset(
    name="STRICT",
    description="Maximum screening - Only highest quality signals. Low frequency, high accuracy.",
    
    # Screening - All enabled
    enable_ma_crossover=True,
    enable_bb_squeeze=True,
    enable_var_limit=True,
    enable_sr_confluence=True,
    enable_gap_analysis=True,
    enable_nrb_trigger=True,
    enable_tick_indicator=True,
    enable_ml_filter=True,
    enable_retest_logic=True,        # Wait for retest
    
    # Risk - Conservative
    max_portfolio_var_percent=12.0,
    max_position_size_percent=5.0,
    max_correlation_factor=0.4,
    
    # Strategy - Strict parameters
    nifty_alignment_threshold=0.3,   # Full market regime filter
    vix_max_threshold=22.0,          # Low volatility only
    adx_min_trending=25.0,           # Strong trend required
    volume_multiplier=2.5,           # High volume required
    rsi_long_min=55.0,               # Narrow RSI ranges
    rsi_long_max=65.0,
    rsi_short_min=35.0,
    rsi_short_max=45.0,
    max_distance_from_50ema=1.5,    # Close to EMA
    atr_min_percent=0.15,
    atr_max_percent=4.0,
    
    expected_signals_per_day=2,
    expected_pass_rate=0.005         # 0.5% pass rate (original)
)


# Preset registry
SCREENING_PRESETS: Dict[str, ScreeningPreset] = {
    'RELAXED': RELAXED_PRESET,
    'MEDIUM': MEDIUM_PRESET,
    'STRICT': STRICT_PRESET
}


def get_preset(mode: str) -> ScreeningPreset:
    """Get screening preset by name"""
    mode_upper = mode.upper()
    if mode_upper not in SCREENING_PRESETS:
        logger.warning(f"Unknown screening mode: {mode}. Defaulting to MEDIUM")
        return MEDIUM_PRESET
    return SCREENING_PRESETS[mode_upper]


def apply_preset_to_screening(screening_manager, preset: ScreeningPreset):
    """Apply preset configuration to AdvancedScreeningManager"""
    
    # Update screening enables
    screening_manager.enable_ma_crossover = preset.enable_ma_crossover
    screening_manager.enable_bb_squeeze = preset.enable_bb_squeeze
    screening_manager.enable_var_limit = preset.enable_var_limit
    screening_manager.enable_sr_confluence = preset.enable_sr_confluence
    screening_manager.enable_gap_analysis = preset.enable_gap_analysis
    screening_manager.enable_nrb_trigger = preset.enable_nrb_trigger
    screening_manager.enable_tick_indicator = preset.enable_tick_indicator
    screening_manager.enable_ml_filter = preset.enable_ml_filter
    screening_manager.enable_retest_logic = preset.enable_retest_logic
    
    # Update risk limits
    screening_manager.max_portfolio_var_percent = preset.max_portfolio_var_percent
    screening_manager.max_position_size_percent = preset.max_position_size_percent
    screening_manager.max_correlation_factor = preset.max_correlation_factor
    
    logger.info(f"✅ Applied {preset.name} screening preset")
    logger.info(f"   Expected: {preset.expected_signals_per_day} signals/day, {preset.expected_pass_rate*100:.1f}% pass rate")


def apply_preset_to_strategy(strategy_instance, preset: ScreeningPreset):
    """Apply preset configuration to AlphaEnsembleStrategy"""
    
    # Update strategy parameters
    strategy_instance.NIFTY_ALIGNMENT_THRESHOLD = preset.nifty_alignment_threshold
    strategy_instance.VIX_MAX_THRESHOLD = preset.vix_max_threshold
    strategy_instance.ADX_MIN_TRENDING = preset.adx_min_trending
    strategy_instance.VOLUME_MULTIPLIER = preset.volume_multiplier
    strategy_instance.RSI_LONG_MIN = preset.rsi_long_min
    strategy_instance.RSI_LONG_MAX = preset.rsi_long_max
    strategy_instance.RSI_SHORT_MIN = preset.rsi_short_min
    strategy_instance.RSI_SHORT_MAX = preset.rsi_short_max
    strategy_instance.MAX_DISTANCE_FROM_50EMA = preset.max_distance_from_50ema
    strategy_instance.ATR_MIN_PERCENT = preset.atr_min_percent
    strategy_instance.ATR_MAX_PERCENT = preset.atr_max_percent
    
    logger.info(f"✅ Applied {preset.name} strategy parameters")


def get_current_mode_stats() -> Dict[str, Any]:
    """Get statistics about all screening modes"""
    return {
        'modes': [
            {
                'name': preset.name,
                'description': preset.description,
                'expected_signals_per_day': preset.expected_signals_per_day,
                'expected_pass_rate': f"{preset.expected_pass_rate*100:.1f}%",
                'risk_level': {
                    'max_var': f"{preset.max_portfolio_var_percent}%",
                    'max_position': f"{preset.max_position_size_percent}%"
                }
            }
            for preset in SCREENING_PRESETS.values()
        ]
    }
