"""
v1.9 Losing Trades Analysis
Analyzes the 54 losing trades from v1.9 backtest to identify patterns and enhancement opportunities
"""
import pandas as pd
import numpy as np

# Load the latest v1.9 backtest results
df = pd.read_csv('backtest_defining_order_20251214_033225.csv')

print('=' * 80)
print('v1.9 BACKTEST ANALYSIS (90 trades, 40% WR, 16.38% return)')
print('=' * 80)
print(f'Total trades: {len(df)}')
print(f'Winners: {len(df[df["pnl"] > 0])} ({len(df[df["pnl"] > 0])/len(df)*100:.2f}%)')
print(f'Losers: {len(df[df["pnl"] < 0])} ({len(df[df["pnl"] < 0])/len(df)*100:.2f}%)')
print()

# Focus on losers
losers = df[df['pnl'] < 0].copy()
winners = df[df['pnl'] > 0].copy()

print('=' * 80)
print(f'ANALYZING {len(losers)} LOSING TRADES')
print('=' * 80)
print()

# 1. Symbol breakdown
print('📊 PATTERN 1: LOSERS BY SYMBOL')
print('-' * 80)
symbol_losers = losers.groupby('symbol').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
symbol_losers.columns = ['Loser_Count', 'Total_Loss', 'Avg_Loss']

# Add winners for comparison
symbol_winners = winners.groupby('symbol').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
symbol_winners.columns = ['Winner_Count', 'Total_Win', 'Avg_Win']

# Combine
symbol_comparison = pd.concat([symbol_losers, symbol_winners], axis=1).fillna(0)
symbol_comparison['Win_Rate'] = (symbol_comparison['Winner_Count'] / 
                                  (symbol_comparison['Winner_Count'] + symbol_comparison['Loser_Count']) * 100).round(2)
symbol_comparison['Net_PnL'] = symbol_comparison['Total_Win'] + symbol_comparison['Total_Loss']
symbol_comparison = symbol_comparison.sort_values('Win_Rate')

print(symbol_comparison)
print()

# 2. Direction breakdown
print('📊 PATTERN 2: LOSERS BY DIRECTION')
print('-' * 80)
dir_losers = losers.groupby('direction').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
dir_losers.columns = ['Loser_Count', 'Total_Loss', 'Avg_Loss']

dir_winners = winners.groupby('direction').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
dir_winners.columns = ['Winner_Count', 'Total_Win', 'Avg_Win']

dir_comparison = pd.concat([dir_losers, dir_winners], axis=1).fillna(0)
dir_comparison['Win_Rate'] = (dir_comparison['Winner_Count'] / 
                               (dir_comparison['Winner_Count'] + dir_comparison['Loser_Count']) * 100).round(2)
print(dir_comparison)
print()

# 3. Time of day analysis
print('📊 PATTERN 3: LOSERS BY HOUR OF DAY')
print('-' * 80)
losers['Hour'] = pd.to_datetime(losers['entry_time']).dt.hour
winners['Hour'] = pd.to_datetime(winners['entry_time']).dt.hour

hour_losers = losers.groupby('Hour').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
hour_losers.columns = ['Loser_Count', 'Total_Loss', 'Avg_Loss']

hour_winners = winners.groupby('Hour').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
hour_winners.columns = ['Winner_Count', 'Total_Win', 'Avg_Win']

hour_comparison = pd.concat([hour_losers, hour_winners], axis=1).fillna(0)
hour_comparison['Win_Rate'] = (hour_comparison['Winner_Count'] / 
                                (hour_comparison['Winner_Count'] + hour_comparison['Loser_Count']) * 100).round(2)
hour_comparison = hour_comparison.sort_values('Win_Rate')
print(hour_comparison)
print()

# 4. Exit type analysis
print('📊 PATTERN 4: LOSERS BY EXIT TYPE')
print('-' * 80)
losers['Exit_Type'] = losers['exit_reason'].apply(lambda x: 'SL Hit' if 'SL' in str(x) else 'EOD Close')
exit_losers = losers.groupby('Exit_Type').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
exit_losers.columns = ['Trades', 'Total_Loss', 'Avg_Loss']
exit_losers['Percentage'] = (exit_losers['Trades'] / len(losers) * 100).round(2)
print(exit_losers)
print()

# 5. Date analysis
print('📊 PATTERN 5: WORST DAYS (Most Losing Trades)')
print('-' * 80)
losers['Date'] = pd.to_datetime(losers['entry_time']).dt.date
winners['Date'] = pd.to_datetime(winners['entry_time']).dt.date

day_losers = losers.groupby('Date').agg({
    'pnl': ['count', 'sum']
}).round(2)
day_losers.columns = ['Loser_Count', 'Total_Loss']

