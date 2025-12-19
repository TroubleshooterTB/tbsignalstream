"""
Automated 65%+ Win Rate Optimization
Executes Aggressive Baseline + 12 Batch Tests

This script will:
1. Run Aggressive Baseline (stricter parameters)
2. Run all 12 batches systematically
3. Save results for comparison
4. Identify best parameters for 65%+ WR

Constraint: Must maintain 1+ trade per day (20-25/month)
"""

import json
import subprocess
import time
from datetime import datetime
import pandas as pd

# AGGRESSIVE BASELINE CONFIGURATION
AGGRESSIVE_BASELINE = {
    "name": "Aggressive Baseline",
    "ema_period": 200,
    "adx_threshold": 23,
    "rsi_oversold": 32,
    "rsi_overbought": 68,
    "volume_multiplier": 1.8,
    "risk_reward": 3.0,
    "stop_loss_atr": 1.8,
    "position_size": 2,
    "max_positions": 3,
    "timeframe_alignment": "3TF",  # 5min + 15min + hourly
    "nifty_alignment": "same",
    "trading_hours": "09:45-15:00",
    "universe": "NIFTY100"
}

# 12 BATCHES TO TEST
BATCHES = [
    {
        "batch_num": 1,
        "name": "Current Baseline (for comparison)",
        "variations": [
            {"label": "Current", "params": {"adx_threshold": 20, "rsi_oversold": 30, "rsi_overbought": 70, "volume_multiplier": 1.5}}
        ]
    },
    {
        "batch_num": 2,
        "name": "EMA Period",
        "variations": [
            {"label": "EMA100", "params": {"ema_period": 100}},
            {"label": "EMA150", "params": {"ema_period": 150}},
            {"label": "EMA200", "params": {"ema_period": 200}},
            {"label": "EMA250", "params": {"ema_period": 250}}
        ]
    },
    {
        "batch_num": 3,
        "name": "ADX Threshold",
        "variations": [
            {"label": "ADX20", "params": {"adx_threshold": 20}},
            {"label": "ADX23", "params": {"adx_threshold": 23}},
            {"label": "ADX25", "params": {"adx_threshold": 25}},
            {"label": "ADX27", "params": {"adx_threshold": 27}}
        ]
    },
    {
        "batch_num": 4,
        "name": "RSI Range",
        "variations": [
            {"label": "RSI_30_70", "params": {"rsi_oversold": 30, "rsi_overbought": 70}},
            {"label": "RSI_32_68", "params": {"rsi_oversold": 32, "rsi_overbought": 68}},
            {"label": "RSI_35_65", "params": {"rsi_oversold": 35, "rsi_overbought": 65}},
            {"label": "RSI_38_62", "params": {"rsi_oversold": 38, "rsi_overbought": 62}}
        ]
    },
    {
        "batch_num": 5,
        "name": "Volume Filter",
        "variations": [
            {"label": "Vol_1.5x", "params": {"volume_multiplier": 1.5}},
            {"label": "Vol_1.8x", "params": {"volume_multiplier": 1.8}},
            {"label": "Vol_2.0x", "params": {"volume_multiplier": 2.0}},
            {"label": "Vol_2.5x", "params": {"volume_multiplier": 2.5}}
        ]
    },
    {
        "batch_num": 6,
        "name": "Risk:Reward Ratio",
        "variations": [
            {"label": "RR_2.5", "params": {"risk_reward": 2.5}},
            {"label": "RR_3.0", "params": {"risk_reward": 3.0}},
            {"label": "RR_3.5", "params": {"risk_reward": 3.5}},
            {"label": "RR_4.0", "params": {"risk_reward": 4.0}}
        ]
    },
    {
        "batch_num": 7,
        "name": "Stop Loss Width",
        "variations": [
            {"label": "SL_1.5_ATR", "params": {"stop_loss_atr": 1.5}},
            {"label": "SL_1.8_ATR", "params": {"stop_loss_atr": 1.8}},
            {"label": "SL_2.0_ATR", "params": {"stop_loss_atr": 2.0}},
            {"label": "SL_2.5_ATR", "params": {"stop_loss_atr": 2.5}}
        ]
    },
    {
        "batch_num": 8,
        "name": "Position Sizing",
        "variations": [
            {"label": "Size_1pct", "params": {"position_size": 1}},
            {"label": "Size_2pct", "params": {"position_size": 2}},
            {"label": "Size_3pct", "params": {"position_size": 3}},
            {"label": "Size_5pct", "params": {"position_size": 5}}
        ]
    },
    {
        "batch_num": 9,
        "name": "Max Concurrent Positions",
        "variations": [
            {"label": "Max_2", "params": {"max_positions": 2}},
            {"label": "Max_3", "params": {"max_positions": 3}},
            {"label": "Max_5", "params": {"max_positions": 5}},
            {"label": "Max_7", "params": {"max_positions": 7}}
        ]
    },
    {
        "batch_num": 10,
        "name": "Timeframe Alignment",
        "variations": [
            {"label": "1TF_5min", "params": {"timeframe_alignment": "1TF"}},
            {"label": "2TF_5_15", "params": {"timeframe_alignment": "2TF"}},
            {"label": "3TF_5_15_H", "params": {"timeframe_alignment": "3TF"}},
            {"label": "4TF_All", "params": {"timeframe_alignment": "4TF"}}
        ]
    },
    {
        "batch_num": 11,
        "name": "Symbol Universe",
        "variations": [
            {"label": "NIFTY200", "params": {"universe": "NIFTY200"}},
            {"label": "NIFTY100", "params": {"universe": "NIFTY100"}},
            {"label": "NIFTY50", "params": {"universe": "NIFTY50"}},
            {"label": "NIFTY20", "params": {"universe": "NIFTY20"}}
        ]
    },
    {
        "batch_num": 12,
        "name": "Trading Hours",
        "variations": [
            {"label": "Full_Day", "params": {"trading_hours": "09:45-15:00"}},
            {"label": "Morning", "params": {"trading_hours": "09:45-12:30"}},
            {"label": "Afternoon", "params": {"trading_hours": "13:00-15:00"}},
            {"label": "Core_Hours", "params": {"trading_hours": "10:30-14:30"}}
        ]
    }
]

