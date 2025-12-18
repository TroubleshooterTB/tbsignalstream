"""
Test v1.5 Strategy - Simpler Version Comparison
Run 1-year backtest with v1.5 to compare against v2.1 results
"""

import sys
import os
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import v1.5 strategy
import importlib.util
spec = importlib.util.spec_from_file_location(
    "strategy_v15",
    os.path.join(os.path.dirname(__file__), "run_backtest_defining_order_v1.5_FINAL_595PCT.py")
)
strategy_v15 = importlib.util.module_from_spec(spec)
sys.modules["strategy_v15"] = strategy_v15
spec.loader.exec_module(strategy_v15)

DefiningOrderStrategyV15 = strategy_v15.DefiningOrderStrategy
generate_jwt_token = strategy_v15.generate_jwt_token

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_v15_strategy():
    """Test v1.5 strategy with same 1-year period"""
    
    logger.info("=" * 100)
    logger.info("TESTING v1.5 STRATEGY (Simpler Version)")
    logger.info("=" * 100)
    logger.info("")
    logger.info("Comparison Test:")
    logger.info("  v2.1 Results: -39.34% (26.80% WR, 153 trades)")
    logger.info("  v1.5 Claims:  'FINAL_595PCT' - Should be better")
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
    
    # Initialize v1.5 strategy
    strategy = DefiningOrderStrategyV15(api_key, jwt_token)
    
    # Same symbols as v2.1 test
    symbols = [
        {'symbol': 'RELIANCE-EQ', 'token': '2885'},
        {'symbol': 'TCS-EQ', 'token': '11536'},
        {'symbol': 'HDFCBANK-EQ', 'token': '1333'},
        {'symbol': 'INFY-EQ', 'token': '1594'},
        {'symbol': 'ICICIBANK-EQ', 'token': '4963'},
        {'symbol': 'HINDUNILVR-EQ', 'token': '1394'},
        {'symbol': 'SBIN-EQ', 'token': '3045'},
        {'symbol': 'BHARTIARTL-EQ', 'token': '10604'},
        {'symbol': 'ITC-EQ', 'token': '1660'},
        {'symbol': 'KOTAKBANK-EQ', 'token': '1922'},
        {'symbol': 'LT-EQ', 'token': '11483'},
        {'symbol': 'AXISBANK-EQ', 'token': '5900'},
        {'symbol': 'WIPRO-EQ', 'token': '3787'},
        {'symbol': 'HCLTECH-EQ', 'token': '7229'},
        {'symbol': 'MARUTI-EQ', 'token': '10999'},
    ]
    
    logger.info(f"\n📊 Testing with {len(symbols)} symbols")
    logger.info("📅 Period: December 15, 2024 to December 15, 2025 (1 year)")
    logger.info("💰 Initial Capital: ₹100,000")
    logger.info("")
    logger.info("Key Differences from v2.1:")
    logger.info("  ✓ Simpler filters (less strict)")
    logger.info("  ✓ No 13:00 hour skip")
    logger.info("  ✓ Lower ATR thresholds")
    logger.info("  ✓ More lenient RSI (22-78 vs 55/45)")
    logger.info("  ✓ Allows SuperTrend bypass with strong volume")
    logger.info("")
    
    # Run backtest
    logger.info("🚀 Starting v1.5 backtest... This may take several minutes.\n")
    
    results = strategy.run_backtest(
        symbols=symbols,
        start_date="2024-12-15",
        end_date="2025-12-15",
        initial_capital=100000
    )
    
    # Save results
    if results['total_trades'] > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_v15_1year_{timestamp}.csv"
        results['trades'].to_csv(filename, index=False)
        logger.info(f"\n✅ Results saved to: {filename}")
        
        # Compare with v2.1
        logger.info("\n" + "=" * 100)
        logger.info("COMPARISON: v1.5 vs v2.1")
        logger.info("=" * 100)
        
        import pandas as pd
        trades_v15 = results['trades']
        
        # v1.5 stats
        v15_return = results['total_return_pct']
        v15_trades = results['total_trades']
        v15_winrate = results['win_rate']
        v15_profit_factor = results['profit_factor']
        
        # v2.1 stats (from previous run)
        v21_return = -39.34
        v21_trades = 153
        v21_winrate = 26.80
        v21_profit_factor = 0.54
        
        logger.info("\n📊 HEAD-TO-HEAD COMPARISON:\n")
        logger.info(f"{'Metric':<25} {'v1.5':>15} {'v2.1':>15} {'Winner':>15}")
        logger.info("-" * 70)
        logger.info(f"{'Return %':<25} {v15_return:>14.2f}% {v21_return:>14.2f}% {'v1.5' if v15_return > v21_return else 'v2.1':>15}")
        logger.info(f"{'Total Trades':<25} {v15_trades:>15} {v21_trades:>15} {'v1.5' if v15_trades > v21_trades else 'v2.1':>15}")
        logger.info(f"{'Win Rate %':<25} {v15_winrate:>14.2f}% {v21_winrate:>14.2f}% {'v1.5' if v15_winrate > v21_winrate else 'v2.1':>15}")
        logger.info(f"{'Profit Factor':<25} {v15_profit_factor:>15.2f} {v21_profit_factor:>15.2f} {'v1.5' if v15_profit_factor > v21_profit_factor else 'v2.1':>15}")
        
        # Symbol breakdown
        logger.info("\n📈 v1.5 SYMBOL PERFORMANCE:")
        symbol_stats = trades_v15.groupby('symbol').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(2)
        symbol_stats.columns = ['Trades', 'Total PnL', 'Avg PnL']
        symbol_stats = symbol_stats.sort_values('Total PnL', ascending=False)
        print(symbol_stats)
        
        # Monthly breakdown
        logger.info("\n📅 v1.5 MONTHLY PERFORMANCE:")
        trades_v15['month'] = pd.to_datetime(trades_v15['entry_time']).dt.to_period('M')
        monthly = trades_v15.groupby('month').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(2)
        monthly.columns = ['Trades', 'Total PnL', 'Avg PnL']
        print(monthly)
        
        # Final verdict
        logger.info("\n" + "=" * 100)
        logger.info("FINAL VERDICT")
        logger.info("=" * 100)
        
        if v15_return > 0:
            logger.info("\n✅ v1.5 is PROFITABLE!")
            logger.info(f"   Return: {v15_return:.2f}%")
            logger.info(f"   This is {v15_return - v21_return:.2f}% better than v2.1")
            logger.info("\n💡 RECOMMENDATION: Use v1.5 strategy instead of v2.1")
            logger.info("   - Simpler filters allow more trades")
            logger.info("   - Better win rate and profitability")
            logger.info("   - More suitable for live trading")
        elif v15_return > v21_return:
            logger.info(f"\n⚠️ v1.5 is LESS BAD than v2.1")
            logger.info(f"   v1.5 Loss: {v15_return:.2f}%")
            logger.info(f"   v2.1 Loss: {v21_return:.2f}%")
            logger.info(f"   Improvement: {v15_return - v21_return:.2f}%")
            logger.info("\n💡 RECOMMENDATION: v1.5 is better but STILL NOT VIABLE")
            logger.info("   - Both strategies lose money")
            logger.info("   - Need fundamental strategy redesign")
            logger.info("   - Do NOT trade either version live")
        else:
            logger.info(f"\n❌ v1.5 is WORSE than v2.1!")
            logger.info(f"   v1.5 Loss: {v15_return:.2f}%")
            logger.info(f"   v2.1 Loss: {v21_return:.2f}%")
            logger.info(f"   Deterioration: {v15_return - v21_return:.2f}%")
            logger.info("\n💡 RECOMMENDATION: Strategy is fundamentally flawed")
            logger.info("   - Neither version works")
            logger.info("   - Start fresh with proven strategy")
            logger.info("   - Do NOT trade any version live")
        
    else:
        logger.warning("⚠️ No trades executed during v1.5 backtest period")
        logger.info("\nThis means v1.5 filters are ALSO too strict!")
        logger.info("Strategy needs fundamental redesign.")
    
    logger.info("\n" + "=" * 100)


if __name__ == "__main__":
    test_v15_strategy()
