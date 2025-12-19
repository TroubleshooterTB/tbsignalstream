"""
Comprehensive 12-Batch Backtesting Plan
Systematically test Alpha-Ensemble to find optimal parameters
"""

# 12 BATCHES TO TEST
# Each batch tests a specific aspect of the strategy

BATCHES = {
    "BATCH 1: Baseline Performance": {
        "description": "Current Alpha-Ensemble settings (no changes)",
        "date_range": "2025-11-01 to 2025-12-18",
        "parameters": {
            "strategy": "alpha-ensemble",
            "ema_period": 200,
            "adx_threshold": 20,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "volume_multiplier": 1.5,
            "risk_reward": 2.5
        },
        "goal": "Establish baseline metrics for comparison"
    },
    
    "BATCH 2: EMA Period Sensitivity": {
        "description": "Test different EMA periods (100, 150, 200, 250)",
        "variations": [
            {"ema": 100, "label": "EMA100 - Faster trend"},
            {"ema": 150, "label": "EMA150 - Medium trend"},
            {"ema": 200, "label": "EMA200 - Current"},
            {"ema": 250, "label": "EMA250 - Slower trend"}
        ],
        "goal": "Find optimal trend filter"
    },
    
    "BATCH 3: ADX Threshold Testing": {
        "description": "Test ADX thresholds (15, 20, 25, 30)",
        "variations": [
            {"adx": 15, "label": "ADX>15 - Include weak trends"},
            {"adx": 20, "label": "ADX>20 - Current"},
            {"adx": 25, "label": "ADX>25 - Strong trends only"},
            {"adx": 30, "label": "ADX>30 - Very strong trends"}
        ],
        "goal": "Balance trade frequency vs quality"
    },
    
    "BATCH 4: RSI Range Optimization": {
        "description": "Test RSI overbought/oversold levels",
        "variations": [
            {"rsi_os": 25, "rsi_ob": 75, "label": "25/75 - Tighter range"},
            {"rsi_os": 30, "rsi_ob": 70, "label": "30/70 - Current"},
            {"rsi_os": 35, "rsi_ob": 65, "label": "35/65 - Narrower range"},
            {"rsi_os": 40, "rsi_ob": 60, "label": "40/60 - Very narrow"}
        ],
        "goal": "Avoid overbought/oversold conditions"
    },
    
    "BATCH 5: Volume Filter Strength": {
        "description": "Test volume multipliers (1.2x, 1.5x, 2.0x, 2.5x)",
        "variations": [
            {"vol": 1.2, "label": "1.2x - Lenient"},
            {"vol": 1.5, "label": "1.5x - Current"},
            {"vol": 2.0, "label": "2.0x - Strict"},
            {"vol": 2.5, "label": "2.5x - Very strict"}
        ],
        "goal": "Ensure sufficient liquidity"
    },
    
    "BATCH 6: Risk:Reward Ratio": {
        "description": "Test different R:R ratios (2.0, 2.5, 3.0, 3.5)",
        "variations": [
            {"rr": 2.0, "label": "2:1 R:R"},
            {"rr": 2.5, "label": "2.5:1 R:R - Current"},
            {"rr": 3.0, "label": "3:1 R:R"},
            {"rr": 3.5, "label": "3.5:1 R:R"}
        ],
        "goal": "Maximize profit factor"
    },
    
    "BATCH 7: Time-of-Day Analysis": {
        "description": "Test entry restrictions by hour",
        "variations": [
            {"hours": "9:15-15:30", "label": "All hours"},
            {"hours": "9:15-12:00", "label": "Morning only"},
            {"hours": "12:00-15:30", "label": "Afternoon only"},
            {"hours": "10:00-14:00", "label": "Core hours (avoid extremes)"}
        ],
        "goal": "Avoid low-quality time windows"
    },
    
    "BATCH 8: Nifty Alignment Strength": {
        "description": "Test Nifty trend alignment requirement",
        "variations": [
            {"nifty_req": "none", "label": "No Nifty filter"},
            {"nifty_req": "same", "label": "Same direction - Current"},
            {"nifty_req": "strong_same", "label": "Strong same direction"},
            {"nifty_req": "very_strong", "label": "Very strong alignment"}
        ],
        "goal": "Ride market momentum"
    },
    
    "BATCH 9: Position Sizing": {
        "description": "Test different position sizes (1%, 2%, 3%, 5%)",
        "variations": [
            {"size": 0.01, "label": "1% per trade"},
            {"size": 0.02, "label": "2% per trade - Current"},
            {"size": 0.03, "label": "3% per trade"},
            {"size": 0.05, "label": "5% per trade"}
        ],
        "goal": "Optimize capital allocation"
    },
    
    "BATCH 10: Max Concurrent Positions": {
        "description": "Test different max position limits (2, 3, 5, 7)",
        "variations": [
            {"max_pos": 2, "label": "Max 2 positions"},
            {"max_pos": 3, "label": "Max 3 positions"},
            {"max_pos": 5, "label": "Max 5 positions - Current"},
            {"max_pos": 7, "label": "Max 7 positions"}
        ],
        "goal": "Balance diversification vs capital efficiency"
    },
    
    "BATCH 11: Symbol Universe": {
        "description": "Test different stock universes (Baseline: Nifty 200 - 276 symbols)",
        "variations": [
            {"universe": "NIFTY200", "label": "Nifty 200 (276 symbols) - Current baseline"},
            {"universe": "NIFTY100", "label": "Nifty 100 - More liquid"},
            {"universe": "NIFTY50", "label": "Nifty 50 - Highly liquid"},
            {"universe": "NIFTY20", "label": "Top 20 - Ultra liquid"}
        ],
        "goal": "Find best opportunity set (more symbols = more opportunities, fewer = higher quality)"
    },
    
    "BATCH 12: Multi-Timeframe Confirmation": {
        "description": "Test timeframe alignment requirements",
        "variations": [
            {"tf": "5min_only", "label": "5min only - Fast"},
            {"tf": "5min+15min", "label": "5min+15min - Current"},
            {"tf": "5min+15min+hourly", "label": "5min+15min+hourly - Conservative"},
            {"tf": "all_timeframes", "label": "All timeframes aligned - Very conservative"}
        ],
        "goal": "Reduce false signals"
    }
}

