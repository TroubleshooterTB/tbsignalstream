"""
v2.5 SINGLE-DAY TESTING FRAMEWORK
==================================
Test bot readiness day-by-day for intraday deployment validation

USAGE:
    python test_single_day.py 2025-12-08  # Test specific day
    python test_single_day.py             # Test latest day
"""

import pandas as pd
import sys
from datetime import datetime, timedelta

def load_backtest_results():
    """Load existing v2.5 backtest results"""
    df = pd.read_csv('backtest_defining_order_20251214_112010.csv')
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df['trade_date'] = df['entry_time'].dt.date
    return df

def analyze_single_day(df, target_date):
    """Analyze performance for a single trading day"""
    # Filter to target date
    day_trades = df[df['trade_date'] == target_date]
    
    if len(day_trades) == 0:
        print(f"\n❌ No trades found for {target_date}")
        print("\nAvailable dates:")
        for date in sorted(df['trade_date'].unique()):
            print(f"  - {date} ({df[df['trade_date'] == date].iloc[0]['entry_time'].strftime('%A')})")
        return None
    
    print('=' * 80)
    print(f'SINGLE DAY ANALYSIS: {target_date} ({day_trades.iloc[0]["entry_time"].strftime("%A")})')
    print('=' * 80)
    print()
    
    # Overall stats
    total_trades = len(day_trades)
    wins = len(day_trades[day_trades['pnl'] > 0])
    losses = len(day_trades[day_trades['pnl'] <= 0])
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    total_pnl = day_trades['pnl'].sum()
    
    print(f'📊 DAILY SUMMARY:')
    print(f'  Total Trades: {total_trades}')
    print(f'  Wins: {wins}')
    print(f'  Losses: {losses}')
    print(f'  Win Rate: {win_rate:.1f}%')
    print(f'  Total P&L: ₹{total_pnl:,.2f}')
    print(f'  Avg P&L per Trade: ₹{total_pnl/total_trades:,.2f}')
    print()
    
    # Exit breakdown
    tp_count = len(day_trades[day_trades['exit_reason'] == 'Take Profit'])
    sl_count = len(day_trades[day_trades['exit_reason'] == 'Stop Loss'])
    eod_count = len(day_trades[day_trades['exit_reason'] == 'End of Day'])
    
    print(f'🎯 EXIT BREAKDOWN:')
    print(f'  Take Profit: {tp_count} trades')
    print(f'  Stop Loss: {sl_count} trades')
    print(f'  End of Day: {eod_count} trades')
    print()
    
    # Direction breakdown
    long_trades = day_trades[day_trades['direction'] == 'LONG']
    short_trades = day_trades[day_trades['direction'] == 'SHORT']
    
    print(f'📈 DIRECTION BREAKDOWN:')
    if len(long_trades) > 0:
        long_wr = (len(long_trades[long_trades['pnl'] > 0]) / len(long_trades) * 100)
        long_pnl = long_trades['pnl'].sum()
        print(f'  LONG: {len(long_trades)} trades, {long_wr:.1f}% WR, ₹{long_pnl:,.2f} P&L')
    else:
        print(f'  LONG: 0 trades')
    
    if len(short_trades) > 0:
        short_wr = (len(short_trades[short_trades['pnl'] > 0]) / len(short_trades) * 100)
        short_pnl = short_trades['pnl'].sum()
        print(f'  SHORT: {len(short_trades)} trades, {short_wr:.1f}% WR, ₹{short_pnl:,.2f} P&L')
    else:
        print(f'  SHORT: 0 trades')
    print()
    
    # Hour-by-hour breakdown
    print(f'🕐 HOUR-BY-HOUR:')
    for hour in sorted(day_trades['entry_time'].dt.hour.unique()):
        hour_trades = day_trades[day_trades['entry_time'].dt.hour == hour]
        hour_wins = len(hour_trades[hour_trades['pnl'] > 0])
        hour_wr = (hour_wins / len(hour_trades) * 100) if len(hour_trades) > 0 else 0
        hour_pnl = hour_trades['pnl'].sum()
        
        print(f'  {hour:02d}:00 - {len(hour_trades)} trades, {hour_wr:.1f}% WR, ₹{hour_pnl:,.2f} P&L')
    print()
    
    # Symbol breakdown
    print(f'🏢 TOP SYMBOLS:')
    symbol_stats = day_trades.groupby('symbol').agg({
        'pnl': ['sum', 'count'],
    }).round(2)
    symbol_stats.columns = ['total_pnl', 'trades']
    symbol_stats = symbol_stats.sort_values('total_pnl', ascending=False)
    
    for symbol in symbol_stats.head(5).index:
        trades = int(symbol_stats.loc[symbol, 'trades'])
        pnl = symbol_stats.loc[symbol, 'total_pnl']
        symbol_trades = day_trades[day_trades['symbol'] == symbol]
        symbol_wr = (len(symbol_trades[symbol_trades['pnl'] > 0]) / trades * 100)
        print(f'  {symbol}: {trades} trades, {symbol_wr:.0f}% WR, ₹{pnl:,.2f}')
    print()
    
    # Trade-by-trade details
    print('=' * 80)
    print('TRADE-BY-TRADE LOG:')
    print('=' * 80)
    
    for idx, trade in day_trades.iterrows():
        entry_time = trade['entry_time'].strftime('%H:%M')
        exit_time = trade['exit_time'].strftime('%H:%M')
        duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 60
        
        status = '✅' if trade['pnl'] > 0 else '❌'
        
        print(f"{status} {entry_time}-{exit_time} ({int(duration)}min) {trade['symbol']} {trade['direction']}")
        print(f"   Entry: ₹{trade['entry_price']:.2f} → Exit: ₹{trade['exit_price']:.2f} ({trade['exit_reason']})")
        print(f"   P&L: ₹{trade['pnl']:,.2f}")
        print()
    
    # Readiness assessment
    print('=' * 80)
    print('INTRADAY READINESS ASSESSMENT:')
    print('=' * 80)
    
    readiness_score = 0
    max_score = 5
    
    # Criteria 1: Positive P&L
    if total_pnl > 0:
        print('✅ Daily P&L: POSITIVE')
        readiness_score += 1
    else:
        print('❌ Daily P&L: NEGATIVE')
    
    # Criteria 2: Win Rate > 40%
    if win_rate >= 40:
        print('✅ Win Rate: ACCEPTABLE (≥40%)')
        readiness_score += 1
    else:
        print(f'⚠️ Win Rate: BELOW TARGET ({win_rate:.1f}% < 40%)')
    
    # Criteria 3: More TP than SL
    if tp_count > sl_count:
        print('✅ Exit Quality: More TPs than SLs')
        readiness_score += 1
    else:
        print('⚠️ Exit Quality: More SLs than TPs')
    
    # Criteria 4: At least 3 trades
    if total_trades >= 3:
        print('✅ Trade Volume: Sufficient activity')
        readiness_score += 1
    else:
        print('⚠️ Trade Volume: Low activity')
    
    # Criteria 5: Average trade profitable
    avg_trade_pnl = total_pnl / total_trades
    if avg_trade_pnl > 0:
        print(f'✅ Avg Trade: PROFITABLE (₹{avg_trade_pnl:,.2f})')
        readiness_score += 1
    else:
        print(f'❌ Avg Trade: LOSING (₹{avg_trade_pnl:,.2f})')
    
    print()
    print(f'READINESS SCORE: {readiness_score}/{max_score}')
    
    if readiness_score >= 4:
        print('🟢 VERDICT: READY FOR LIVE TRADING')
    elif readiness_score >= 3:
        print('🟡 VERDICT: CAUTIOUSLY READY (Monitor closely)')
    else:
        print('🔴 VERDICT: NOT READY (Needs improvement)')
    
    print()
    
    return {
        'date': target_date,
        'trades': total_trades,
        'win_rate': win_rate,
        'pnl': total_pnl,
        'readiness_score': readiness_score
    }

