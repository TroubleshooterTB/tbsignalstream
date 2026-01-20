"""
Alpha-Ensemble Strategy Backtest Runner
Tests the new retest-based strategy across multiple timeframes
"""

import sys
from datetime import datetime, timedelta
from alpha_ensemble_strategy import AlphaEnsembleStrategy
from nifty200_watchlist import NIFTY200_WATCHLIST
import pandas as pd
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_jwt_token(client_code: str, password: str, totp: str, api_key: str) -> str:
    """Generate JWT token for Angel One API"""
    import requests
    
    url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-PrivateKey': api_key
    }
    
    payload = {
        "clientcode": client_code,
        "password": password,
        "totp": totp
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') and data.get('data'):
            return data['data']['jwtToken']
    
    raise Exception(f"Authentication failed: {response.text}")


def run_alpha_ensemble_backtest():
    """Run Alpha-Ensemble strategy backtest"""
    
    print("\n" + "=" * 80)
    print("ALPHA-ENSEMBLE STRATEGY BACKTEST")
    print("=" * 80)
    print("\nEnter your Angel One credentials:")
    
    client_code = input("Client Code: ").strip()
    password = input("Password/MPIN: ").strip()
    totp = input("TOTP Code: ").strip()
    api_key = input("API Key: ").strip()
    
    print("\n🔐 Authenticating...")
    
    try:
        jwt_token = generate_jwt_token(client_code, password, totp, api_key)
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Use NIFTY 200 WATCHLIST from imported module
    test_symbols = NIFTY200_WATCHLIST
    
    print(f"🎯 Testing with {len(test_symbols)} Nifty 200 symbols")
    print(f"   Expected scan time per cycle: ~90 seconds")
    print(f"   15-minute interval buffer: 14+ minutes ✅\n")
    
    # Create strategy instance
    strategy = AlphaEnsembleStrategy(api_key, jwt_token)
    
    # Test periods
    today = datetime.now()
    
    test_periods = [
        {
            'name': '1 MONTH',
            'start': (today - timedelta(days=30)).strftime("%Y-%m-%d"),
            'end': today.strftime("%Y-%m-%d")
        },
        {
            'name': '3 MONTHS',
            'start': (today - timedelta(days=90)).strftime("%Y-%m-%d"),
            'end': today.strftime("%Y-%m-%d")
        },
        {
            'name': '6 MONTHS',
            'start': (today - timedelta(days=180)).strftime("%Y-%m-%d"),
            'end': today.strftime("%Y-%m-%d")
        },
        {
            'name': '1 YEAR',
            'start': (today - timedelta(days=365)).strftime("%Y-%m-%d"),
            'end': today.strftime("%Y-%m-%d")
        },
    ]
    
    all_results = []
    
    print("\n" + "=" * 80)
    print("RUNNING MULTI-TIMEFRAME BACKTEST WITH 200 NIFTY SYMBOLS")
    print("=" * 80)
    print("\n⚠️ Processing in batches of 25 symbols to avoid JWT expiry...")
    print("⚠️ This will take ~40-50 minutes total for all timeframes.\n")
    
    # Split symbols into batches to avoid JWT token expiry
    BATCH_SIZE = 25  # Increased from 15 since we have more symbols
    symbol_batches = [test_symbols[i:i + BATCH_SIZE] for i in range(0, len(test_symbols), BATCH_SIZE)]
    
    for period in test_periods:
        print(f"\n{'=' * 80}")
        print(f"TESTING: {period['name']} ({period['start']} to {period['end']})")
        print(f"{'=' * 80}\n")
        
        all_trades = []
        total_capital = 100000  # Track capital across batches
        
        for batch_idx, symbol_batch in enumerate(symbol_batches):
            print(f"\n📦 Batch {batch_idx + 1}/{len(symbol_batches)}: Processing {len(symbol_batch)} symbols...")
            
            # Re-authenticate for each batch to get fresh JWT token
            if batch_idx > 0:
                print("🔄 Refreshing JWT token...")
                try:
                    totp = input("Enter new TOTP code: ").strip()
                    jwt_token = generate_jwt_token(client_code, password, totp, api_key)
                    strategy.jwt_token = jwt_token  # Update strategy with fresh token
                    print("✅ Token refreshed!\n")
                except Exception as e:
                    print(f"❌ Failed to refresh token: {e}")
                    print("⚠️ Continuing with old token (may fail)...\n")
            
            # Run backtest for this batch
            batch_results = strategy.run_backtest(
                symbols=symbol_batch,
                start_date=period['start'],
                end_date=period['end'],
                initial_capital=total_capital
            )
            
            # Merge trades and update capital
            all_trades.extend(batch_results['trades'])
            total_capital = batch_results['capital']
            
            print(f"✅ Batch {batch_idx + 1} complete: {len(batch_results['trades'])} trades, Capital: ₹{total_capital:,.2f}")
        
        # Calculate aggregate metrics for the period
        winning_trades = [t for t in all_trades if t['pnl'] > 0]
        losing_trades = [t for t in all_trades if t['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / len(all_trades) * 100) if all_trades else 0
        
        total_profit = sum(t['pnl'] for t in winning_trades)
        total_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        all_results.append({
            'period': period['name'],
            'trades': len(all_trades),
            'win_rate': win_rate,
            'final_capital': total_capital,
            'return_pct': ((total_capital - 100000) / 100000) * 100,
            'profit_factor': profit_factor
        })
    
    # Print comparison table
    print("\n\n" + "=" * 80)
    print("ALPHA-ENSEMBLE MULTI-TIMEFRAME RESULTS")
    print("=" * 80)
    print(f"\n{'Period':<12} {'Trades':<8} {'Win%':<8} {'Return%':<10} {'P&L':<15} {'PF':<6}")
    print("-" * 80)
    
    for result in all_results:
        pnl = result['final_capital'] - 100000
        print(f"{result['period']:<12} {result['trades']:<8} {result['win_rate']:<7.1f}% "
              f"{result['return_pct']:<9.2f}% ₹{pnl:>12,.2f}  {result['profit_factor']:<6.2f}")
    
    print("=" * 80)
    
    # Compare with v3.2
    print("\n\n" + "=" * 80)
    print("COMPARISON: ALPHA-ENSEMBLE vs v3.2")
    print("=" * 80)
    print("\nv3.2 (Original):")
    print("  1 Year: 63 trades, 33.33% WR, -45.25% return, -₹45,252")
    print("\nv3.3 (Relaxed):")
    print("  1 Year: 204 trades, 26.47% WR, -96.62% return, -₹96,621")
    
    year_result = [r for r in all_results if r['period'] == '1 YEAR'][0]
    print(f"\nAlpha-Ensemble:")
    print(f"  1 Year: {year_result['trades']} trades, {year_result['win_rate']:.2f}% WR, "
          f"{year_result['return_pct']:.2f}% return, ₹{year_result['final_capital'] - 100000:,.2f}")
    
    if year_result['return_pct'] > -45.25:
        improvement = year_result['return_pct'] - (-45.25)
        print(f"\n✅ IMPROVEMENT: +{improvement:.2f}% better than v3.2!")
    else:
        decline = (-45.25) - year_result['return_pct']
        print(f"\n❌ DECLINE: -{decline:.2f}% worse than v3.2")
    
    print("\n" + "=" * 80)
    print("KEY METRICS TO VALIDATE:")
    print("=" * 80)
    print(f"✅ Win Rate > 40%? {year_result['win_rate']:.2f}% {'✅ YES' if year_result['win_rate'] > 40 else '❌ NO'}")
    print(f"✅ Profit Factor > 1.0? {year_result['profit_factor']:.2f} {'✅ YES' if year_result['profit_factor'] > 1.0 else '❌ NO'}")
    print(f"✅ Positive Return? {year_result['return_pct']:.2f}% {'✅ YES' if year_result['return_pct'] > 0 else '❌ NO'}")
    print("=" * 80)
    
    # ===== SAVE RESULTS TO FILE =====
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"backtest_results_{timestamp}.json"
    
    save_data = {
        'timestamp': timestamp,
        'total_symbols': len(test_symbols),
        'batches_completed': len(symbol_batches),
        'results': all_results,
        'all_trades': all_trades,
        'summary': {
            'one_year': {
                'trades': year_result['trades'],
                'win_rate': year_result['win_rate'],
                'return_pct': year_result['return_pct'],
                'profit_factor': year_result['profit_factor'],
                'final_capital': year_result['final_capital']
            }
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(save_data, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("=" * 80)


if __name__ == "__main__":
    run_alpha_ensemble_backtest()
