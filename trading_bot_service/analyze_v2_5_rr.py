import pandas as pd
import numpy as np

# Load v2.5 results
df = pd.read_csv('backtest_defining_order_20251214_112010.csv')
df['entry_time'] = pd.to_datetime(df['entry_time'])
df['exit_time'] = pd.to_datetime(df['exit_time'])

print('=' * 80)
print('v2.5 RISK-REWARD ANALYSIS')
print('=' * 80)
print()

# Calculate Risk and Reward for each trade
df['trade_date'] = df['entry_time'].dt.date

# For LONG trades
long_trades = df[df['direction'] == 'LONG'].copy()
# For SHORT trades
short_trades = df[df['direction'] == 'SHORT'].copy()

# Calculate actual risk taken and reward achieved
def calculate_rr(row):
    if row['direction'] == 'LONG':
        # Risk = Entry - implied SL (we can estimate from SL hits)
        # Reward = TP - Entry (we can estimate from TP hits)
        if row['exit_reason'] == 'Take Profit':
            reward = row['pnl'] / row['quantity']
            return reward
        elif row['exit_reason'] == 'Stop Loss':
            risk = abs(row['pnl'] / row['quantity'])
            return -risk
    else:  # SHORT
        if row['exit_reason'] == 'Take Profit':
            reward = row['pnl'] / row['quantity']
            return reward
        elif row['exit_reason'] == 'Stop Loss':
            risk = abs(row['pnl'] / row['quantity'])
            return -risk
    return np.nan

df['rr_value'] = df.apply(calculate_rr, axis=1)

# Analyze TP and SL separately
tp_trades = df[df['exit_reason'] == 'Take Profit']
sl_trades = df[df['exit_reason'] == 'Stop Loss']

print('📊 EXIT BREAKDOWN:')
print(f'  Total Trades: {len(df)}')
print(f'  TP Hits: {len(tp_trades)} (100% WR)')
print(f'  SL Hits: {len(sl_trades)} (0% WR)')
print(f'  EOD Exits: {len(df) - len(tp_trades) - len(sl_trades)}')
print()

# Calculate average risk and reward
if len(tp_trades) > 0:
    avg_tp_profit = tp_trades['pnl'].mean()
    avg_tp_per_share = (tp_trades['pnl'] / tp_trades['quantity']).mean()
    print(f'✅ TAKE PROFIT TRADES:')
    print(f'  Count: {len(tp_trades)}')
    print(f'  Avg Profit: ₹{avg_tp_profit:,.2f}')
    print(f'  Avg Per Share: ₹{avg_tp_per_share:.2f}')
    print()

if len(sl_trades) > 0:
    avg_sl_loss = sl_trades['pnl'].mean()
    avg_sl_per_share = (sl_trades['pnl'] / sl_trades['quantity']).mean()
    print(f'❌ STOP LOSS TRADES:')
    print(f'  Count: {len(sl_trades)}')
    print(f'  Avg Loss: ₹{avg_sl_loss:,.2f}')
    print(f'  Avg Per Share: ₹{avg_sl_per_share:.2f}')
    print()

# Calculate actual R:R achieved
if len(tp_trades) > 0 and len(sl_trades) > 0:
    actual_rr = abs(avg_tp_profit / avg_sl_loss)
    print(f'⚖️ ACTUAL RISK-REWARD RATIO:')
    print(f'  Avg Win / Avg Loss = {actual_rr:.2f}:1')
    print(f'  Target R:R in Code: 2.0:1')
    print()

# Day-by-day analysis
print('=' * 80)
print('DAY-BY-DAY PERFORMANCE (Intraday Readiness)')
print('=' * 80)
print()

for date in sorted(df['trade_date'].unique()):
    day_trades = df[df['trade_date'] == date]
    day_pnl = day_trades['pnl'].sum()
    day_wins = len(day_trades[day_trades['pnl'] > 0])
    day_losses = len(day_trades[day_trades['pnl'] <= 0])
    day_wr = (day_wins / len(day_trades) * 100) if len(day_trades) > 0 else 0
    
    status = '✅' if day_pnl > 0 else '❌'
    
    print(f'{status} {date} ({day_trades.iloc[0]["entry_time"].strftime("%A")}):')
    print(f'   Trades: {len(day_trades)}, Wins: {day_wins}, Losses: {day_losses}, WR: {day_wr:.1f}%')
    print(f'   P&L: ₹{day_pnl:,.2f}')
    print()

# Summary stats
profitable_days = len(df.groupby('trade_date')['pnl'].sum()[df.groupby('trade_date')['pnl'].sum() > 0])
total_days = len(df['trade_date'].unique())

print('=' * 80)
print('INTRADAY READINESS METRICS:')
print('=' * 80)
print(f'Total Trading Days: {total_days}')
print(f'Profitable Days: {profitable_days}')
print(f'Losing Days: {total_days - profitable_days}')
print(f'Daily Win Rate: {(profitable_days / total_days * 100):.1f}%')
print()

# Find best and worst days
daily_pnl = df.groupby('trade_date')['pnl'].sum().sort_values(ascending=False)
print(f'🏆 Best Day: {daily_pnl.index[0]} = ₹{daily_pnl.iloc[0]:,.2f}')
print(f'💀 Worst Day: {daily_pnl.index[-1]} = ₹{daily_pnl.iloc[-1]:,.2f}')
print()

# Average daily P&L
avg_daily_pnl = daily_pnl.mean()
print(f'📊 Average Daily P&L: ₹{avg_daily_pnl:,.2f}')
print(f'📊 Median Daily P&L: ₹{daily_pnl.median():,.2f}')