day_winners = winners.groupby('Date').agg({
    'pnl': ['count', 'sum']
}).round(2)
day_winners.columns = ['Winner_Count', 'Total_Win']

day_comparison = pd.concat([day_losers, day_winners], axis=1).fillna(0)
day_comparison['Win_Rate'] = (day_comparison['Winner_Count'] / 
                               (day_comparison['Winner_Count'] + day_comparison['Loser_Count']) * 100).round(2)
day_comparison = day_comparison.sort_values('Win_Rate')
print(day_comparison)
print()

# 6. Loss magnitude analysis
print('📊 PATTERN 6: LOSS MAGNITUDE DISTRIBUTION')
print('-' * 80)
print(f'Smallest loss: ₹{losers["pnl"].max():.2f}')
print(f'Largest loss: ₹{losers["pnl"].min():.2f}')
print(f'Average loss: ₹{losers["pnl"].mean():.2f}')
print(f'Median loss: ₹{losers["pnl"].median():.2f}')
print()

# Categorize losses
losers['Loss_Category'] = pd.cut(losers['pnl'], 
                                  bins=[-2000, -1150, -1000, -500, 0],
                                  labels=['Large (>1150)', 'Medium (1000-1150)', 'Small (500-1000)', 'Tiny (<500)'])
print('Loss Distribution:')
print(losers['Loss_Category'].value_counts().sort_index())
print()

# 7. Day of week analysis
print('📊 PATTERN 7: LOSERS BY DAY OF WEEK')
print('-' * 80)
losers['DayOfWeek'] = pd.to_datetime(losers['entry_time']).dt.day_name()
winners['DayOfWeek'] = pd.to_datetime(winners['entry_time']).dt.day_name()

dow_losers = losers.groupby('DayOfWeek').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
dow_losers.columns = ['Loser_Count', 'Total_Loss', 'Avg_Loss']

dow_winners = winners.groupby('DayOfWeek').agg({
    'pnl': ['count', 'sum', 'mean']
}).round(2)
dow_winners.columns = ['Winner_Count', 'Total_Win', 'Avg_Win']

dow_comparison = pd.concat([dow_losers, dow_winners], axis=1).fillna(0)
dow_comparison['Win_Rate'] = (dow_comparison['Winner_Count'] / 
                               (dow_comparison['Winner_Count'] + dow_comparison['Loser_Count']) * 100).round(2)

# Order by weekday
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
dow_comparison = dow_comparison.reindex([d for d in weekday_order if d in dow_comparison.index])
print(dow_comparison)
print()

# 8. Save detailed analysis
print('=' * 80)
print('SAVING DETAILED REPORTS...')
print('=' * 80)

# Save losing trades with all analysis columns
losers_detailed = losers[[
    'Date', 'DayOfWeek', 'symbol', 'direction', 'entry_time', 'Hour',
    'entry_price', 'exit_price', 'exit_reason', 'Exit_Type', 'pnl', 'Loss_Category'
]].copy()
losers_detailed = losers_detailed.sort_values('pnl')
losers_detailed.to_csv('v19_losing_trades_detailed.csv', index=False)
print('✅ Detailed losing trades saved to v19_losing_trades_detailed.csv')

# Save summary statistics
with open('v19_loss_analysis_summary.txt', 'w') as f:
    f.write('=' * 80 + '\n')
    f.write('v1.9 LOSING TRADES ANALYSIS SUMMARY\n')
    f.write('=' * 80 + '\n\n')
    
    f.write('TOP 5 CRITICAL PATTERNS:\n\n')
    
    f.write('1. WORST PERFORMING SYMBOLS:\n')
    worst_symbols = symbol_comparison[symbol_comparison['Win_Rate'] < 40].sort_values('Win_Rate')
    f.write(worst_symbols.to_string())
    f.write('\n\n')
    
    f.write('2. WORST HOURS OF DAY:\n')
    worst_hours = hour_comparison[hour_comparison['Win_Rate'] < 40].sort_values('Win_Rate')
    f.write(worst_hours.to_string())
    f.write('\n\n')
    
    f.write('3. STOP LOSS HIT RATE:\n')
    f.write(exit_losers.to_string())
    f.write('\n\n')
    
    f.write('4. WORST DAYS:\n')
    worst_days = day_comparison[day_comparison['Win_Rate'] < 40].sort_values('Win_Rate')
    f.write(worst_days.to_string())
    f.write('\n\n')
    
    f.write('5. DIRECTIONAL BIAS:\n')
    f.write(dir_comparison.to_string())
    f.write('\n')

print('✅ Summary analysis saved to v19_loss_analysis_summary.txt')
print()

print('=' * 80)
print('ANALYSIS COMPLETE')
print('=' * 80)
