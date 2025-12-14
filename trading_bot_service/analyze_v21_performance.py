"""
Comprehensive Analysis of v2.1 Performance
Analyzing 33 trades (17 wins, 16 losses) to identify improvement opportunities
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Find the most recent backtest results
csv_files = [f for f in os.listdir('.') if f.startswith('backtest_defining_order_') and f.endswith('.csv')]
if not csv_files:
    print("❌ No backtest results found!")
    exit(1)

latest_csv = sorted(csv_files)[-1]
print(f"📊 Analyzing: {latest_csv}\n")

# Load results
df = pd.read_csv(latest_csv)

# Rename columns to match expected format
df.columns = [col.replace('_', ' ').title() for col in df.columns]
df = df.rename(columns={
    'Symbol': 'Symbol',
    'Entry Time': 'Entry Time',
    'Exit Time': 'Exit Time',
    'Direction': 'Direction',
    'Entry Price': 'Entry Price',
    'Exit Price': 'Exit Price',
    'Quantity': 'Quantity',
    'Pnl': 'PnL',
    'Exit Reason': 'Exit Type'
})

# Separate winners and losers
winners = df[df['PnL'] > 0].copy()
losers = df[df['PnL'] < 0].copy()

print("=" * 80)
print("v2.1 PERFORMANCE ANALYSIS - COMPLETE BREAKDOWN")
print("=" * 80)

print(f"\n📈 OVERALL METRICS:")
print(f"   Total Trades: {len(df)}")
print(f"   Winners: {len(winners)} ({len(winners)/len(df)*100:.1f}%)")
print(f"   Losers: {len(losers)} ({len(losers)/len(df)*100:.1f}%)")
print(f"   Total P&L: ₹{df['PnL'].sum():,.2f}")
print(f"   Expectancy: ₹{df['PnL'].mean():,.2f}")

# ============================================================================
# PATTERN 1: SYMBOL BREAKDOWN
# ============================================================================
print("\n" + "=" * 80)
print("PATTERN 1: SYMBOL PERFORMANCE ANALYSIS")
print("=" * 80)

for symbol in sorted(df['Symbol'].unique()):
    symbol_trades = df[df['Symbol'] == symbol]
    symbol_wins = len(symbol_trades[symbol_trades['PnL'] > 0])
    symbol_losses = len(symbol_trades[symbol_trades['PnL'] < 0])
    symbol_wr = symbol_wins / len(symbol_trades) * 100 if len(symbol_trades) > 0 else 0
    symbol_pnl = symbol_trades['PnL'].sum()
    
    status = "✅" if symbol_wr >= 55 else "⚠️" if symbol_wr >= 45 else "❌"
    
    print(f"\n{status} {symbol}:")
    print(f"   Trades: {len(symbol_trades)} | W: {symbol_wins} L: {symbol_losses} | WR: {symbol_wr:.1f}%")
    print(f"   Total P&L: ₹{symbol_pnl:,.2f} | Avg: ₹{symbol_pnl/len(symbol_trades):,.2f}")
    
    if symbol_losses > 0:
        symbol_losers = symbol_trades[symbol_trades['PnL'] < 0]
        print(f"   Avg Loss: ₹{symbol_losers['PnL'].mean():,.2f}")
        print(f"   Loss Concentration: {symbol_losses}/{len(losers)} = {symbol_losses/len(losers)*100:.1f}% of all losses")

# ============================================================================
# PATTERN 2: DIRECTION ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("PATTERN 2: LONG vs SHORT PERFORMANCE")
print("=" * 80)

for direction in ['LONG', 'SHORT']:
    dir_trades = df[df['Direction'] == direction]
    if len(dir_trades) == 0:
        continue
    
    dir_wins = len(dir_trades[dir_trades['PnL'] > 0])
    dir_losses = len(dir_trades[dir_trades['PnL'] < 0])
    dir_wr = dir_wins / len(dir_trades) * 100
    dir_pnl = dir_trades['PnL'].sum()
    
    status = "✅" if dir_wr >= 55 else "⚠️" if dir_wr >= 45 else "❌"
    
    print(f"\n{status} {direction}:")
    print(f"   Trades: {len(dir_trades)} | W: {dir_wins} L: {dir_losses} | WR: {dir_wr:.1f}%")
    print(f"   Total P&L: ₹{dir_pnl:,.2f} | Avg: ₹{dir_pnl/len(dir_trades):,.2f}")
    
    if dir_losses > 0:
        dir_losers = dir_trades[dir_trades['PnL'] < 0]
        print(f"   Avg Loss: ₹{dir_losers['PnL'].mean():,.2f}")

# ============================================================================
# PATTERN 3: HOUR ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("PATTERN 3: TIME-OF-DAY PERFORMANCE")
print("=" * 80)

df['Entry_Hour'] = pd.to_datetime(df['Entry Time']).dt.hour

hour_stats = []
for hour in sorted(df['Entry_Hour'].unique()):
    hour_trades = df[df['Entry_Hour'] == hour]
    hour_wins = len(hour_trades[hour_trades['PnL'] > 0])
    hour_losses = len(hour_trades[hour_trades['PnL'] < 0])
    hour_wr = hour_wins / len(hour_trades) * 100
    hour_pnl = hour_trades['PnL'].sum()
    
    hour_stats.append({
        'Hour': f"{hour:02d}:00",
        'Trades': len(hour_trades),
        'Wins': hour_wins,
        'Losses': hour_losses,
        'WR': hour_wr,
        'Net_PnL': hour_pnl
    })

hour_df = pd.DataFrame(hour_stats)
for _, row in hour_df.iterrows():
    status = "✅" if row['WR'] >= 55 else "⚠️" if row['WR'] >= 45 else "❌"
    pnl_status = "📈" if row['Net_PnL'] > 0 else "📉"
    
    print(f"{status} {row['Hour']}: {row['Trades']} trades | W:{row['Wins']} L:{row['Losses']} | WR:{row['WR']:.1f}% {pnl_status} ₹{row['Net_PnL']:,.0f}")

# ============================================================================
# PATTERN 4: EXIT TYPE ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("PATTERN 4: EXIT TYPE BREAKDOWN")
print("=" * 80)

exit_types = df['Exit Type'].value_counts()
for exit_type, count in exit_types.items():
    exit_trades = df[df['Exit Type'] == exit_type]
    exit_wins = len(exit_trades[exit_trades['PnL'] > 0])
    exit_losses = len(exit_trades[exit_trades['PnL'] < 0])
    exit_wr = exit_wins / len(exit_trades) * 100 if len(exit_trades) > 0 else 0
    exit_pnl = exit_trades['PnL'].sum()
    avg_pnl = exit_pnl / len(exit_trades)
    
    status = "✅" if exit_wr >= 55 else "⚠️" if exit_wr >= 45 else "❌"
    
    print(f"\n{status} {exit_type}:")
    print(f"   Trades: {count} ({count/len(df)*100:.1f}%) | W: {exit_wins} L: {exit_losses} | WR: {exit_wr:.1f}%")
    print(f"   Total P&L: ₹{exit_pnl:,.2f} | Avg: ₹{avg_pnl:,.2f}")

# ============================================================================
# PATTERN 5: DATE ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("PATTERN 5: DAILY PERFORMANCE BREAKDOWN")
print("=" * 80)

df['Entry_Date'] = pd.to_datetime(df['Entry Time']).dt.date

daily_stats = []
for date in sorted(df['Entry_Date'].unique()):
    date_trades = df[df['Entry_Date'] == date]
    date_wins = len(date_trades[date_trades['PnL'] > 0])
    date_losses = len(date_trades[date_trades['PnL'] < 0])
    date_wr = date_wins / len(date_trades) * 100 if len(date_trades) > 0 else 0
    date_pnl = date_trades['PnL'].sum()
    
    daily_stats.append({
        'Date': date,
        'Trades': len(date_trades),
        'Wins': date_wins,
        'Losses': date_losses,
        'WR': date_wr,
        'Net_PnL': date_pnl
    })

daily_df = pd.DataFrame(daily_stats)
print("\n📅 Best Days (Highest WR):")
best_days = daily_df.nlargest(5, 'WR')
for _, row in best_days.iterrows():
    print(f"   {row['Date']}: {row['Trades']} trades | WR: {row['WR']:.0f}% | P&L: ₹{row['Net_PnL']:,.0f}")

print("\n📅 Worst Days (Lowest WR):")
worst_days = daily_df.nsmallest(5, 'WR')
for _, row in worst_days.iterrows():
    print(f"   {row['Date']}: {row['Trades']} trades | WR: {row['WR']:.0f}% | P&L: ₹{row['Net_PnL']:,.0f}")

# Days with 0% WR
zero_wr_days = daily_df[daily_df['WR'] == 0]
if len(zero_wr_days) > 0:
    print(f"\n❌ CRITICAL: {len(zero_wr_days)} days with 0% WR:")
    for _, row in zero_wr_days.iterrows():
        print(f"   {row['Date']}: {row['Losses']} losses, ₹{row['Net_PnL']:,.2f}")

# ============================================================================
# PATTERN 6: LOSS MAGNITUDE ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("PATTERN 6: LOSS SIZE DISTRIBUTION")
print("=" * 80)

if len(losers) > 0:
    print(f"\n📊 Loss Statistics:")
    print(f"   Total Losses: {len(losers)}")
    print(f"   Average Loss: ₹{losers['PnL'].mean():,.2f}")
    print(f"   Median Loss: ₹{losers['PnL'].median():,.2f}")
    print(f"   Smallest Loss: ₹{losers['PnL'].max():,.2f}")
    print(f"   Largest Loss: ₹{losers['PnL'].min():,.2f}")
    
    # Loss buckets
    print(f"\n📊 Loss Distribution:")
    buckets = [
        ("Small (< ₹500)", losers[losers['PnL'] > -500]),
        ("Medium (₹500-800)", losers[(losers['PnL'] <= -500) & (losers['PnL'] > -800)]),
        ("Large (₹800-1100)", losers[(losers['PnL'] <= -800) & (losers['PnL'] > -1100)]),
        ("Very Large (> ₹1100)", losers[losers['PnL'] <= -1100])
    ]
    
    for bucket_name, bucket_trades in buckets:
        count = len(bucket_trades)
        pct = count / len(losers) * 100 if len(losers) > 0 else 0
        total = bucket_trades['PnL'].sum() if count > 0 else 0
        print(f"   {bucket_name}: {count} trades ({pct:.1f}%) = ₹{total:,.0f}")

# ============================================================================
# PATTERN 7: DAY OF WEEK ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("PATTERN 7: DAY OF WEEK PERFORMANCE")
print("=" * 80)

df['Day_of_Week'] = pd.to_datetime(df['Entry Time']).dt.day_name()

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for day in day_order:
    day_trades = df[df['Day_of_Week'] == day]
    if len(day_trades) == 0:
        continue
    
    day_wins = len(day_trades[day_trades['PnL'] > 0])
    day_losses = len(day_trades[day_trades['PnL'] < 0])
    day_wr = day_wins / len(day_trades) * 100
    day_pnl = day_trades['PnL'].sum()
    
    status = "✅" if day_wr >= 55 else "⚠️" if day_wr >= 45 else "❌"
    
    print(f"{status} {day}: {len(day_trades)} trades | W:{day_wins} L:{day_losses} | WR:{day_wr:.1f}% | P&L: ₹{day_pnl:,.0f}")

# ============================================================================
# PATTERN 8: WIN/LOSS COMPARISON
# ============================================================================
print("\n" + "=" * 80)
print("PATTERN 8: WINNERS vs LOSERS CHARACTERISTICS")
print("=" * 80)

if len(winners) > 0 and len(losers) > 0:
    print(f"\n💰 WINNERS ({len(winners)} trades):")
    print(f"   Avg Win: ₹{winners['PnL'].mean():,.2f}")
    print(f"   Median Win: ₹{winners['PnL'].median():,.2f}")
    print(f"   Largest Win: ₹{winners['PnL'].max():,.2f}")
    print(f"   Top Symbols: {', '.join(winners['Symbol'].value_counts().head(3).index.tolist())}")
    
    # Winners by hour
    winners['Entry_Hour'] = pd.to_datetime(winners['Entry Time']).dt.hour
    top_winner_hours = winners['Entry_Hour'].value_counts().head(3)
    print(f"   Top Hours: {', '.join([f'{h:02d}:00' for h in top_winner_hours.index.tolist()])}")
    
    print(f"\n💸 LOSERS ({len(losers)} trades):")
    print(f"   Avg Loss: ₹{losers['PnL'].mean():,.2f}")
    print(f"   Median Loss: ₹{losers['PnL'].median():,.2f}")
    print(f"   Largest Loss: ₹{losers['PnL'].min():,.2f}")
    print(f"   Top Symbols: {', '.join(losers['Symbol'].value_counts().head(3).index.tolist())}")
    
    # Losers by hour
    losers['Entry_Hour'] = pd.to_datetime(losers['Entry Time']).dt.hour
    top_loser_hours = losers['Entry_Hour'].value_counts().head(3)
    print(f"   Top Hours: {', '.join([f'{h:02d}:00' for h in top_loser_hours.index.tolist()])}")
    
    print(f"\n📊 Risk/Reward Ratio:")
    avg_win = winners['PnL'].mean()
    avg_loss = abs(losers['PnL'].mean())
    rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0
    print(f"   Avg Win / Avg Loss = {rr_ratio:.2f}:1")

# ============================================================================
# DETAILED LOSING TRADES ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("DETAILED LOSING TRADES BREAKDOWN")
print("=" * 80)

if len(losers) > 0:
    losers_sorted = losers.sort_values('PnL')
    
    print(f"\n❌ ALL {len(losers)} LOSING TRADES (worst first):\n")
    for idx, row in losers_sorted.iterrows():
        entry_time = pd.to_datetime(row['Entry Time'])
        print(f"{idx+1:2d}. {row['Symbol']:15s} {row['Direction']:5s} | {entry_time.strftime('%Y-%m-%d %H:%M')} | "
              f"Entry: ₹{row['Entry Price']:8.2f} | Exit: {row['Exit Type']:8s} @ ₹{row['Exit Price']:8.2f} | "
              f"P&L: ₹{row['PnL']:8.2f}")

# ============================================================================
# ACTIONABLE RECOMMENDATIONS
# ============================================================================
print("\n" + "=" * 80)
print("🎯 ACTIONABLE RECOMMENDATIONS TO IMPROVE WIN RATE")
print("=" * 80)

recommendations = []

# Check symbol performance
symbol_analysis = df.groupby('Symbol').agg({
    'PnL': ['count', 'sum', lambda x: (x > 0).sum() / len(x) * 100]
}).round(2)
symbol_analysis.columns = ['Trades', 'Total_PnL', 'WR']

worst_symbol = symbol_analysis.loc[symbol_analysis['WR'].idxmin()]
if worst_symbol['WR'] < 40:
    recommendations.append({
        'Priority': 'HIGH',
        'Issue': f"Symbol {worst_symbol.name} has {worst_symbol['WR']:.0f}% WR",
        'Action': f"Consider stricter filters for {worst_symbol.name} or skip if WR < 45%"
    })

# Check for bad hours
hour_analysis = df.groupby('Entry_Hour').agg({
    'PnL': ['count', 'sum', lambda x: (x > 0).sum() / len(x) * 100]
}).round(2)
hour_analysis.columns = ['Trades', 'Total_PnL', 'WR']

bad_hours = hour_analysis[hour_analysis['WR'] < 40]
if len(bad_hours) > 0:
    for hour, row in bad_hours.iterrows():
        if row['Trades'] >= 2:  # Only if significant
            recommendations.append({
                'Priority': 'MEDIUM',
                'Issue': f"Hour {hour:02d}:00 has {row['WR']:.0f}% WR ({row['Trades']:.0f} trades)",
                'Action': f"Consider skipping {hour:02d}:00 hour or add stricter filters"
            })

# Check direction imbalance
dir_analysis = df.groupby('Direction').agg({
    'PnL': ['count', lambda x: (x > 0).sum() / len(x) * 100]
}).round(2)
dir_analysis.columns = ['Trades', 'WR']

for direction, row in dir_analysis.iterrows():
    if row['WR'] < 45:
        recommendations.append({
            'Priority': 'MEDIUM',
            'Issue': f"{direction} trades have {row['WR']:.0f}% WR",
            'Action': f"Add stronger {direction} filters (e.g., stricter RSI, trend strength)"
        })

# Check loss concentration
if len(losers) > 0:
    sl_losses = losers[losers['Exit Type'] == 'SL']
    if len(sl_losses) / len(losers) > 0.8:
        recommendations.append({
            'Priority': 'HIGH',
            'Issue': f"{len(sl_losses)/len(losers)*100:.0f}% of losses hit SL",
            'Action': "Consider tighter initial filters or better entry confirmation"
        })

# Print recommendations
if recommendations:
    print("\n📋 Prioritized Improvement Actions:\n")
    
    for priority in ['HIGH', 'MEDIUM', 'LOW']:
        priority_recs = [r for r in recommendations if r['Priority'] == priority]
        if priority_recs:
            print(f"\n{priority} PRIORITY:")
            for i, rec in enumerate(priority_recs, 1):
                print(f"   {i}. Issue: {rec['Issue']}")
                print(f"      Action: {rec['Action']}")
else:
    print("\n✅ No critical issues found. Strategy is performing well!")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
