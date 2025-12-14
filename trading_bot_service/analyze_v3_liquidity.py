import pandas as pd
import numpy as np

# Load v2.5 results
df = pd.read_csv('backtest_defining_order_20251214_112010.csv')
df['entry_time'] = pd.to_datetime(df['entry_time'])
df['exit_time'] = pd.to_datetime(df['exit_time'])

# Extract hour
df['entry_hour'] = df['entry_time'].dt.hour

print('=' * 80)
print('v3.0 LIQUIDITY FILTER ANALYSIS')
print('=' * 80)
print()

# Check trades in 12:00-14:30 window (v3.0 would block)
liquidity_block_trades = df[(df['entry_hour'] >= 12) & (df['entry_hour'] < 15)]
other_trades = df[(df['entry_hour'] < 12) | (df['entry_hour'] >= 15)]

print('LIQUIDITY TROUGH WINDOW (12:00-14:30) - v3.0 WOULD BLOCK:')
print(f'  Trades: {len(liquidity_block_trades)}')
if len(liquidity_block_trades) > 0:
    wr = (liquidity_block_trades["pnl"] > 0).sum() / len(liquidity_block_trades) * 100
    print(f'  Win Rate: {wr:.1f}%')
    print(f'  Total P&L: ₹{liquidity_block_trades["pnl"].sum():,.2f}')
else:
    print('  Win Rate: N/A')
    print('  Total P&L: ₹0.00')
print()

print('OTHER WINDOWS (09:30-12:00 + 14:30-15:15) - v3.0 WOULD KEEP:')
print(f'  Trades: {len(other_trades)}')
if len(other_trades) > 0:
    wr = (other_trades["pnl"] > 0).sum() / len(other_trades) * 100
    print(f'  Win Rate: {wr:.1f}%')
    print(f'  Total P&L: ₹{other_trades["pnl"].sum():,.2f}')
else:
    print('  Win Rate: N/A')
    print('  Total P&L: ₹0.00')
print()

# Breakdown by specific hours
print('HOUR-BY-HOUR BREAKDOWN:')
for hour in sorted(df['entry_hour'].unique()):
    hour_trades = df[df['entry_hour'] == hour]
    wins = (hour_trades['pnl'] > 0).sum()
    wr = wins / len(hour_trades) * 100
    pnl = hour_trades['pnl'].sum()
    
    blocked = 'BLOCKED' if (hour >= 12 and hour < 15) else 'ALLOWED'
    print(f'  {hour:02d}:00 - Trades: {len(hour_trades):2d}, WR: {wr:5.1f}%, P&L: ₹{pnl:9,.2f} [{blocked}]')

print()
print('=' * 80)
print('CONCLUSION:')
print('=' * 80)

# Calculate impact
blocked_pnl = liquidity_block_trades['pnl'].sum()
kept_pnl = other_trades['pnl'].sum()
total_pnl = df['pnl'].sum()

print(f'v2.5 Current Performance: ₹{total_pnl:,.2f} (66 trades, 42.42% WR)')
print(f'v3.0 Simulated Performance: ₹{kept_pnl:,.2f} ({len(other_trades)} trades)')
print(f'Impact: ₹{kept_pnl - total_pnl:,.2f}')
print()

if kept_pnl > total_pnl:
    print('✅ RECOMMENDATION: v3.0 Liquidity Filter would IMPROVE results')
    improvement_pct = ((kept_pnl - total_pnl) / abs(total_pnl)) * 100
    print(f'   Expected improvement: +{improvement_pct:.1f}%')
else:
    print('❌ RECOMMENDATION: v3.0 Liquidity Filter would HURT results - STAY WITH v2.5')
    loss_pct = ((total_pnl - kept_pnl) / abs(total_pnl)) * 100
    print(f'   Expected loss: -{loss_pct:.1f}%')
