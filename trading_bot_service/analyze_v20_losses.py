"""
Comprehensive Loss Analysis for v2.0 ENHANCED PRECISION
Analyzing 36 losing trades to identify patterns and improvements
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Read the v2.0 backtest results
df = pd.read_csv('backtest_defining_order_20251214_035231.csv')

print("=" * 80)
print("v2.0 ENHANCED PRECISION - LOSING TRADES ANALYSIS")
print("=" * 80)
print(f"\nTotal trades: {len(df)}")
print(f"Winning trades: {len(df[df['pnl'] > 0])}")
print(f"Losing trades: {len(df[df['pnl'] < 0])}")
print(f"Win Rate: {(len(df[df['pnl'] > 0]) / len(df) * 100):.2f}%")

# Filter losing trades
losers_df = df[df['pnl'] < 0].copy()
winners = df[df['pnl'] > 0].copy()

print(f"\n{'='*80}")
print("ANALYZING {0} LOSING TRADES".format(len(losers_df)))
print("=" * 80)

# Add analysis columns to losers
losers_df['entry_time'] = pd.to_datetime(losers_df['entry_time'])
losers_df['exit_time'] = pd.to_datetime(losers_df['exit_time'])
losers_df['entry_hour'] = losers_df['entry_time'].dt.hour
losers_df['entry_day'] = losers_df['entry_time'].dt.day
losers_df['day_of_week'] = losers_df['entry_time'].dt.day_name()
losers_df['trade_duration_minutes'] = (losers_df['exit_time'] - losers_df['entry_time']).dt.total_seconds() / 60

# Add analysis columns to winners
winners['entry_time'] = pd.to_datetime(winners['entry_time'])
winners['exit_time'] = pd.to_datetime(winners['exit_time'])
winners['trade_duration_minutes'] = (winners['exit_time'] - winners['entry_time']).dt.total_seconds() / 60

# Calculate loss magnitude categories
losers_df['loss_category'] = pd.cut(
    abs(losers_df['pnl']),
    bins=[0, 500, 800, 1000, 1200, 10000],
    labels=['₹0-500', '₹500-800', '₹800-1000', '₹1000-1200', '₹1200+']
)

print("\n" + "=" * 80)
print("PATTERN 1: LOSERS BY SYMBOL")
print("=" * 80)

symbol_analysis = df.groupby('symbol').agg({
    'pnl': ['count', lambda x: (x < 0).sum(), lambda x: (x > 0).sum(), 'sum', 'mean']
}).round(2)
symbol_analysis.columns = ['Total_Trades', 'Losers', 'Winners', 'Net_PnL', 'Avg_PnL']
symbol_analysis['Win_Rate'] = (symbol_analysis['Winners'] / symbol_analysis['Total_Trades'] * 100).round(2)
symbol_analysis = symbol_analysis.sort_values('Win_Rate')

print(symbol_analysis.to_string())

print("\n🔍 Symbol Insights:")
worst_symbol = symbol_analysis.index[0]
best_symbol = symbol_analysis.iloc[-1].name
print(f"   ⚠️ WORST: {worst_symbol} - {symbol_analysis.loc[worst_symbol, 'Win_Rate']:.1f}% WR, ₹{symbol_analysis.loc[worst_symbol, 'Net_PnL']:.0f} net")
print(f"   ✅ BEST: {best_symbol} - {symbol_analysis.loc[best_symbol, 'Win_Rate']:.1f}% WR, ₹{symbol_analysis.loc[best_symbol, 'Net_PnL']:.0f} net")

# Identify symbols to consider excluding
problem_symbols = symbol_analysis[
    (symbol_analysis['Win_Rate'] < 40) | (symbol_analysis['Net_PnL'] < 0)
]
if len(problem_symbols) > 0:
    print(f"\n   🚨 PROBLEM SYMBOLS (WR<40% OR Negative Net):")
    for sym in problem_symbols.index:
        wr = symbol_analysis.loc[sym, 'Win_Rate']
        net = symbol_analysis.loc[sym, 'Net_PnL']
        print(f"      - {sym}: {wr:.1f}% WR, ₹{net:.0f} net")

print("\n" + "=" * 80)
print("PATTERN 2: LOSERS BY DIRECTION (LONG vs SHORT)")
print("=" * 80)

direction_analysis = df.groupby('direction').agg({
    'pnl': ['count', lambda x: (x < 0).sum(), lambda x: (x > 0).sum(), 'sum', 'mean']
}).round(2)
direction_analysis.columns = ['Total_Trades', 'Losers', 'Winners', 'Net_PnL', 'Avg_PnL']
direction_analysis['Win_Rate'] = (direction_analysis['Winners'] / direction_analysis['Total_Trades'] * 100).round(2)

print(direction_analysis.to_string())

long_data = direction_analysis.loc['LONG'] if 'LONG' in direction_analysis.index else None
short_data = direction_analysis.loc['SHORT'] if 'SHORT' in direction_analysis.index else None

print("\n🔍 Direction Insights:")
if long_data is not None and short_data is not None:
    print(f"   LONG:  {long_data['Win_Rate']:.1f}% WR, ₹{long_data['Net_PnL']:.0f} net, ₹{long_data['Avg_PnL']:.0f} avg")
    print(f"   SHORT: {short_data['Win_Rate']:.1f}% WR, ₹{short_data['Net_PnL']:.0f} net, ₹{short_data['Avg_PnL']:.0f} avg")
    
    if long_data['Win_Rate'] < short_data['Win_Rate']:
        diff = short_data['Win_Rate'] - long_data['Win_Rate']
        print(f"\n   ⚠️ LONG underperforming SHORT by {diff:.1f}% WR")
        print(f"   💡 Consider: Stricter filters for LONG trades")

print("\n" + "=" * 80)
print("PATTERN 3: LOSERS BY HOUR OF DAY")
print("=" * 80)

hour_analysis = df.copy()
hour_analysis['entry_hour'] = pd.to_datetime(hour_analysis['entry_time']).dt.hour
hour_stats = hour_analysis.groupby('entry_hour').agg({
    'pnl': ['count', lambda x: (x < 0).sum(), lambda x: (x > 0).sum(), 'sum']
}).round(2)
hour_stats.columns = ['Total', 'Losers', 'Winners', 'Net_PnL']
hour_stats['Win_Rate'] = (hour_stats['Winners'] / hour_stats['Total'] * 100).round(2)
hour_stats = hour_stats.sort_values('Win_Rate')

print(hour_stats.to_string())

print("\n🔍 Hour Insights:")
worst_hours = hour_stats[hour_stats['Win_Rate'] < 40]
if len(worst_hours) > 0:
    print("   ⚠️ WORST HOURS (WR < 40%):")
    for hour in worst_hours.index:
        wr = hour_stats.loc[hour, 'Win_Rate']
        losers = hour_stats.loc[hour, 'Losers']
        total = hour_stats.loc[hour, 'Total']
        print(f"      {hour:02d}:00 - {wr:.1f}% WR ({losers}/{total} trades)")

best_hours = hour_stats[hour_stats['Win_Rate'] >= 50]
if len(best_hours) > 0:
    print("   ✅ BEST HOURS (WR >= 50%):")
    for hour in best_hours.index:
        wr = hour_stats.loc[hour, 'Win_Rate']
        winners = hour_stats.loc[hour, 'Winners']
        total = hour_stats.loc[hour, 'Total']
        print(f"      {hour:02d}:00 - {wr:.1f}% WR ({winners}/{total} trades)")

print("\n" + "=" * 80)
print("PATTERN 4: LOSERS BY EXIT TYPE")
print("=" * 80)

exit_analysis = losers_df.groupby('exit_reason').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
exit_analysis.columns = ['Count', 'Total_Loss', 'Avg_Loss']
exit_analysis['Percentage'] = (exit_analysis['Count'] / len(losers_df) * 100).round(2)
exit_analysis = exit_analysis.sort_values('Count', ascending=False)

print(exit_analysis.to_string())

print("\n🔍 Exit Type Insights:")
sl_hits = exit_analysis.loc['SL Hit', 'Count'] if 'SL Hit' in exit_analysis.index else 0
eod_closes = exit_analysis.loc['EOD Close', 'Count'] if 'EOD Close' in exit_analysis.index else 0

print(f"   SL Hits: {sl_hits}/{len(losers_df)} ({sl_hits/len(losers_df)*100:.1f}%)")
print(f"   EOD Closes: {eod_closes}/{len(losers_df)} ({eod_closes/len(losers_df)*100:.1f}%)")

if sl_hits > 0:
    print(f"\n   ✅ IMPROVEMENT from v1.9: SL now hitting (was 0% in v1.9)")
    print(f"   💡 This means tighter SL (1.5x ATR for lunch) is working!")

print("\n" + "=" * 80)
print("PATTERN 5: LOSERS BY DATE")
print("=" * 80)

date_analysis = df.copy()
date_analysis['date'] = pd.to_datetime(date_analysis['entry_time']).dt.date
date_stats = date_analysis.groupby('date').agg({
    'pnl': ['count', lambda x: (x < 0).sum(), lambda x: (x > 0).sum(), 'sum']
}).round(2)
date_stats.columns = ['Total', 'Losers', 'Winners', 'Net_PnL']
date_stats['Win_Rate'] = (date_stats['Winners'] / date_stats['Total'] * 100).round(2)
date_stats = date_stats.sort_values('Win_Rate')

print(date_stats.to_string())

print("\n🔍 Date Insights:")
bad_days = date_stats[date_stats['Win_Rate'] == 0]
if len(bad_days) > 0:
    print(f"   🚨 WORST DAYS (0% WR): {len(bad_days)} days")
    for date in bad_days.index:
        losers_count = date_stats.loc[date, 'Losers']
        loss = date_stats.loc[date, 'Net_PnL']
        print(f"      {date}: {losers_count} losers, ₹{loss:.0f} damage")

print("\n" + "=" * 80)
print("PATTERN 6: LOSS MAGNITUDE DISTRIBUTION")
print("=" * 80)

loss_dist = losers_df.groupby('loss_category').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
loss_dist.columns = ['Count', 'Total_Loss', 'Avg_Loss']
loss_dist['Percentage'] = (loss_dist['Count'] / len(losers_df) * 100).round(2)

print(loss_dist.to_string())

print("\n🔍 Loss Magnitude Insights:")
large_losses = losers_df[abs(losers_df['pnl']) >= 1000]
print(f"   Losses ≥ ₹1,000: {len(large_losses)}/{len(losers_df)} ({len(large_losses)/len(losers_df)*100:.1f}%)")
print(f"   Average loss: ₹{abs(losers_df['pnl'].mean()):.2f}")
print(f"   Largest loss: ₹{abs(losers_df['pnl'].min()):.2f}")

print("\n" + "=" * 80)
print("PATTERN 7: LOSERS BY DAY OF WEEK")
print("=" * 80)

dow_analysis = df.copy()
dow_analysis['day_of_week'] = pd.to_datetime(dow_analysis['entry_time']).dt.day_name()
dow_stats = dow_analysis.groupby('day_of_week').agg({
    'pnl': ['count', lambda x: (x < 0).sum(), lambda x: (x > 0).sum(), 'sum', 'mean']
}).round(2)
dow_stats.columns = ['Total', 'Losers', 'Winners', 'Net_PnL', 'Avg_PnL']
dow_stats['Win_Rate'] = (dow_stats['Winners'] / dow_stats['Total'] * 100).round(2)

# Reorder by weekday
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
dow_stats = dow_stats.reindex([d for d in day_order if d in dow_stats.index])

print(dow_stats.to_string())

print("\n🔍 Day of Week Insights:")
worst_day = dow_stats['Win_Rate'].idxmin()
best_day = dow_stats['Win_Rate'].idxmax()
print(f"   ⚠️ WORST: {worst_day} - {dow_stats.loc[worst_day, 'Win_Rate']:.1f}% WR, ₹{dow_stats.loc[worst_day, 'Avg_PnL']:.0f} avg")
print(f"   ✅ BEST: {best_day} - {dow_stats.loc[best_day, 'Win_Rate']:.1f}% WR, ₹{dow_stats.loc[best_day, 'Avg_PnL']:.0f} avg")

print("\n" + "=" * 80)
print("PATTERN 8: TRADE DURATION ANALYSIS")
print("=" * 80)

print(f"\nLosing Trades Duration:")
print(f"   Average: {losers_df['trade_duration_minutes'].mean():.1f} minutes")
print(f"   Median: {losers_df['trade_duration_minutes'].median():.1f} minutes")
print(f"   Min: {losers_df['trade_duration_minutes'].min():.1f} minutes")
print(f"   Max: {losers_df['trade_duration_minutes'].max():.1f} minutes")

print(f"\nWinning Trades Duration:")
print(f"   Average: {winners['trade_duration_minutes'].mean():.1f} minutes")
print(f"   Median: {winners['trade_duration_minutes'].median():.1f} minutes")

quick_losses = losers_df[losers_df['trade_duration_minutes'] < 30]
print(f"\nQuick losses (<30 min): {len(quick_losses)}/{len(losers_df)} ({len(quick_losses)/len(losers_df)*100:.1f}%)")
print(f"   Average loss: ₹{abs(quick_losses['pnl'].mean()):.2f}")

print("\n" + "=" * 80)
print("CRITICAL ISSUES SUMMARY")
print("=" * 80)

issues = []

# Issue 1: Check worst symbol
if len(problem_symbols) > 0:
    issues.append({
        'priority': 'HIGH',
        'issue': f"{len(problem_symbols)} symbols with WR<40% or negative net",
        'symbols': list(problem_symbols.index),
        'impact': f"{problem_symbols['Losers'].sum()} losers, ₹{abs(problem_symbols['Net_PnL'].sum()):.0f} loss"
    })

# Issue 2: Check direction imbalance
if long_data is not None and short_data is not None:
    if abs(long_data['Win_Rate'] - short_data['Win_Rate']) > 5:
        issues.append({
            'priority': 'MEDIUM',
            'issue': f"LONG/SHORT imbalance: {abs(long_data['Win_Rate'] - short_data['Win_Rate']):.1f}% difference",
            'impact': f"Weaker direction has {min(long_data['Win_Rate'], short_data['Win_Rate']):.1f}% WR"
        })

# Issue 3: Check worst hours
if len(worst_hours) > 0:
    issues.append({
        'priority': 'MEDIUM',
        'issue': f"{len(worst_hours)} hours with WR<40%",
        'hours': list(worst_hours.index),
        'impact': f"{worst_hours['Losers'].sum()} losers from these hours"
    })

# Issue 4: EOD closes
if eod_closes > len(losers_df) * 0.5:
    issues.append({
        'priority': 'HIGH',
        'issue': f"{eod_closes/len(losers_df)*100:.1f}% of losses are EOD closes",
        'impact': "SL not tight enough or trailing stops needed"
    })

# Issue 5: Large losses
large_loss_pct = len(large_losses) / len(losers_df) * 100
if large_loss_pct > 70:
    issues.append({
        'priority': 'MEDIUM',
        'issue': f"{large_loss_pct:.1f}% of losses ≥ ₹1,000",
        'impact': f"Average loss: ₹{abs(losers_df['pnl'].mean()):.0f}"
    })

if len(issues) == 0:
    print("\n✅ No critical issues identified!")
else:
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. [{issue['priority']}] {issue['issue']}")
        if 'symbols' in issue:
            print(f"   Symbols: {', '.join(issue['symbols'])}")
        if 'hours' in issue:
            print(f"   Hours: {', '.join([f'{h:02d}:00' for h in issue['hours']])}")
        print(f"   Impact: {issue['impact']}")

print("\n" + "=" * 80)
print("RECOMMENDED ENHANCEMENTS (v2.1)")
print("=" * 80)

recommendations = []

# Rec 1: Symbol exclusions
if len(problem_symbols) > 0:
    recommendations.append({
        'priority': 1,
        'enhancement': f"EXCLUDE {len(problem_symbols)} underperforming symbols",
        'symbols': list(problem_symbols.index),
        'expected_impact': f"Remove {problem_symbols['Losers'].sum()} losers, avoid ₹{abs(problem_symbols['Net_PnL'].sum()):.0f} loss"
    })

# Rec 2: Direction filters
if long_data is not None and short_data is not None:
    if long_data['Win_Rate'] < short_data['Win_Rate'] - 5:
        recommendations.append({
            'priority': 2,
            'enhancement': "STRICTER LONG filters (require 2.0x volume)",
            'rationale': f"LONG: {long_data['Win_Rate']:.1f}% WR vs SHORT: {short_data['Win_Rate']:.1f}% WR",
            'expected_impact': "Reduce LONG losers by 20-30%"
        })

# Rec 3: Hour-based filters
if len(worst_hours) > 0:
    recommendations.append({
        'priority': 3,
        'enhancement': f"AVOID/STRICTER filters for worst hours",
        'hours': list(worst_hours.index),
        'expected_impact': f"Remove {worst_hours['Losers'].sum()} losers from bad hours"
    })

# Rec 4: Trailing stops
if eod_closes > len(losers_df) * 0.5:
    recommendations.append({
        'priority': 2,
        'enhancement': "IMPLEMENT trailing stops (move to breakeven at 50% TP)",
        'rationale': f"{eod_closes} losers ({eod_closes/len(losers_df)*100:.1f}%) hit EOD instead of SL",
        'expected_impact': "Convert some losers to breakeven exits"
    })

if len(recommendations) > 0:
    for rec in recommendations:
        print(f"\n{rec['priority']}. {rec['enhancement']}")
        if 'symbols' in rec:
            print(f"   Symbols: {', '.join(rec['symbols'])}")
        if 'hours' in rec:
            print(f"   Hours: {', '.join([f'{h:02d}:00' for h in rec['hours']])}")
        if 'rationale' in rec:
            print(f"   Why: {rec['rationale']}")
        print(f"   Expected: {rec['expected_impact']}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

# Save detailed losers to CSV
losers_detailed = losers[[
    'entry_time', 'exit_time', 'symbol', 'direction', 'entry_price', 'exit_price',
    'stop_loss', 'take_profit', 'quantity', 'pnl', 'exit_reason',
    'entry_hour', 'day_of_week', 'trade_duration_minutes', 'loss_category'
]].copy()

output_file = 'v20_losing_trades_detailed.csv'
losers_detailed.to_csv(output_file, index=False)
print(f"\n✅ Detailed losing trades saved to: {output_file}")

# Save summary
summary_file = 'v20_loss_analysis_summary.txt'
with open(summary_file, 'w') as f:
    f.write("v2.0 LOSS ANALYSIS SUMMARY\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Total Losing Trades: {len(losers_df)}\n")
    f.write(f"Average Loss: ₹{abs(losers_df['pnl'].mean()):.2f}\n")
    f.write(f"Largest Loss: ₹{abs(losers_df['pnl'].min()):.2f}\n\n")
    
    f.write("Critical Issues:\n")
    for i, issue in enumerate(issues, 1):
        f.write(f"{i}. [{issue['priority']}] {issue['issue']}\n")
        f.write(f"   Impact: {issue['impact']}\n\n")
    
    f.write("\nRecommended Enhancements:\n")
    for rec in recommendations:
        f.write(f"{rec['priority']}. {rec['enhancement']}\n")
        f.write(f"   Expected: {rec['expected_impact']}\n\n")

print(f"✅ Summary saved to: {summary_file}")
print("\n" + "=" * 80)
