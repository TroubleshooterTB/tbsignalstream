"""
Analyze v1.7 Losing Trades to Find Patterns
============================================
Examines the 72 losers from expanded backtest to identify common patterns
and propose v1.8 improvements.
"""

import pandas as pd
import numpy as np

# Load the backtest results
df = pd.read_csv('backtest_defining_order_20251214_032045.csv')

# Rename columns for easier access
df.columns = ['Symbol', 'Entry Time', 'Exit Time', 'Direction', 'Entry Price', 'Exit Price', 'Quantity', 'P&L', 'Exit Reason']

# Filter losing trades
losers = df[df['P&L'] < 0].copy()
winners = df[df['P&L'] > 0].copy()

print("=" * 80)
print("v1.7 LOSING TRADES ANALYSIS")
print("=" * 80)
print(f"\nTotal Trades: {len(df)}")
print(f"Winners: {len(winners)} ({len(winners)/len(df)*100:.1f}%)")
print(f"Losers: {len(losers)} ({len(losers)/len(df)*100:.1f}%)")
print(f"\nAverage Win: ₹{winners['P&L'].mean():.2f}")
print(f"Average Loss: ₹{losers['P&L'].mean():.2f}")

print("\n" + "=" * 80)
print("PATTERN ANALYSIS: What Makes Trades Lose?")
print("=" * 80)

# Pattern 1: Entry Time Distribution
print("\n1. ENTRY TIME DISTRIBUTION:")
print("-" * 40)
losers['Entry_Hour'] = pd.to_datetime(losers['Entry Time']).dt.hour
winners['Entry_Hour'] = pd.to_datetime(winners['Entry Time']).dt.hour

print("\nLosers by Hour:")
loser_time = losers.groupby('Entry_Hour').size()
print(loser_time)

print("\nWinners by Hour:")
winner_time = winners.groupby('Entry_Hour').size()
print(winner_time)

print("\nLate Entry Performance (14:30+):")
late_losers = losers[losers['Entry_Hour'] >= 14]
late_winners = winners[winners['Entry_Hour'] >= 14]
print(f"Late Losers: {len(late_losers)} ({len(late_losers)/len(losers)*100:.1f}% of all losers)")
print(f"Late Winners: {len(late_winners)} ({len(late_winners)/len(winners)*100:.1f}% of all winners)")

# Pattern 2: Symbol Performance
print("\n2. SYMBOL PERFORMANCE:")
print("-" * 40)
symbol_stats = df.groupby('Symbol').agg({
    'P&L': ['count', 'sum', 'mean'],
}).round(2)
symbol_stats.columns = ['Trades', 'Total P&L', 'Avg P&L']
symbol_stats['Win Rate %'] = (df[df['P&L'] > 0].groupby('Symbol').size() / df.groupby('Symbol').size() * 100).round(1)
symbol_stats = symbol_stats.sort_values('Win Rate %', ascending=False)
print(symbol_stats)

print("\nWorst Performing Symbols (by Win Rate):")
worst_symbols = symbol_stats.nsmallest(3, 'Win Rate %')
print(worst_symbols)

# Pattern 3: Direction Performance
print("\n3. DIRECTION PERFORMANCE:")
print("-" * 40)
direction_stats = df.groupby('Direction').agg({
    'P&L': ['count', 'sum', 'mean'],
}).round(2)
direction_stats.columns = ['Trades', 'Total P&L', 'Avg P&L']
direction_stats['Win Rate %'] = (df[df['P&L'] > 0].groupby('Direction').size() / df.groupby('Direction').size() * 100).round(1)
print(direction_stats)

# Pattern 4: Signal Type Distribution
print("\n4. SIGNAL TYPE ANALYSIS:")
print("-" * 40)
if 'Signal Type' in df.columns or 'Confirmation' in df.columns:
    # Try to extract signal type from entry notes if available
    print("Signal type data not directly available in CSV")
else:
    print("Signal type data not available - would need to extract from logs")

# Pattern 5: Stop Loss Hit Ratio
print("\n5. STOP LOSS ANALYSIS:")
print("-" * 40)
print(f"Total Losers: {len(losers)}")
print(f"Average Loss Size: ₹{losers['P&L'].mean():.2f}")
print(f"Median Loss Size: ₹{losers['P&L'].median():.2f}")
print(f"Max Loss: ₹{losers['P&L'].min():.2f}")

