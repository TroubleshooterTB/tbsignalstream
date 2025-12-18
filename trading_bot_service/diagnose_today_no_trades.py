"""
Diagnose Why No Trades Today (December 18, 2025)
Backtest today's date specifically and show detailed rejection reasons
"""

import sys
import os
from datetime import datetime, time
import logging
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the current strategy
import importlib.util
spec = importlib.util.spec_from_file_location(
    "strategy_module",
    os.path.join(os.path.dirname(__file__), "run_backtest_defining_order_v2.1_51PCT.py")
)
strategy_module = importlib.util.module_from_spec(spec)
sys.modules["strategy_module"] = strategy_module
spec.loader.exec_module(strategy_module)

DefiningOrderStrategy = strategy_module.DefiningOrderStrategy
generate_jwt_token = strategy_module.generate_jwt_token

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def diagnose_today():
    """Run detailed diagnostic for today's trading"""
    
    logger.info("=" * 100)
    logger.info("DIAGNOSING TODAY (December 18, 2025) - WHY NO TRADES?")
    logger.info("=" * 100)
    logger.info("")
    
    # Get credentials
    api_key = os.environ.get('ANGELONE_API_KEY', '')
    client_code = os.environ.get('ANGELONE_CLIENT_CODE', '')
    password = os.environ.get('ANGELONE_PASSWORD', '')
    totp = os.environ.get('ANGELONE_TOTP', '')
    
    if not api_key:
        logger.info("Please enter your Angel One credentials:")
        api_key = input("API Key: ").strip()
        client_code = input("Client Code: ").strip()
        password = input("Trading Password: ").strip()
        totp = input("TOTP (6-digit code): ").strip()
    
    # Generate JWT token
    logger.info("\n🔐 Logging in to Angel One...")
    jwt_token = generate_jwt_token(api_key, client_code, password, totp)
    
    if not jwt_token:
        logger.error("❌ Failed to generate JWT token. Cannot proceed.")
        return
    
    logger.info("✅ Login successful!")
    
    # Initialize strategy
    strategy = DefiningOrderStrategy(api_key, jwt_token)
    
    # Test with symbols that should trade
    symbols = [
        {'symbol': 'RELIANCE-EQ', 'token': '2885'},
        {'symbol': 'HDFCBANK-EQ', 'token': '1333'},
        {'symbol': 'INFY-EQ', 'token': '1594'},
        {'symbol': 'ICICIBANK-EQ', 'token': '4963'},
        {'symbol': 'TCS-EQ', 'token': '11536'},
    ]
    
    logger.info(f"\n📊 Testing with {len(symbols)} major symbols")
    logger.info("📅 Date: December 18, 2025 (TODAY)")
    logger.info("💰 Initial Capital: ₹100,000")
    logger.info("")
    logger.info("🔍 DETAILED ANALYSIS MODE - Will show ALL rejection reasons")
    logger.info("")
    
    # Run backtest for TODAY ONLY
    logger.info("🚀 Running backtest for today...\n")
    
    results = strategy.run_backtest(
        symbols=symbols,
        start_date="2025-12-18",
        end_date="2025-12-18",
        initial_capital=100000
    )
    
    logger.info("\n" + "=" * 100)
    logger.info("TODAY'S DIAGNOSTIC RESULTS")
    logger.info("=" * 100)
    
    if results['total_trades'] > 0:
        logger.info(f"\n✅ TRADES FOUND: {results['total_trades']} trade(s)")
        logger.info("\nThis means:")
        logger.info("  1. The backtest CAN find trades for today")
        logger.info("  2. But the LIVE bot did not take them")
        logger.info("  3. This indicates a LIVE vs BACKTEST discrepancy")
        logger.info("\nPossible causes:")
        logger.info("  - Defining Range not calculated correctly in live mode")
        logger.info("  - WebSocket data delays or missing candles")
        logger.info("  - Live filters behaving differently")
        logger.info("  - Paper trading mode disabled?")
        
        # Show trade details
        logger.info("\n📋 TRADE DETAILS:")
        trades_df = results['trades']
        for idx, trade in trades_df.iterrows():
            logger.info(f"\n  Trade {idx + 1}:")
            logger.info(f"    Symbol: {trade['symbol']}")
            logger.info(f"    Direction: {trade['direction']}")
            logger.info(f"    Entry: {trade['entry_time']} @ ₹{trade['entry_price']}")
            logger.info(f"    Exit: {trade['exit_time']} @ ₹{trade['exit_price']}")
            logger.info(f"    P&L: ₹{trade['pnl']:.2f}")
            logger.info(f"    Exit Reason: {trade['exit_reason']}")
            
    else:
        logger.info("\n❌ NO TRADES FOUND")
        logger.info("\nThis means:")
        logger.info("  1. Even the backtest couldn't find valid trades today")
        logger.info("  2. This is consistent with the live bot not trading")
        logger.info("  3. Today's market conditions don't meet strategy criteria")
        logger.info("\nCheck the detailed logs above for rejection reasons:")
        logger.info("  - Look for 'REJECTED' messages")
        logger.info("  - Common reasons: ATR too low, weak momentum, skip 13:00 hour, etc.")
        logger.info("  - The strategy filters are TOO STRICT for today's conditions")
    
    logger.info("\n" + "=" * 100)
    logger.info("NEXT STEPS")
    logger.info("=" * 100)
    
    if results['total_trades'] > 0:
        logger.info("\n1. Check live bot logs for defining range calculation")
        logger.info("2. Verify WebSocket is receiving all 5-min candles")
        logger.info("3. Compare live candle data vs historical data for today")
        logger.info("4. Check if paper trading mode is enabled")
    else:
        logger.info("\n1. Review rejection reasons in logs above")
        logger.info("2. Strategy filters are too strict - consider loosening:")
        logger.info("   - ATR minimum threshold (currently 0.15%)")
        logger.info("   - RSI thresholds (currently 55/45)")
        logger.info("   - Volume multipliers (currently 2.0x)")
        logger.info("   - Skip 13:00 hour rule")
        logger.info("3. Test with simpler v1.5 strategy")
    
    logger.info("\n" + "=" * 100)


if __name__ == "__main__":
    diagnose_today()
