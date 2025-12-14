import pandas as pd
import numpy as np
import sys

# Read backtest results from command line argument or default
if len(sys.argv) > 1:
    csv_file = sys.argv[1]
else:
    csv_file = 'backtest_defining_order_20251214_120206.csv'  # LATEST: 11:00 hour blocked
    
df = pd.read_csv(csv_file)

print('='*80)
print('DEEP ANALYSIS: WINS VS LOSSES - Dec 1-12, 2025 (NIFTY 50)')
print('='*80)

# Separate wins and losses
wins = df[df['pnl'] > 0]
losses = df[df['pnl'] < 0]

print(f'\n📊 OVERALL STATS:')
print(f'Total Trades: {len(df)}')
print(f'Wins: {len(wins)} ({len(wins)/len(df)*100:.1f}%)')
print(f'Losses: {len(losses)} ({len(losses)/len(df)*100:.1f}%)')
print(f'Total P&L: ₹{df["pnl"].sum():.2f}')
print(f'Avg Win: ₹{wins["pnl"].mean():.2f}' if len(wins) > 0 else 'No wins')
print(f'Avg Loss: ₹{losses["pnl"].mean():.2f}' if len(losses) > 0 else 'No losses')

# Win/Loss by Direction
print(f'\n📈 BY DIRECTION:')
for direction in ['LONG', 'SHORT']:
    dir_df = df[df['direction'] == direction]
    dir_wins = dir_df[dir_df['pnl'] > 0]
    dir_losses = dir_df[dir_df['pnl'] < 0]
    if len(dir_df) > 0:
        print(f'\n{direction}:')
        print(f'  Trades: {len(dir_df)}')
        print(f'  Win Rate: {len(dir_wins)/len(dir_df)*100:.1f}%')
        if len(dir_wins) > 0:
            print(f'  Avg Win: ₹{dir_wins["pnl"].mean():.2f}')
        else:
            print(f'  No wins')
        if len(dir_losses) > 0:
            print(f'  Avg Loss: ₹{dir_losses["pnl"].mean():.2f}')
        else:
            print(f'  No losses')
        print(f'  Net P&L: ₹{dir_df["pnl"].sum():.2f}')

# Win/Loss by Day of Week
print(f'\n📅 BY DAY OF WEEK:')
df['date_dt'] = pd.to_datetime(df['entry_time'])
df['day_of_week'] = df['date_dt'].dt.day_name()
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
    day_df = df[df['day_of_week'] == day]
    if len(day_df) > 0:
        day_wins = day_df[day_df['pnl'] > 0]
        print(f'\n{day}:')
        print(f'  Trades: {len(day_df)}')
        print(f'  Win Rate: {len(day_wins)/len(day_df)*100:.1f}%')
        print(f'  Net P&L: ₹{day_df["pnl"].sum():.2f}')

# Win/Loss by Hour
print(f'\n🕐 BY HOUR OF DAY:')
df['hour'] = pd.to_datetime(df['entry_time']).dt.hour
hour_stats = df.groupby('hour').agg({
    'pnl': ['count', lambda x: (x > 0).sum(), 'sum', 'mean']
}).round(2)
hour_stats.columns = ['Trades', 'Wins', 'Total P&L', 'Avg P&L']
hour_stats['Win Rate %'] = (hour_stats['Wins'] / hour_stats['Trades'] * 100).round(1)
print(hour_stats.to_string())

# Top/Bottom performing symbols
print(f'\n🏆 TOP 5 SYMBOLS (by P&L):')
symbol_pnl = df.groupby('symbol')['pnl'].sum().sort_values(ascending=False)
print(symbol_pnl.head(5).to_string())

print(f'\n💀 BOTTOM 5 SYMBOLS (by P&L):')
print(symbol_pnl.tail(5).to_string())

# Symbol performance stats
print(f'\n📋 SYMBOLS WITH TRADES:')
symbol_stats = df.groupby('symbol').agg({
    'pnl': ['count', lambda x: (x > 0).sum(), 'sum']
}).round(2)
symbol_stats.columns = ['Trades', 'Wins', 'Total P&L']
symbol_stats['Win Rate %'] = (symbol_stats['Wins'] / symbol_stats['Trades'] * 100).round(1)
print(symbol_stats.sort_values('Total P&L', ascending=False).to_string())

# Exit reason analysis
print(f'\n🎯 EXIT REASONS:')
exit_stats = df.groupby('exit_reason').agg({
    'pnl': ['count', lambda x: (x > 0).sum(), 'sum']
}).round(2)
exit_stats.columns = ['Trades', 'Wins', 'Total P&L']
exit_stats['Win Rate %'] = (exit_stats['Wins'] / exit_stats['Trades'] * 100).round(1)
print(exit_stats.to_string())

# Trade duration patterns
print(f'\n⏱️ TRADE DURATION ANALYSIS:')
df['entry_time_dt'] = pd.to_datetime(df['entry_time'])
df['exit_time_dt'] = pd.to_datetime(df['exit_time'])
df['duration_minutes'] = (df['exit_time_dt'] - df['entry_time_dt']).dt.total_seconds() / 60
print(f'Avg Win Duration: {df[df["pnl"] > 0]["duration_minutes"].mean():.1f} min')
print(f'Avg Loss Duration: {df[df["pnl"] < 0]["duration_minutes"].mean():.1f} min')

print('\n' + '='*80)