# Calculate approximate SL hit rate (losses close to -₹1,100 suggest SL hits)
likely_sl_hits = losers[losers['P&L'] <= -1000]
print(f"\nLikely SL Hits (loss >= ₹1,000): {len(likely_sl_hits)} ({len(likely_sl_hits)/len(losers)*100:.1f}%)")

# Pattern 6: Entry Price vs SL Distance Analysis
print("\n6. RISK/REWARD ANALYSIS:")
print("-" * 40)
print("Calculating SL distance from Entry prices...")

# Extract SL distance as percentage
losers['SL_Distance_%'] = abs((losers['Entry Price'] - losers['Stop Loss']) / losers['Entry Price'] * 100)
winners['SL_Distance_%'] = abs((winners['Entry Price'] - winners['Stop Loss']) / winners['Entry Price'] * 100)

print(f"\nAverage SL Distance (Losers): {losers['SL_Distance_%'].mean():.3f}%")
print(f"Average SL Distance (Winners): {winners['SL_Distance_%'].mean():.3f}%")

print(f"\nMin SL Distance (Losers): {losers['SL_Distance_%'].min():.3f}%")
print(f"Min SL Distance (Winners): {winners['SL_Distance_%'].min():.3f}%")

# Pattern 7: Day-wise Performance
print("\n7. DAILY PERFORMANCE:")
print("-" * 40)
df['Trade_Date'] = pd.to_datetime(df['Entry Time']).dt.date
daily_stats = df.groupby('Trade_Date').agg({
    'P&L': ['count', 'sum', 'mean'],
}).round(2)
daily_stats.columns = ['Trades', 'Total P&L', 'Avg P&L']
daily_stats['Win Rate %'] = (df[df['P&L'] > 0].groupby(df['Trade_Date']).size() / df.groupby('Trade_Date').size() * 100).round(1)
print(daily_stats.sort_values('Win Rate %'))

print("\n" + "=" * 80)
print("RECOMMENDATIONS FOR v1.8:")
print("=" * 80)

# Analyze and recommend improvements
recommendations = []

# Rec 1: Late entry performance
if len(late_losers) > len(late_winners):
    late_loss_rate = len(late_losers) / len(losers) * 100
    recommendations.append(f"1. STRICTER LATE ENTRY: {late_loss_rate:.1f}% of losers are late entries (14:30+)")
    recommendations.append("   → Tighten late entry cutoff to 14:00 OR require 3x volume")

# Rec 2: Symbol selection
worst_symbol = symbol_stats.nsmallest(1, 'Win Rate %').index[0]
worst_wr = symbol_stats.loc[worst_symbol, 'Win Rate %']
if worst_wr < 30:
    recommendations.append(f"2. SYMBOL FILTER: {worst_symbol} has {worst_wr:.1f}% win rate")
    recommendations.append(f"   → Consider excluding symbols with <30% win rate")

# Rec 3: Direction bias
if 'LONG' in direction_stats.index and 'SHORT' in direction_stats.index:
    long_wr = direction_stats.loc['LONG', 'Win Rate %']
    short_wr = direction_stats.loc['SHORT', 'Win Rate %']
    if abs(long_wr - short_wr) > 15:
        better_dir = 'LONG' if long_wr > short_wr else 'SHORT'
        recommendations.append(f"3. DIRECTION BIAS: {better_dir} has {max(long_wr, short_wr):.1f}% win rate vs {min(long_wr, short_wr):.1f}%")
        recommendations.append(f"   → Consider trading only {better_dir} OR add stricter filters for weaker direction")

# Rec 4: SL distance
if losers['SL_Distance_%'].mean() < 0.6:
    recommendations.append(f"4. WIDER STOPS: Average SL distance is {losers['SL_Distance_%'].mean():.3f}%")
    recommendations.append("   → Increase minimum SL to 0.6% or 2.0x ATR (from current 0.5%/1.5x)")

# Rec 5: Volume threshold
recommendations.append("5. VOLUME CONFIRMATION: Test increasing base volume from 1.4x to 1.6x")
recommendations.append("   → Higher volume = stronger conviction = potentially better win rate")

for rec in recommendations:
    print(rec)

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. Implement v1.8 with recommended filters")
print("2. Re-run backtest on same period (Nov 11-29)")
print("3. Compare v1.8 vs v1.7 performance")
print("4. Target: 60%+ win rate with maintained profitability")
print("=" * 80)
