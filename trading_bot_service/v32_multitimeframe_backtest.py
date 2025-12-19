"""
Multi-Timeframe Backtest for v3.2 Strategy
===========================================

Tests the deployed v3.2 strategy across 6 different time periods:
1. 1 Day (Today - Dec 18, 2025)
2. 1 Week (Dec 11-18, 2025)
3. 1 Month (Nov 18 - Dec 18, 2025)
4. 3 Months (Sep 18 - Dec 18, 2025)
5. 6 Months (Jun 18 - Dec 18, 2025)
6. 1 Year (Dec 18, 2024 - Dec 18, 2025)

Analyzes performance to identify:
- What's working
- What needs improvement
- Optimal time periods
- Pattern consistency
"""

import sys
import os
from datetime import datetime, timedelta
import logging
import pandas as pd
import csv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the backtest runner (contains v3.2 strategy)
import importlib.util

# Load the module dynamically
spec = importlib.util.spec_from_file_location(
    "backtest_module",
    os.path.join(os.path.dirname(__file__), "run_backtest_defining_order.py")
)
backtest_module = importlib.util.module_from_spec(spec)
sys.modules["backtest_module"] = backtest_module
spec.loader.exec_module(backtest_module)

DefiningOrderStrategy = backtest_module.DefiningOrderStrategy
generate_jwt_token_original = backtest_module.generate_jwt_token

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use the generate_jwt_token from the backtest module (handles MPIN properly)
generate_jwt_token = generate_jwt_token_original