def compare_all_days(df):
    """Compare all trading days"""
    print('=' * 80)
    print('ALL DAYS COMPARISON:')
    print('=' * 80)
    print()
    
    daily_stats = []
    for date in sorted(df['trade_date'].unique()):
        day_trades = df[df['trade_date'] == date]
        total_pnl = day_trades['pnl'].sum()
        total_trades = len(day_trades)
        wins = len(day_trades[day_trades['pnl'] > 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        daily_stats.append({
            'date': date,
            'day': day_trades.iloc[0]['entry_time'].strftime('%A'),
            'trades': total_trades,
            'win_rate': win_rate,
            'pnl': total_pnl
        })
    
    df_daily = pd.DataFrame(daily_stats)
    
    for _, row in df_daily.iterrows():
        status = '✅' if row['pnl'] > 0 else '❌'
        print(f"{status} {row['date']} ({row['day']:<9}): {row['trades']:2d} trades, {row['win_rate']:5.1f}% WR, ₹{row['pnl']:9,.2f}")
    
    print()
    print(f"Profitable Days: {len(df_daily[df_daily['pnl'] > 0])}/{len(df_daily)}")
    print(f"Average Daily P&L: ₹{df_daily['pnl'].mean():,.2f}")
    print(f"Best Day: {df_daily.loc[df_daily['pnl'].idxmax(), 'date']} (₹{df_daily['pnl'].max():,.2f})")
    print(f"Worst Day: {df_daily.loc[df_daily['pnl'].idxmin(), 'date']} (₹{df_daily['pnl'].min():,.2f})")
    print()

if __name__ == "__main__":
    # Load data
    df = load_backtest_results()
    
    # Check if date provided
    if len(sys.argv) > 1:
        target_date_str = sys.argv[1]
        try:
            target_date = pd.to_datetime(target_date_str).date()
            analyze_single_day(df, target_date)
        except:
            print(f"Invalid date format: {target_date_str}")
            print("Use format: YYYY-MM-DD (e.g., 2025-12-08)")
    else:
        # Show comparison of all days
        compare_all_days(df)
        print()
        print("To analyze a specific day, run:")
        print("  python test_single_day.py YYYY-MM-DD")
        print()
        print("Example:")
        print("  python test_single_day.py 2025-12-08")
