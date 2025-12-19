"""
Aggressive Baseline Backtest
Goal: 65%+ WR with at least 1 trade per day (20-25 trades/month)

Balanced Parameters:
- Strict enough to filter out low-quality setups
- Loose enough to ensure daily trading opportunities
"""

# Test configuration for dashboard backtesting
AGGRESSIVE_BASELINE_CONFIG = {
    "name": "Aggressive Baseline - 65% WR Target",
    "strategy": "alpha-ensemble",
    "date_range": "2025-11-01 to 2025-12-18",
    
    # SCREENING PARAMETERS (balanced for daily opportunities)
    "ema_period": 200,
    "adx_threshold": 23,  # Stricter than 20, but not too strict
    "rsi_oversold": 32,   # Tighter than 30
    "rsi_overbought": 68, # Tighter than 70
    "volume_multiplier": 1.8,  # Higher than 1.5x
    
    # RISK MANAGEMENT
    "risk_reward_ratio": 3.0,  # Higher targets
    "stop_loss_atr": 1.8,      # Wider stops
    "position_size_pct": 2,    # Conservative sizing
    "max_positions": 3,        # Focused portfolio
    
    # TIMEFRAME CONFIRMATION
    "timeframes": ["5min", "15min", "hourly"],  # 3 timeframes must align
    
    # MARKET ALIGNMENT
    "nifty_alignment": "same",  # Same direction (not too strict)
    
    # TRADING HOURS (extended to ensure opportunities)
    "start_time": "09:45",  # After opening volatility
    "end_time": "15:00",    # Full day except last 30 mins
    
    # SYMBOL UNIVERSE
    "universe": "NIFTY100",  # 100 stocks - balance between quality and quantity
    
    # EXPECTED RESULTS
    "expected_trades": "20-25 per month (1+ per day)",
    "target_win_rate": "65%+",
    "target_profit_factor": "5.0+",
    "target_expectancy": "₹1,500+ per trade"
}

print("=" * 80)
print("🎯 AGGRESSIVE BASELINE CONFIGURATION")
print("=" * 80)
print()
print(f"Strategy: {AGGRESSIVE_BASELINE_CONFIG['strategy']}")
print(f"Period: {AGGRESSIVE_BASELINE_CONFIG['date_range']}")
print()
print("📊 SCREENING FILTERS:")
print(f"   • EMA Period: {AGGRESSIVE_BASELINE_CONFIG['ema_period']}")
print(f"   • ADX Threshold: {AGGRESSIVE_BASELINE_CONFIG['adx_threshold']} (stricter than 20)")
print(f"   • RSI Range: {AGGRESSIVE_BASELINE_CONFIG['rsi_oversold']}/{AGGRESSIVE_BASELINE_CONFIG['rsi_overbought']} (tighter than 30/70)")
print(f"   • Volume: {AGGRESSIVE_BASELINE_CONFIG['volume_multiplier']}x average (stricter than 1.5x)")
print()
print("💰 RISK MANAGEMENT:")
print(f"   • Risk:Reward: {AGGRESSIVE_BASELINE_CONFIG['risk_reward_ratio']}:1 (higher than 2.5)")
print(f"   • Stop Loss: {AGGRESSIVE_BASELINE_CONFIG['stop_loss_atr']} ATR (wider than 1.5)")
print(f"   • Position Size: {AGGRESSIVE_BASELINE_CONFIG['position_size_pct']}% per trade")
print(f"   • Max Positions: {AGGRESSIVE_BASELINE_CONFIG['max_positions']} concurrent")
print()
print("⏰ TIMING:")
print(f"   • Trading Hours: {AGGRESSIVE_BASELINE_CONFIG['start_time']} - {AGGRESSIVE_BASELINE_CONFIG['end_time']}")
print(f"   • Timeframe Alignment: {', '.join(AGGRESSIVE_BASELINE_CONFIG['timeframes'])}")
print(f"   • Nifty Alignment: {AGGRESSIVE_BASELINE_CONFIG['nifty_alignment']} direction")
print()
print("📈 UNIVERSE:")
print(f"   • Symbols: {AGGRESSIVE_BASELINE_CONFIG['universe']} (100 stocks)")
print()
print("=" * 80)
print("🎯 TARGETS:")
print("=" * 80)
print(f"   ✓ Win Rate: {AGGRESSIVE_BASELINE_CONFIG['target_win_rate']}")
print(f"   ✓ Profit Factor: {AGGRESSIVE_BASELINE_CONFIG['target_profit_factor']}")
print(f"   ✓ Expectancy: {AGGRESSIVE_BASELINE_CONFIG['target_expectancy']}")
print(f"   ✓ Trade Frequency: {AGGRESSIVE_BASELINE_CONFIG['expected_trades']}")
print()
print("=" * 80)
print()
print("💡 HOW TO RUN:")
print("   1. Go to Dashboard → Strategy Backtester")
print("   2. Select date range: Nov 1 - Dec 18, 2025")
print("   3. Use parameters above as baseline")
print("   4. Compare results against current 36% WR baseline")
print()
print("📊 COMPARISON:")
print("   Current: 36% WR, 2.64 PF, ~50 trades/month")
print("   Target:  65% WR, 5.0+ PF, ~22 trades/month")
print("   Impact:  6x better expectancy, fewer but better trades")
print()
print("🚀 If baseline achieves 50%+ WR, continue with 12-batch optimization!")
print("   If below 50%, adjust parameters to be less strict")
print()