class BacktestOptimizer:
    def __init__(self):
        self.results = []
        self.best_config = None
        self.best_win_rate = 0
        
    def run_backtest(self, config_name, params):
        """
        Run a single backtest with given parameters
        Note: This is a placeholder - actual backtest execution depends on your setup
        
        Options:
        1. Call dashboard API endpoint
        2. Run Python backtest script directly
        3. Manual execution through dashboard
        """
        print(f"\n{'='*80}")
        print(f"🔬 RUNNING: {config_name}")
        print(f"{'='*80}")
        
        print("\n📊 Parameters:")
        for key, value in params.items():
            print(f"   • {key}: {value}")
        
        print("\n⏳ Backtest execution options:")
        print("   1. Dashboard: Go to Strategy Backtester and use params above")
        print("   2. API: Call /api/backtest with these parameters")
        print("   3. Python: Modify run_backtest_defining_order.py with params")
        
        print("\n⌛ Waiting for results...")
        print("   (In production, this would execute automatically)")
        print("   (For now, run manually and record results)")
        
        # Placeholder for actual execution
        # In real implementation, this would call your backtest API/script
        
        return {
            "config_name": config_name,
            "params": params,
            "timestamp": datetime.now().isoformat()
        }
    
    def display_execution_plan(self):
        """Show the complete execution plan"""
        print("="*80)
        print("🎯 65%+ WIN RATE OPTIMIZATION - EXECUTION PLAN")
        print("="*80)
        print()
        print("GOAL: Achieve 65%+ WR with 1+ trade per day (20-25 trades/month)")
        print("DATE RANGE: Nov 1 - Dec 18, 2025")
        print("SYMBOL UNIVERSE: Nifty 200 (276 symbols)")
        print()
        print("="*80)
        print("📋 TESTING SEQUENCE")
        print("="*80)
        print()
        
        print("STEP 0: Aggressive Baseline")
        print("-" * 80)
        for key, value in AGGRESSIVE_BASELINE.items():
            if key != "name":
                print(f"   • {key}: {value}")
        print()
        
        total_tests = sum(len(batch["variations"]) for batch in BATCHES)
        
        for batch in BATCHES:
            print(f"\nBATCH {batch['batch_num']}: {batch['name']}")
            print("-" * 80)
            for var in batch["variations"]:
                print(f"   ✓ {var['label']}")
        
        print()
        print("="*80)
        print(f"📊 TOTAL TESTS: {total_tests + 1} (1 baseline + {total_tests} variations)")
        print("⏱️  ESTIMATED TIME: 3-4 hours (if automated)")
        print("="*80)
        print()
        
    def save_results_template(self):
        """Create a template CSV for recording results manually"""
        
        all_tests = [{"batch": 0, "test": "Aggressive Baseline", **AGGRESSIVE_BASELINE}]
        
        for batch in BATCHES:
            for var in batch["variations"]:
                test_config = {**AGGRESSIVE_BASELINE, **var["params"]}
                all_tests.append({
                    "batch": batch["batch_num"],
                    "test": f"{batch['name']} - {var['label']}",
                    **test_config
                })
        
        df = pd.DataFrame(all_tests)
        
        # Add result columns
        df["win_rate"] = None
        df["profit_factor"] = None
        df["total_trades"] = None
        df["total_pnl"] = None
        df["avg_win"] = None
        df["avg_loss"] = None
        df["expectancy"] = None
        df["max_drawdown"] = None
        df["trades_per_day"] = None
        df["notes"] = None
        
        filename = f"optimization_results_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\n✅ Results template saved to: {filename}")
        print("   → Fill in results as you run each backtest")
        print("   → This will help track which parameters work best")
        
        return filename

