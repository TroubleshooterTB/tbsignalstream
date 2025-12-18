"""
Test Mean Reversion with RELAXED parameters
To see if strategy can generate trades
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from strategy_mean_reversion_v1 import MeanReversionStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_relaxed_parameters():
    """Test with relaxed parameters to see trade potential"""
    
    logging.info("\n" + "="*80)
    logging.info("MEAN REVERSION - RELAXED PARAMETERS TEST")
    logging.info("="*80 + "\n")
    
    # Create simulated ranging day data
    dates = pd.date_range(start='2025-12-18 09:15', end='2025-12-18 15:30', freq='5T')
    np.random.seed(42)
    
    price_base = 1540
    prices = []
    volumes = []
    
    for i in range(len(dates)):
        hour = dates[i].hour
        
        # Create clear mean reversion patterns
        phase = i / len(dates) * 4 * np.pi  # 2 full cycles
        offset = np.sin(phase) * 7  # Oscillate ±7 rupees
        
        # Add some noise
        offset += np.random.uniform(-1, 1)
        
        open_price = price_base + offset
        high_price = open_price + abs(np.random.uniform(0, 2))
        low_price = open_price - abs(np.random.uniform(0, 2))
        close_price = np.random.uniform(low_price, high_price)
        
        # Varied volume
        if hour == 9 or hour == 15:
            volume = np.random.randint(100000, 180000)
        elif 12 <= hour <= 14:
            volume = np.random.randint(30000, 60000)
        else:
            volume = np.random.randint(60000, 100000)
        
        prices.append([open_price, high_price, low_price, close_price])
        volumes.append(volume)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': [p[0] for p in prices],
        'high': [p[1] for p in prices],
        'low': [p[2] for p in prices],
        'close': [p[3] for p in prices],
        'volume': volumes
    })
    
    logging.info(f"📊 Data: {len(df)} candles")
    logging.info(f"📊 Price range: ₹{df['low'].min():.2f} - ₹{df['high'].max():.2f}")
    logging.info(f"📊 Price deviation: ₹{df['high'].max() - df['low'].min():.2f}")
    
    # Test with 3 parameter sets
    test_configs = [
        {
            'name': 'STRICT (Original)',
            'RSI_OVERSOLD': 30,
            'RSI_OVERBOUGHT': 70,
            'VOLUME_MULTIPLIER': 1.5,
            'VWAP_DEVIATION_PERCENT': 0.5,
            'BB_STD': 2.0
        },
        {
            'name': 'MODERATE (Relaxed)',
            'RSI_OVERSOLD': 40,  # Easier to trigger
            'RSI_OVERBOUGHT': 60,  # Easier to trigger
            'VOLUME_MULTIPLIER': 1.2,  # Lower volume requirement
            'VWAP_DEVIATION_PERCENT': 0.3,  # Closer to VWAP
            'BB_STD': 1.5  # Tighter bands
        },
        {
            'name': 'LOOSE (Very Relaxed)',
            'RSI_OVERSOLD': 45,
            'RSI_OVERBOUGHT': 55,
            'VOLUME_MULTIPLIER': 1.0,  # No extra volume needed
            'VWAP_DEVIATION_PERCENT': 0.2,
            'BB_STD': 1.0  # Very tight bands
        }
    ]
    
    results_summary = []
    
    for config in test_configs:
        logging.info(f"\n{'='*80}")
        logging.info(f"Testing: {config['name']}")
        logging.info(f"{'='*80}")
        logging.info(f"Parameters:")
        logging.info(f"  RSI Oversold/Overbought: {config['RSI_OVERSOLD']}/{config['RSI_OVERBOUGHT']}")
        logging.info(f"  Volume Multiplier: {config['VOLUME_MULTIPLIER']}x")
        logging.info(f"  VWAP Deviation: {config['VWAP_DEVIATION_PERCENT']}%")
        logging.info(f"  BB Std Dev: {config['BB_STD']}")
        logging.info("")
        
        # Create strategy with custom params
        strategy = MeanReversionStrategy("dummy", "dummy")
        strategy.RSI_OVERSOLD = config['RSI_OVERSOLD']
        strategy.RSI_OVERBOUGHT = config['RSI_OVERBOUGHT']
        strategy.VOLUME_MULTIPLIER = config['VOLUME_MULTIPLIER']
        strategy.VWAP_DEVIATION_PERCENT = config['VWAP_DEVIATION_PERCENT']
        strategy.BB_STD = config['BB_STD']
        
        # Run backtest
        results = strategy.run_backtest(config['name'], df.copy(), initial_capital=100000)
        
        results_summary.append({
            'config': config['name'],
            'trades': results['total_trades'],
            'win_rate': results['win_rate'] if results['total_trades'] > 0 else 0,
            'pnl': results['total_pnl'] if results['total_trades'] > 0 else 0,
            'return_pct': results['return_pct'] if results['total_trades'] > 0 else 0
        })
    
    # Comparison
    logging.info("\n" + "="*80)
    logging.info("PARAMETER COMPARISON SUMMARY")
    logging.info("="*80)
    logging.info(f"{'Config':<20} {'Trades':<10} {'Win Rate':<12} {'P&L':<15} {'Return':<10}")
    logging.info("-" * 80)
    
    for r in results_summary:
        logging.info(f"{r['config']:<20} {r['trades']:<10} {r['win_rate']:>6.1f}%     ₹{r['pnl']:>10.2f}   {r['return_pct']:>6.2f}%")
    
    logging.info("="*80)
    
    # Recommendation
    best = max(results_summary, key=lambda x: x['pnl'])
    
    if best['trades'] > 0:
        logging.info(f"\n✅ BEST CONFIGURATION: {best['config']}")
        logging.info(f"   - {best['trades']} trades taken")
        logging.info(f"   - {best['win_rate']:.1f}% win rate")
        logging.info(f"   - ₹{best['pnl']:.2f} total P&L")
        logging.info(f"   - {best['return_pct']:.2f}% return")
        
        if best['win_rate'] > 50 and best['pnl'] > 0:
            logging.info("\n💡 RECOMMENDATION:")
            logging.info(f"   Use '{best['config']}' parameters for paper trading tomorrow")
            logging.info("   This configuration shows trade potential with acceptable win rate")
        else:
            logging.info("\n⚠️ WARNING:")
            logging.info("   Even best config doesn't meet targets (>50% win rate, positive P&L)")
            logging.info("   Consider testing other strategies in parallel")
    else:
        logging.info("\n❌ NO CONFIGURATION GENERATED TRADES")
        logging.info("   This suggests:")
        logging.info("   1. Mean reversion may not suit all market conditions")
        logging.info("   2. Need hybrid approach (mean reversion + trend following)")
        logging.info("   3. Test other strategies: VWAP+SuperTrend, Last Hour Momentum")
    
    logging.info("\n" + "="*80)
    logging.info("NEXT STEPS:")
    logging.info("="*80)
    logging.info("1. Paper trade with 'MODERATE' parameters tomorrow")
    logging.info("2. If no trades by 11 AM, switch to 'LOOSE' parameters")
    logging.info("3. Document every signal (taken or rejected)")
    logging.info("4. Test other strategies simultaneously")
    logging.info("5. After 1 week, keep only profitable strategies")
    logging.info("="*80)

if __name__ == "__main__":
    test_relaxed_parameters()