def run_multi_timeframe_backtest():
    """Run backtests across all timeframes"""
    
    logger.info("="*100)
    logger.info("MULTI-TIMEFRAME BACKTEST - v3.2 STRATEGY ANALYSIS")
    logger.info("="*100)
    logger.info("")
    
    # Get credentials
    import os
    
    api_key = os.environ.get('ANGELONE_API_KEY', '')
    client_code = os.environ.get('ANGELONE_CLIENT_CODE', '')
    password = os.environ.get('ANGELONE_PASSWORD', '')
    
    # If not in environment, prompt user
    if not api_key:
        logger.info("Please enter your Angel One credentials:")
        api_key = input("API Key: ").strip() or "jgosiGzs"
        client_code = input("Client Code: ").strip() or "AABL713311"
        password = input("Trading Password/MPIN: ").strip() or "Sarvesh@7218"
    
    logger.info("Please enter your current TOTP code (6 digits):")
    totp = input("TOTP: ").strip()
    
    if not totp or len(totp) != 6:
        logger.error("❌ Invalid TOTP. Cannot proceed.")
        return None
    
    # Generate JWT token using the backtest module's function
    logger.info("\n🔐 Authenticating with Angel One API...")
    jwt_token = generate_jwt_token(api_key, client_code, password, totp)
    
    if not jwt_token:
        logger.error("❌ Failed to authenticate. Cannot proceed.")
        return None
    
    logger.info("✅ Authentication successful!")
    
    # Initialize strategy with v3.2 configuration
    strategy = DefiningOrderStrategy(api_key, jwt_token)
    
    logger.info("\n✅ Strategy Configuration:")
    logger.info(f"   RSI Range: {strategy.RSI_SAFE_LOWER}-{strategy.RSI_SAFE_UPPER}")
    logger.info(f"   Breakout Min: {strategy.MIN_BREAKOUT_STRENGTH_PCT}%")
    logger.info(f"   Late Entry Volume: {strategy.LATE_ENTRY_VOLUME_THRESHOLD}x")
    logger.info(f"   Hour Blocks: Noon✓ Lunch✓ 15:00✗")
    logger.info(f"   Symbol Blacklist: {len(strategy.BLACKLISTED_SYMBOLS)} symbols")
    
    # Test symbols (comprehensive Nifty 50 sample)
    symbols = [
        {'symbol': 'RELIANCE-EQ', 'token': '2885'},
        {'symbol': 'HDFCBANK-EQ', 'token': '1333'},
        {'symbol': 'INFY-EQ', 'token': '1594'},
        {'symbol': 'ICICIBANK-EQ', 'token': '4963'},
        {'symbol': 'TCS-EQ', 'token': '11536'},
        {'symbol': 'KOTAKBANK-EQ', 'token': '1922'},
        {'symbol': 'SBIN-EQ', 'token': '3045'},
        {'symbol': 'BHARTIARTL-EQ', 'token': '10604'},
        {'symbol': 'HINDUNILVR-EQ', 'token': '1394'},
        {'symbol': 'ITC-EQ', 'token': '1660'},
        {'symbol': 'LT-EQ', 'token': '11483'},
        {'symbol': 'AXISBANK-EQ', 'token': '5900'},
        {'symbol': 'WIPRO-EQ', 'token': '3787'},
        {'symbol': 'HCLTECH-EQ', 'token': '7229'},
        {'symbol': 'MARUTI-EQ', 'token': '10999'},
    ]
    
    # Define test periods
    today = datetime(2025, 12, 18)
    
    test_periods = [
        {
            'name': '1 DAY',
            'start': today,
            'end': today,
            'description': 'Today only (Dec 18, 2025)'
        },
        {
            'name': '1 WEEK',
            'start': today - timedelta(days=7),
            'end': today,
            'description': 'Last 7 days (Dec 11-18, 2025)'
        },
        {
            'name': '1 MONTH',
            'start': today - timedelta(days=30),
            'end': today,
            'description': 'Last 30 days (Nov 18 - Dec 18, 2025)'
        },
        {
            'name': '3 MONTHS',
            'start': today - timedelta(days=90),
            'end': today,
            'description': 'Last 90 days (Sep 18 - Dec 18, 2025)'
        },
        {
            'name': '6 MONTHS',
            'start': today - timedelta(days=180),
            'end': today,
            'description': 'Last 180 days (Jun 18 - Dec 18, 2025)'
        },
        {
            'name': '1 YEAR',
            'start': today - timedelta(days=365),
            'end': today,
            'description': 'Full year (Dec 18, 2024 - Dec 18, 2025)'
        }
    ]
    
    all_results = []
    
    # Run each timeframe test
    for period in test_periods:
        logger.info("\n" + "="*100)
        logger.info(f"TESTING PERIOD: {period['name']}")
        logger.info(f"Description: {period['description']}")
        logger.info(f"Date Range: {period['start'].strftime('%Y-%m-%d')} to {period['end'].strftime('%Y-%m-%d')}")
        logger.info("="*100)
        
        # Format dates for API
        start_date = period['start'].strftime('%Y-%m-%d')
        end_date = period['end'].strftime('%Y-%m-%d')
        
        # Run backtest
        logger.info(f"\n🚀 Starting {period['name']} backtest...")
        logger.info(f"Testing {len(symbols)} symbols")
        logger.info(f"Initial Capital: ₹100,000\n")
        
        try:
            results = strategy.run_backtest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                initial_capital=100000
            )
            
            # Store results
            result_summary = {
                'period': period['name'],
                'description': period['description'],
                'start_date': start_date,
                'end_date': end_date,
                'total_trades': results.get('total_trades', 0),
                'winning_trades': results.get('winning_trades', 0),
                'losing_trades': results.get('losing_trades', 0),
                'win_rate': results.get('win_rate', 0),
                'total_pnl': results.get('total_pnl', 0),
                'total_return_pct': results.get('total_return_pct', 0),
                'profit_factor': results.get('profit_factor', 0),
                'avg_win': results.get('avg_win', 0),
                'avg_loss': results.get('avg_loss', 0),
                'largest_win': results.get('largest_win', 0),
                'largest_loss': results.get('largest_loss', 0),
                'max_drawdown': results.get('max_drawdown', 0),
                'expectancy': results.get('expectancy', 0)
            }
            
            all_results.append(result_summary)
            
            # Display summary
            logger.info(f"\n{'='*100}")
            logger.info(f"{period['name']} RESULTS SUMMARY")
            logger.info(f"{'='*100}")
            logger.info(f"Total Trades:      {result_summary['total_trades']}")
            logger.info(f"Winning Trades:    {result_summary['winning_trades']}")
            logger.info(f"Losing Trades:     {result_summary['losing_trades']}")
            logger.info(f"Win Rate:          {result_summary['win_rate']:.2f}%")
            logger.info(f"Total P&L:         ₹{result_summary['total_pnl']:,.2f}")
            logger.info(f"Return:            {result_summary['total_return_pct']:.2f}%")
            logger.info(f"Profit Factor:     {result_summary['profit_factor']:.2f}")
            logger.info(f"Avg Win:           ₹{result_summary['avg_win']:,.2f}")
            logger.info(f"Avg Loss:          ₹{result_summary['avg_loss']:,.2f}")
            logger.info(f"Expectancy:        ₹{result_summary['expectancy']:,.2f}")
            logger.info(f"Max Drawdown:      {result_summary['max_drawdown']:.2f}%")
            logger.info(f"{'='*100}\n")
            
        except Exception as e:
            logger.error(f"❌ Error in {period['name']} backtest: {e}")
            logger.exception("Full error:")
            continue
    
    # Generate comprehensive comparison report
    if all_results:
        logger.info("\n" + "="*100)
        logger.info("COMPREHENSIVE MULTI-TIMEFRAME COMPARISON")
        logger.info("="*100 + "\n")
        
        # Create comparison table
        logger.info(f"{'Period':<12} {'Trades':<8} {'Win%':<8} {'Return%':<10} {'P&L':<15} {'PF':<8} {'Expectancy':<12}")
        logger.info("-" * 100)
        
        for r in all_results:
            logger.info(
                f"{r['period']:<12} "
                f"{r['total_trades']:<8} "
                f"{r['win_rate']:>6.1f}%  "
                f"{r['total_return_pct']:>8.2f}%  "
                f"₹{r['total_pnl']:>12,.0f}  "
                f"{r['profit_factor']:>6.2f}  "
                f"₹{r['expectancy']:>10.2f}"
            )
        
        logger.info("="*100)
        
        # Analysis
        logger.info("\n" + "="*100)
        logger.info("KEY FINDINGS & ANALYSIS")
        logger.info("="*100 + "\n")
        
        # 1. Consistency Analysis
        profitable_periods = [r for r in all_results if r['total_pnl'] > 0]
        logger.info(f"📊 PROFITABILITY:")
        logger.info(f"   Profitable Periods: {len(profitable_periods)}/{len(all_results)}")
        
        if profitable_periods:
            logger.info(f"   Best Period: {max(profitable_periods, key=lambda x: x['total_return_pct'])['period']} "
                       f"({max(profitable_periods, key=lambda x: x['total_return_pct'])['total_return_pct']:.2f}%)")
        
        losing_periods = [r for r in all_results if r['total_pnl'] < 0]
        if losing_periods:
            logger.info(f"   Worst Period: {min(losing_periods, key=lambda x: x['total_return_pct'])['period']} "
                       f"({min(losing_periods, key=lambda x: x['total_return_pct'])['total_return_pct']:.2f}%)")
        
        # 2. Win Rate Analysis
        logger.info(f"\n📊 WIN RATE ANALYSIS:")
        avg_win_rate = sum(r['win_rate'] for r in all_results) / len(all_results) if all_results else 0
        logger.info(f"   Average Win Rate: {avg_win_rate:.2f}%")
        logger.info(f"   Best Win Rate: {max(all_results, key=lambda x: x['win_rate'])['period']} "
                   f"({max(all_results, key=lambda x: x['win_rate'])['win_rate']:.2f}%)")
        logger.info(f"   Worst Win Rate: {min(all_results, key=lambda x: x['win_rate'])['period']} "
                   f"({min(all_results, key=lambda x: x['win_rate'])['win_rate']:.2f}%)")
        
        # 3. Trade Frequency
        logger.info(f"\n📊 TRADE FREQUENCY:")
        total_trades = sum(r['total_trades'] for r in all_results)
        logger.info(f"   Total Trades (All Periods): {total_trades}")
        
        for r in all_results:
            if r['period'] == '1 DAY':
                logger.info(f"   Daily Average: {r['total_trades']} trades/day")
            elif r['period'] == '1 WEEK':
                trades_per_day = r['total_trades'] / 7 if r['total_trades'] > 0 else 0
                logger.info(f"   Weekly Average: {trades_per_day:.1f} trades/day")
            elif r['period'] == '1 MONTH':
                trades_per_day = r['total_trades'] / 30 if r['total_trades'] > 0 else 0
                logger.info(f"   Monthly Average: {trades_per_day:.1f} trades/day")
        
        # 4. Pattern Detection
        logger.info(f"\n📊 PATTERN DETECTION:")
        
        # Check if performance degrades over time
        short_term = [r for r in all_results if r['period'] in ['1 DAY', '1 WEEK', '1 MONTH']]
        long_term = [r for r in all_results if r['period'] in ['3 MONTHS', '6 MONTHS', '1 YEAR']]
        
        if short_term and long_term:
            avg_short_return = sum(r['total_return_pct'] for r in short_term) / len(short_term)
            avg_long_return = sum(r['total_return_pct'] for r in long_term) / len(long_term)
            
            logger.info(f"   Short-term Avg Return (1D-1M): {avg_short_return:.2f}%")
            logger.info(f"   Long-term Avg Return (3M-1Y): {avg_long_return:.2f}%")
            
            if avg_short_return > avg_long_return:
                logger.info("   ⚠️ WARNING: Performance degrades over longer timeframes (overfitting concern)")
            else:
                logger.info("   ✅ GOOD: Strategy maintains consistency across timeframes")
        
        # 5. Recommendations
        logger.info(f"\n{'='*100}")
        logger.info("RECOMMENDATIONS")
        logger.info("="*100)
        
        # Check 1-year performance
        one_year = next((r for r in all_results if r['period'] == '1 YEAR'), None)
        
        if one_year:
            if one_year['total_return_pct'] > 10 and one_year['win_rate'] > 50:
                logger.info("✅ STRATEGY VALIDATED:")
                logger.info(f"   - 1-year return: {one_year['total_return_pct']:.2f}% (Target: >10%)")
                logger.info(f"   - 1-year win rate: {one_year['win_rate']:.2f}% (Target: >50%)")
                logger.info("   - RECOMMENDATION: Keep v3.2 strategy, continue paper trading")
            elif one_year['total_return_pct'] > 0:
                logger.info("⚠️ STRATEGY MARGINAL:")
                logger.info(f"   - 1-year return: {one_year['total_return_pct']:.2f}% (Profitable but low)")
                logger.info(f"   - 1-year win rate: {one_year['win_rate']:.2f}%")
                logger.info("   - RECOMMENDATION: Needs improvement, test parameter adjustments")
            else:
                logger.info("❌ STRATEGY FAILING:")
                logger.info(f"   - 1-year return: {one_year['total_return_pct']:.2f}% (NEGATIVE)")
                logger.info(f"   - 1-year win rate: {one_year['win_rate']:.2f}%")
                logger.info("   - RECOMMENDATION: Major overhaul needed or switch strategies")
        
        # Save detailed results to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"v32_multitimeframe_backtest_{timestamp}.csv"
        
        with open(csv_filename, 'w', newline='') as f:
            fieldnames = all_results[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        
        logger.info(f"\n✅ Detailed results saved to: {csv_filename}")
        logger.info("="*100)

if __name__ == "__main__":
    run_multi_timeframe_backtest()
