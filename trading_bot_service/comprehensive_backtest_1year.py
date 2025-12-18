"""
Comprehensive 1-Year Backtest Runner
December 15, 2024 to December 15, 2025
Automated - No user input required
"""

import sys
import os
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the strategy
# Note: Import from the actual filename (dots in version number)
import importlib.util
import sys

# Load the module dynamically due to dots in filename
spec = importlib.util.spec_from_file_location(
    "strategy_module",
    os.path.join(os.path.dirname(__file__), "run_backtest_defining_order_v2.1_51PCT.py")
)
strategy_module = importlib.util.module_from_spec(spec)
sys.modules["strategy_module"] = strategy_module
spec.loader.exec_module(strategy_module)

DefiningOrderStrategy = strategy_module.DefiningOrderStrategy
generate_jwt_token = strategy_module.generate_jwt_token

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_comprehensive_backtest():
    """Run 1-year backtest with automated credentials"""
    
    logger.info("=" * 100)
    logger.info("COMPREHENSIVE 1-YEAR BACKTEST: December 15, 2024 to December 15, 2025")
    logger.info("=" * 100)
    logger.info("")
    
    # Get credentials from environment or prompt
    api_key = os.environ.get('ANGELONE_API_KEY', '')
    client_code = os.environ.get('ANGELONE_CLIENT_CODE', '')
    password = os.environ.get('ANGELONE_PASSWORD', '')
    totp = os.environ.get('ANGELONE_TOTP', '')
    
    # If not in environment, prompt user
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
    
    # ALL Nifty 50 symbols for comprehensive testing
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
    
    # Run backtest
    logger.info("🚀 Starting backtest... This may take several minutes.\n")
    
    results = strategy.run_backtest(
        symbols=symbols,
        start_date="2024-12-15",
        end_date="2025-12-15",
        initial_capital=100000
    )
    
    # Save detailed results
    if results['total_trades'] > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_1year_comprehensive_{timestamp}.csv"
        results['trades'].to_csv(filename, index=False)
        logger.info(f"\n✅ Detailed results saved to: {filename}")
        
        # Additional analysis
        logger.info("\n" + "=" * 100)
        logger.info("DETAILED ANALYSIS")
        logger.info("=" * 100)
        
        trades_df = results['trades']
        
        # Monthly breakdown
        logger.info("\n📅 MONTHLY PERFORMANCE:")
        trades_df['Month'] = trades_df['Entry Time'].apply(lambda x: x.strftime('%Y-%m'))
        monthly = trades_df.groupby('Month').agg({
            'PnL': ['count', 'sum', 'mean'],
            'Win': 'sum'
        }).round(2)
        monthly.columns = ['Trades', 'Total PnL', 'Avg PnL', 'Wins']
        monthly['Win Rate %'] = (monthly['Wins'] / monthly['Trades'] * 100).round(1)
        print(monthly)
        
        # Symbol breakdown
        logger.info("\n📊 SYMBOL PERFORMANCE:")
        symbol_stats = trades_df.groupby('Symbol').agg({
            'PnL': ['count', 'sum', 'mean'],
            'Win': 'sum'
        }).round(2)
        symbol_stats.columns = ['Trades', 'Total PnL', 'Avg PnL', 'Wins']
        symbol_stats['Win Rate %'] = (symbol_stats['Wins'] / symbol_stats['Trades'] * 100).round(1)
        symbol_stats = symbol_stats.sort_values('Total PnL', ascending=False)
        print(symbol_stats)
        
        # Time of day analysis
        logger.info("\n🕐 HOURLY PERFORMANCE:")
        trades_df['Hour'] = trades_df['Entry Time'].apply(lambda x: x.hour)
        hourly = trades_df.groupby('Hour').agg({
            'PnL': ['count', 'sum', 'mean'],
            'Win': 'sum'
        }).round(2)
        hourly.columns = ['Trades', 'Total PnL', 'Avg PnL', 'Wins']
        hourly['Win Rate %'] = (hourly['Wins'] / hourly['Trades'] * 100).round(1)
        print(hourly)
        
        # Win/Loss analysis
        logger.info("\n💰 WIN/LOSS BREAKDOWN:")
        winning_trades = trades_df[trades_df['Win'] == 1]
        losing_trades = trades_df[trades_df['Win'] == 0]
        
        logger.info(f"Winning Trades: {len(winning_trades)}")
        logger.info(f"  Average Win: ₹{winning_trades['PnL'].mean():.2f}")
        logger.info(f"  Largest Win: ₹{winning_trades['PnL'].max():.2f}")
        logger.info(f"  Total Wins: ₹{winning_trades['PnL'].sum():.2f}")
        
        logger.info(f"\nLosing Trades: {len(losing_trades)}")
        logger.info(f"  Average Loss: ₹{losing_trades['PnL'].mean():.2f}")
        logger.info(f"  Largest Loss: ₹{losing_trades['PnL'].min():.2f}")
        logger.info(f"  Total Losses: ₹{losing_trades['PnL'].sum():.2f}")
        
        # Drawdown analysis
        logger.info("\n📉 DRAWDOWN ANALYSIS:")
        trades_df['Cumulative'] = trades_df['PnL'].cumsum()
        trades_df['Peak'] = trades_df['Cumulative'].cummax()
        trades_df['Drawdown'] = trades_df['Cumulative'] - trades_df['Peak']
        max_drawdown = trades_df['Drawdown'].min()
        logger.info(f"Maximum Drawdown: ₹{max_drawdown:.2f}")
        
        # Consecutive wins/losses
        logger.info("\n🎯 STREAK ANALYSIS:")
        streaks = []
        current_streak = 0
        for win in trades_df['Win']:
            if win == 1:
                current_streak = current_streak + 1 if current_streak > 0 else 1
            else:
                current_streak = current_streak - 1 if current_streak < 0 else -1
            streaks.append(current_streak)
        
        max_win_streak = max([s for s in streaks if s > 0], default=0)
        max_loss_streak = abs(min([s for s in streaks if s < 0], default=0))
        logger.info(f"Longest Winning Streak: {max_win_streak} trades")
        logger.info(f"Longest Losing Streak: {max_loss_streak} trades")
        
        logger.info("\n" + "=" * 100)
        logger.info("✅ COMPREHENSIVE BACKTEST COMPLETE")
        logger.info("=" * 100)
        
    else:
        logger.warning("⚠️ No trades executed during the backtest period")


if __name__ == "__main__":
    run_comprehensive_backtest()
