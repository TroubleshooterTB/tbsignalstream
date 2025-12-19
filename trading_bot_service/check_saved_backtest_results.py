"""
Check Saved Backtest Results from Firestore
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase
try:
    firebase_admin.get_app()
except ValueError:
    # Initialize without credentials (uses Application Default Credentials in Cloud environment)
    firebase_admin.initialize_app()

db = firestore.client()

print("="*80)
print("📊 CHECKING SAVED BACKTEST RESULTS")
print("="*80)
print()

# Get all backtest results
results = db.collection('backtest_results').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()

results_list = []
for doc in results:
    data = doc.to_dict()
    results_list.append(data)
    
    print(f"ID: {doc.id}")
    print(f"Strategy: {data.get('strategy', 'N/A')}")
    print(f"Date Range: {data.get('start_date', 'N/A')} to {data.get('end_date', 'N/A')}")
    print(f"Capital: ₹{data.get('capital', 0):,}")
    
    summary = data.get('summary', {})
    if summary:
        print(f"\n📈 RESULTS:")
        print(f"   Total Trades: {summary.get('total_trades', 0)}")
        print(f"   Win Rate: {summary.get('win_rate', 0):.2f}%")
        print(f"   Profit Factor: {summary.get('profit_factor', 0):.2f}")
        print(f"   Total P&L: ₹{summary.get('total_pnl', 0):,.0f}")
        
        if 'pnl_percentage' in summary:
            print(f"   Returns: {summary.get('pnl_percentage', 0):.2f}%")
        
        print(f"   Winning Trades: {summary.get('winning_trades', 0)}")
        print(f"   Losing Trades: {summary.get('losing_trades', 0)}")
        print(f"   Avg Win: ₹{summary.get('avg_win', 0):,.0f}")
        print(f"   Avg Loss: ₹{summary.get('avg_loss', 0):,.0f}")
        print(f"   Max Win: ₹{summary.get('max_win', 0):,.0f}")
        print(f"   Max Loss: ₹{summary.get('max_loss', 0):,.0f}")
    
    trades = data.get('trades', [])
    print(f"\n📋 Trade Details: {len(trades)} trades")
    
    timestamp = data.get('timestamp')
    created_at = data.get('created_at')
    print(f"Saved: {created_at or timestamp}")
    
    print("\n" + "-"*80 + "\n")

if not results_list:
    print("❌ No backtest results found in Firestore")
    print("   Make sure you clicked 'Save Results' button after running backtest")
else:
    print(f"\n✅ Found {len(results_list)} saved backtest result(s)")
    
    # Analyze latest result
    if results_list:
        latest = results_list[0]
        summary = latest.get('summary', {})
        
        print("\n" + "="*80)
        print("🔍 ANALYSIS OF LATEST RESULT")
        print("="*80)
        
        wr = summary.get('win_rate', 0)
        pf = summary.get('profit_factor', 0)
        pnl_pct = summary.get('pnl_percentage', 0)
        
        print(f"\nWin Rate: {wr:.2f}%")
        if wr < 40:
            print("   ❌ VERY LOW - Strategy is losing most trades")
            print("   → Need MUCH stricter filters")
        elif wr < 50:
            print("   ⚠️  LOW - Strategy needs improvement")
            print("   → Need stricter filters")
        elif wr < 60:
            print("   ✅ DECENT - Room for improvement")
        else:
            print("   ✅ GOOD - Winning most trades")
        
        print(f"\nProfit Factor: {pf:.2f}")
        if pf < 1.0:
            print("   ❌ LOSING MONEY - Strategy is not profitable")
            print("   → Average loss > Average win")
        elif pf < 1.5:
            print("   ⚠️  BARELY PROFITABLE - High risk")
        elif pf < 2.0:
            print("   ✅ ACCEPTABLE")
        else:
            print("   ✅ EXCELLENT")
        
        if pnl_pct != 0:
            print(f"\nReturns: {pnl_pct:.2f}%")
            if pnl_pct < 0:
                print("   ❌ NEGATIVE RETURNS - Losing capital")
            elif pnl_pct < 20:
                print("   ⚠️  LOW RETURNS")
            else:
                print("   ✅ GOOD RETURNS")
        
        print("\n" + "="*80)
        print("💡 RECOMMENDATION")
        print("="*80)
        
        if wr < 50 and pf < 1.5:
            print("❌ Current strategy is NOT WORKING")
            print("\n🚀 NEXT STEP: Run Aggressive Baseline with these parameters:")
            print("   • ADX > 25 (vs current 20)")
            print("   • RSI 35/65 (vs 30/70)")
            print("   • Volume 2.0x (vs 1.5x)")
            print("   • R:R 3.0 (vs 2.5)")
            print("   • 3 timeframes must align")
            print("   • Trading hours: 10:00-14:30")
            print("\nExpected: 50-60% WR, 2.0+ PF, positive returns")
        else:
            print("✅ Strategy shows promise - Continue with 12-batch optimization")

print("\n" + "="*80)
