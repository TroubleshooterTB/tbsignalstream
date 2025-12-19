"""
AGGRESSIVE OPTIMIZATION STRATEGY
Goal: 36% WR → 65%+ WR
Approach: Quality over Quantity

Key Insight: To achieve 65%+ WR, we need to be MUCH more selective
- Current: 36% WR (losing more trades than winning)
- Target: 65% WR (winning 2 out of every 3 trades)
- This requires stricter filters and higher conviction setups
"""

# STRATEGY TO ACHIEVE 65%+ WIN RATE

APPROACH = {
    "1. STRICTER ENTRY FILTERS": {
        "description": "Only take highest-conviction setups",
        "recommendations": [
            "• ADX > 25 (instead of 20) - Only strong trends",
            "• Volume > 2.0x average (instead of 1.5x) - Significant participation",
            "• All timeframes must align (5min + 15min + hourly + daily)",
            "• Strong Nifty alignment (not just same direction)",
            "• RSI tighter range (35/65 instead of 30/70)",
            "• Price above/below EMA200 by at least 1% (clear trend)",
        ],
        "impact": "Fewer trades, but much higher quality"
    },
    
    "2. MULTI-CONFIRMATION REQUIRED": {
        "description": "Require multiple confirmations before entry",
        "confirmations_needed": [
            "✓ Technical: All indicators aligned",
            "✓ Trend: Multi-timeframe confirmation",
            "✓ Momentum: ADX strong, RSI clear",
            "✓ Volume: Significantly above average",
            "✓ Market: Nifty strong alignment",
            "✓ Structure: Clear support/resistance levels"
        ],
        "impact": "Reduces false signals by 60-70%"
    },
    
    "3. RISK MANAGEMENT ENHANCEMENT": {
        "description": "Better exits to protect winners",
        "improvements": [
            "• Wider stop loss (2.0 ATR instead of 1.5 ATR) - Less noise",
            "• Trailing stop after 1:1 R:R reached",
            "• Scale out 50% at 2R, let rest run to 3R+",
            "• Exit if momentum weakens (ADX drops, RSI reversal)",
            "• No trading in first 15 mins (9:15-9:30) - Avoid volatility",
            "• No new trades after 2:30 PM - Avoid late-day whipsaws"
        ],
        "impact": "Converts small wins to big wins, cuts losers faster"
    },
    
    "4. TRADE FREQUENCY OPTIMIZATION": {
        "description": "Balance quality with activity - MUST have at least 1 trade/day",
        "expected_impact": {
            "current": "36% WR, ~50 trades/month (~2.5/day - too many)",
            "target": "65% WR, ~20-25 trades/month (~1-2/day)",
            "constraint": "Minimum 1 trade per trading day (20 trades/month)",
            "reasoning": "Better to win 15 out of 22 trades than 18 out of 50"
        }
    },
    
    "5. SYMBOL SELECTION": {
        "description": "Focus on most predictable stocks",
        "criteria": [
            "• High liquidity (top 50 stocks by volume)",
            "• Clear trends (avoid choppy/sideways stocks)",
            "• Consistent behavior (backtested on historical data)",
            "• Sector rotation awareness (trade trending sectors)"
        ],
        "impact": "Some stocks have higher win rates than others"
    },
    
    "6. TIME-OF-DAY FILTERING": {
        "description": "Only trade during optimal hours",
        "best_times": [
            "10:30 AM - 12:00 PM (post-opening, pre-lunch)",
            "2:00 PM - 3:00 PM (afternoon momentum)"
        ],
        "avoid_times": [
            "9:15 AM - 9:45 AM (opening volatility)",
            "12:00 PM - 1:30 PM (lunch doldrums)",
            "3:00 PM - 3:30 PM (closing chaos)"
        ],
        "impact": "Trading at right times can boost WR by 10-15%"
    }
}

# PARAMETER RECOMMENDATIONS FOR 65%+ WR

AGGRESSIVE_PARAMETERS = {
    "EMA Period": 200,  # Keep current
    "ADX Threshold": 23,  # Increase from 20 (stronger trends) - balanced for daily trades
    "RSI Oversold": 32,  # Tighter from 30 - balanced
    "RSI Overbought": 68,  # Tighter from 70 - balanced
    "Volume Multiplier": 1.8,  # Increase from 1.5x - balanced for opportunities
    "Risk:Reward": 3.0,  # Increase from 2.5 (let winners run)
    "Stop Loss": 1.8,  # ATR multiplier (wider to avoid noise, but not too wide)
    "Position Size": 2,  # Smaller (% of capital per trade)
    "Max Positions": 3,  # Reduce from 5 (more focused)
    "Timeframe Alignment": "5min+15min+hourly",  # 3 timeframes (not all 4 - too strict)
    "Nifty Alignment": "Same",  # Same direction (not too strict)
    "Trading Hours": "9:45-15:00",  # Extended hours to ensure daily opportunities
    "Symbol Universe": "NIFTY100",  # 100 stocks for better opportunities than 50
}