def main():
    print("\n" + "="*80)
    print("🚀 STARTING 65%+ WIN RATE OPTIMIZATION")
    print("="*80)
    print()
    
    optimizer = BacktestOptimizer()
    
    # Display the plan
    optimizer.display_execution_plan()
    
    # Create results template
    template_file = optimizer.save_results_template()
    
    print("\n" + "="*80)
    print("📝 MANUAL EXECUTION INSTRUCTIONS")
    print("="*80)
    print()
    print("Since backtesting requires dashboard/API access, here's the workflow:")
    print()
    print("1. Open the dashboard at:")
    print("   https://studio--tbsignalstream.us-central1.hosted.app")
    print()
    print("2. Go to Strategy Backtester")
    print()
    print("3. For each test:")
    print("   a) Set date range: Nov 1 - Dec 18, 2025")
    print("   b) Use parameters from the template CSV")
    print("   c) Run backtest")
    print("   d) Record results in the CSV")
    print()
    print("4. After all tests:")
    print("   a) Sort by Win Rate descending")
    print("   b) Find tests with 65%+ WR AND 20+ trades")
    print("   c) Select best overall configuration")
    print()
    print(f"5. Results tracking:")
    print(f"   → Fill in: {template_file}")
    print()
    print("="*80)
    print()
    print("💡 TIP: Start with Aggressive Baseline first!")
    print("   If WR < 50%, parameters are too strict - loosen them")
    print("   If WR > 60%, you're on the right track - continue with batches")
    print()
    print("🎯 KEY METRICS TO WATCH:")
    print("   1. Win Rate (must be 65%+)")
    print("   2. Total Trades (must be 20+ for the month)")
    print("   3. Profit Factor (target 5.0+)")
    print("   4. Expectancy (target ₹1,500+)")
    print()
    print("="*80)
    print("✅ OPTIMIZATION PLAN READY!")
    print("="*80)

if __name__ == "__main__":
    main()
