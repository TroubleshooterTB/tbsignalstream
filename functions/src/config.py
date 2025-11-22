# ==============================================================================
# Arcane Nexus - Live Tactical Alert Engine
# Central Configuration Module (config.py)
#
# This file centralizes all operational parameters for the trading bot.
# Modifying these values allows for strategy adjustments and risk management
# without altering the core logic of the bot's components.
# ==============================================================================

import os

# --- Trading & Risk Management Parameters ---
RISK_SETTINGS = {
    # The maximum percentage of total account equity to risk on a single trade.
    'RISK_PER_TRADE_PERCENT': 1.0,  # e.g., 1.0 means 1% of account equity

    # The total account equity. In a live environment, this should be fetched
    # dynamically from the broker API. For now, it's a static value.
    'ACCOUNT_EQUITY': 100000.0,  # Example: 100,000 units of currency
}

# --- Position Management Parameters ---
POSITION_MANAGEMENT = {
    # The ATR period used for calculating volatility-based trailing stops.
    'ATR_PERIOD': 14,

    # The multiplier for ATR to determine the trailing stop distance.
    # A higher value means a wider, more lenient stop.
    'TRAILING_STOP_ATR_FACTOR': 2.0,

    # The percentage of the position to sell at the first profit target.
    'SCALE_OUT_PERCENTAGE': 0.5,  # e.g., 0.5 means sell 50%
}

# --- Data Fetching & Analysis Parameters ---
DATA_ANALYSIS = {
    # The symbol of the instrument to trade.
    'SYMBOL': 'RELIANCE-EQ',  # Example for NSE

    # The timeframe for the chart data (e.g., '5minute', '1day').
    'INTERVAL': '5minute',

    # The number of historical bars to fetch for analysis.
    'DATA_LOOKBACK_PERIOD': 150,
}

# --- Pattern Detection Parameters ---
# These values tune the sensitivity of the pattern detection algorithms.
PATTERN_DETECTION = {
    'SWING_PROMINENCE_FACTOR': 0.015, # How significant a peak/trough must be to be considered a swing point
    'TRIANGLE_WEDGE_LOOKBACK': 30,    # Number of bars to look back for triangle/wedge patterns
    'FLAG_POLE_LOOKBACK': 15,         # Number of bars for the flag's pole
    'FLAG_LOOKBACK': 20,              # Number of bars for the flag's consolidation
    'DOUBLE_TOP_BOTTOM_LOOKBACK': 30, # Number of bars to look back for double tops/bottoms
}

# --- Angel One API Credentials ---
# IMPORTANT: These are placeholders. In a live environment, these values MUST be
# set as environment variables for security. The bot will read them from there.
# Using distinct environment variables for each API key type.
def _env_first(*names, default=None):
    """Return the first set environment variable from names, or default."""
    for n in names:
        v = os.environ.get(n)
        if v is not None and v != '':
            return v
    return default


# Normalize supported environment variable names for Angel One credentials.
# The repo historically uses several naming conventions (e.g. ANGELONE_TRADING_API_KEY
# vs ANGELONE_API_KEY_TRADING). This mapping tries common variants so code can
# read a single canonical value regardless of which name is set in the runtime.
ANGEL_ONE_API = {
    'API_KEY_HISTORICAL': _env_first('ANGELONE_HISTORICAL_API_KEY', 'ANGELONE_API_KEY_HISTORICAL', default='YOUR_HISTORICAL_API_KEY_HERE'),
    'API_KEY_TRADING': _env_first('ANGELONE_TRADING_API_KEY', 'ANGELONE_API_KEY_TRADING', default='YOUR_TRADING_API_KEY_HERE'),
    'API_KEY_PUBLISHER': _env_first('ANGELONE_PUBLISHER_API_KEY', 'ANGELONE_API_KEY_PUBLISHER', default='YOUR_PUBLISHER_API_KEY_HERE'),
    'API_KEY_MARKET': _env_first('ANGELONE_MARKET_API_KEY', 'ANGELONE_API_KEY_MARKET', default='YOUR_MARKET_API_KEY_HERE'),
    'CLIENT_CODE': _env_first('ANGELONE_CLIENT_CODE', 'ANGELONE_CLIENT', default='YOUR_CLIENT_CODE_HERE'),
    'PASSWORD': _env_first('ANGELONE_PASSWORD', 'ANGELONE_PASSWORD', default='YOUR_PASSWORD_HERE'),
    'TOTP_SECRET': _env_first('ANGELONE_TOTP_SECRET', 'ANGELONE_TOTP_TOKEN', default='YOUR_TOTP_SECRET_HERE'),
    'TRADING_API_SECRET': _env_first('ANGELONE_TRADING_SECRET', 'ANGELONE_TRADING_API_SECRET', default=None),
}

# --- Firestore Configuration ---
FIRESTORE_SETTINGS = {
    # Names of the Firestore collections the bot will write to for monitoring.
    'BOT_STATUS_COLLECTION': 'botStatus',
    'MARKET_DATA_COLLECTION': 'marketData',
    'DETECTED_PATTERNS_COLLECTION': 'detectedPatterns',
    'OPEN_POSITIONS_COLLECTION': 'openPositions',
    'CLOSED_POSITIONS_COLLECTION': 'closedPositions',
    'BOT_LOGS_COLLECTION': 'botLogs',
}

# --- Operational Mode ---
# 'PAPER' for simulated trading, 'LIVE' for real money trading.
# This acts as a master safety switch.
OPERATIONAL_MODE = 'PAPER' # CRITICAL: Change to 'LIVE' only when ready.
