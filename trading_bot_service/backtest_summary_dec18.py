"""
Backtest Results Summary - December 18, 2025
Alpha-Ensemble Strategy (The Defining Order v3.2)
"""

import pandas as pd
import os

print("=" * 100)
print("📊 BACKTEST RESULTS SUMMARY - DECEMBER 18, 2025")
print("=" * 100)
print()

# Load the summary results
summary_file = "v32_multitimeframe_backtest_20251218_222158.csv"
if os.path.exists(summary_file):
    df_summary = pd.read_csv(summary_file)
    
    print("🎯 ALPHA-ENSEMBLE STRATEGY PERFORMANCE")
    print("=" * 100)
    print()
    
    for idx, row in df_summary.iterrows():
        print(f"📅 {row['description']}")
        print("-" * 100)
        print(f"   Period: {row['start_date']} to {row['end_date']}")
        print(f"   Total Trades: {int(row['total_trades'])}")
        print(f"   Winning Trades: {int(row['winning_trades'])} | Losing Trades: {int(row['losing_trades'])}")
        print(f"   Win Rate: {row['win_rate']:.2f}%")
        print(f"   Profit Factor: {row['profit_factor']:.2f}")
        print(f"   Average Win: ₹{row['avg_win']:.2f}")
        print(f"   Average Loss: ₹{row['avg_loss']:.2f}")
        print(f"   Largest Win: ₹{row['largest_win']:.2f}")
        print(f"   Largest Loss: ₹{row['largest_loss']:.2f}")
        print(f"   Expectancy: ₹{row['expectancy']:.2f} per trade")
        print()

# Load detailed trades
detailed_file = "backtest_1year_comprehensive_20251218_195603.csv"
if os.path.exists(detailed_file):
    df_trades = pd.read_csv(detailed_file)
    
    print("\n📈 DETAILED TRADE ANALYSIS")
    print("=" * 100)
    print(f"Total Detailed Trades: {len(df_trades)}")
    print()
    
    # Analyze by direction
    if 'direction' in df_trades.columns:
        print("📊 BY DIRECTION:")
        print("-" * 100)
        for direction in df_trades['direction'].unique():
            dir_trades = df_trades[df_trades['direction'] == direction]
            wins = len(dir_trades[dir_trades['pnl'] > 0]) if 'pnl' in dir_trades.columns else 0
            total = len(dir_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            print(f"   {direction}: {total} trades, {wins} wins ({win_rate:.1f}% WR)")
    
    # Analyze by symbol
    if 'symbol' in df_trades.columns:
        print("\n📊 TOP 10 TRADED SYMBOLS:")
        print("-" * 100)
        symbol_counts = df_trades['symbol'].value_counts().head(10)
        for symbol, count in symbol_counts.items():
            symbol_trades = df_trades[df_trades['symbol'] == symbol]
            wins = len(symbol_trades[symbol_trades['pnl'] > 0]) if 'pnl' in symbol_trades.columns else 0
            win_rate = (wins / count * 100) if count > 0 else 0
            print(f"   {symbol}: {count} trades ({win_rate:.1f}% WR)")

print("\n" + "=" * 100)
print("💡 KEY INSIGHTS FROM BACKTESTING")
print("=" * 100)
print()
print("1️⃣ CONSISTENCY ANALYSIS:")
print("   • 1 Week:  33.33% WR, 0.69 PF - Recent performance")
print("   • 1 Month: 30.19% WR, 0.70 PF - Short-term trend")
print("   • 3 Months: 24.08% WR, 0.49 PF - ⚠️ Deteriorating")
print("   • 1 Year:  26.47% WR, 0.51 PF - Overall trend")
print()
print("2️⃣ PROFIT FACTOR TREND:")
print("   📈 Improving recently (last week better than long-term)")
print("   ⚠️  But still below breakeven (need PF > 1.0)")
print()
print("3️⃣ EXPECTANCY:")
print("   • 1 Week:  -₹1,031 per trade")
print("   • 1 Month: -₹708 per trade")  
print("   • Long-term: -₹473 to -₹510 per trade")
print("   🚨 NEGATIVE EXPECTANCY - Strategy needs optimization!")
print()
print("=" * 100)
print("🔧 RECOMMENDED NEXT STEPS")
print("=" * 100)
print()
print("1. RUN 12-BATCH OPTIMIZATION")
print("   → Test different parameters systematically")
print("   → Find what improves Win Rate and Profit Factor")
print()
print("2. FOCUS AREAS FOR BATCH TESTING:")
print("   ✅ Time-of-day restrictions (avoid low-quality hours)")
print("   ✅ Tighter entry filters (improve signal quality)")
print("   ✅ Risk:Reward optimization (target 3:1 or higher)")
print("   ✅ ADX threshold (only strongest trends)")
print()
print("3. TARGET METRICS:")
print("   • Win Rate: 35-40% (vs current 26-33%)")
print("   • Profit Factor: 2.0+ (vs current 0.5-0.7)")
print("   • Expectancy: +₹500 to +₹1000 per trade")
print()
print("=" * 100)
print("📁 BACKTEST FILES SAVED:")
print("=" * 100)
print(f"   • {summary_file}")
print(f"   • {detailed_file}")
print(f"   • backtest_v15_1year_20251218_202202.csv")
print(f"   • v32_multitimeframe_backtest_20251218_220553.csv")
print("=" * 100)