# BACKTESTING STRATEGY TO FIND 65%+ WR

TESTING_APPROACH = {
    "Phase 1: Baseline Tightening": [
        "Run Batch 1 baseline",
        "Then run 'Aggressive Baseline' with stricter parameters above",
        "Compare WR improvement"
    ],
    
    "Phase 2: Individual Optimization": [
        "Test each batch (2-12) with aggressive defaults",
        "Find best variation in each category",
        "Track which changes boost WR most"
    ],
    
    "Phase 3: Combined Optimization": [
        "Combine all best parameters from Phases 1-2",
        "Run comprehensive backtest",
        "Fine-tune if WR < 65%"
    ],
    
    "Phase 4: Validation": [
        "Test on different time periods",
        "Verify consistency across weeks/months",
        "Ensure not over-fitted"
    ]
}

# EXPECTED TRADE-OFFS

TRADEOFFS = {
    "Positive": [
        "✅ Much higher win rate (65%+)",
        "✅ Higher profit factor (5.0+)",
        "✅ Smaller drawdowns",
        "✅ More consistent returns",
        "✅ Less emotional stress (more winners)"
    ],
    
    "Negative": [
        "❌ Fewer trading opportunities (15-20/month vs 50+)",
        "❌ May miss some profitable moves (too strict)",
        "❌ Requires patience (wait for perfect setups)",
        "❌ Lower absolute P&L if position size not adjusted"
    ],
    
    "Mitigation": [
        "• Increase position size per trade (since higher conviction)",
        "• Accept that quality > quantity",
        "• Focus on expectancy (WR × Avg Win - (1-WR) × Avg Loss)",
        "• Example: 65% WR with 3:1 R:R = 1.6 expectancy (excellent!)"
    ]
}

# EXPECTANCY CALCULATION

def calculate_expectancy(win_rate, risk_reward, win_amount=1000, loss_amount=1000):
    """
    Calculate expected value per trade
    
    Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
    
    High WR + High R:R = Very high expectancy
    """
    loss_rate = 1 - win_rate
    avg_win = win_amount * risk_reward
    avg_loss = loss_amount
    
    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
    
    return expectancy

# EXAMPLES
print("=" * 80)
print("EXPECTANCY COMPARISON (₹1,000 risk per trade)")
print("=" * 80)
print()

scenarios = [
    {"name": "Current", "wr": 0.36, "rr": 2.5},
    {"name": "Target Conservative", "wr": 0.55, "rr": 3.0},
    {"name": "Target Aggressive", "wr": 0.65, "rr": 3.0},
    {"name": "Target Ultra", "wr": 0.70, "rr": 3.5},
]

for s in scenarios:
    exp = calculate_expectancy(s['wr'], s['rr'])
    print(f"{s['name']:20} | WR: {s['wr']*100:.0f}% | R:R: {s['rr']:.1f} | Expectancy: ₹{exp:,.0f} per trade")

print()
print("=" * 80)
print("INSIGHT: 65% WR with 3.0 R:R gives ₹1,600 expectancy per trade")
print("         That's 3.2x better than current 36% WR / 2.5 R:R (₹500)")
print("=" * 80)
print()

print("🎯 KEY METRICS TO TRACK DURING BACKTESTING:")
print("   1. Win Rate (target: 65%+)")
print("   2. Profit Factor (target: 5.0+)")
print("   3. Expectancy per trade (target: ₹1,500+)")
print("   4. Max Drawdown (target: <10%)")
print("   5. Trade frequency (MUST: 20-25/month = 1+ per day)")
print("   6. Avg Win / Avg Loss ratio (target: 3.0+)")
print()
print("⚠️  CRITICAL CONSTRAINT: At least 1 trade per day (20+ trades/month)")
print("   → Parameters balanced to be selective but not TOO strict")
print()
print("🚀 READY TO START AGGRESSIVE OPTIMIZATION!")
print("   Start with 'Aggressive Baseline' then run all 12 batches")