print("=" * 100)
print("📊 12-BATCH COMPREHENSIVE BACKTESTING PLAN")
print("=" * 100)
print()
print("OBJECTIVE: Systematically optimize Alpha-Ensemble strategy parameters")
print("BASELINE: 36% WR, 2.64 PF, 250% returns (1 month)")
print("🎯 AGGRESSIVE TARGET: 65%+ WR, 5.0+ PF (quality over quantity)")
print("   Strategy: Higher conviction setups, stricter filters, fewer but better trades")
print()
print("=" * 100)

for batch_num, (batch_name, batch_data) in enumerate(BATCHES.items(), 1):
    print(f"\n{batch_num}. {batch_name}")
    print("-" * 100)
    print(f"   📝 Description: {batch_data['description']}")
    print(f"   🎯 Goal: {batch_data['goal']}")
    
    if 'variations' in batch_data:
        print(f"   🔬 Variations to test:")
        for var in batch_data['variations']:
            print(f"      • {var['label']}")
    elif 'parameters' in batch_data:
        print(f"   ⚙️  Parameters:")
        for key, value in batch_data['parameters'].items():
            print(f"      • {key}: {value}")
    
    print()

print("=" * 100)
print("📋 EXECUTION PLAN")
print("=" * 100)
print()
print("Each batch will:")
print("  1. Run backtest on same date range (Nov 1 - Dec 18, 2025)")
print("  2. Record: Win Rate, Profit Factor, Total P&L, Avg Win, Avg Loss")
print("  3. Compare against baseline (Batch 1)")
print("  4. Identify best variation in each category")
print()
print("After all 12 batches:")
print("  1. Select best parameter from each batch")
print("  2. Combine into 'optimized configuration'")
print("  3. Run final validation backtest")
print("  4. Deploy if results > baseline")
print()
print("=" * 100)
print("⏱️  ESTIMATED TIME: ~2-3 hours for all 12 batches")
print("📊 TOTAL BACKTESTS: ~40-50 individual runs")
print("=" * 100)
print()
print("Ready to begin? Run backtests through dashboard Strategy Backtester!")
print("Or create automated script to run all batches programmatically.")
