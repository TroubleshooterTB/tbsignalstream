"""
Pattern Detection Diagnostic Tool
Analyzes why patterns are not being detected frequently
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trading.patterns import PatternDetector
from historical_data_manager import HistoricalDataManager

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_pattern_detection(data: pd.DataFrame, symbol: str) -> Dict:
    """
    Detailed analysis of why patterns are/aren't detected
    """
    detector = PatternDetector()
    
    # Get basic stats
    price_range = data['High'].max() - data['Low'].min()
    avg_price = data['Close'].mean()
    volatility = (price_range / avg_price) * 100
    
    # Check for swing points (no prominence for intraday)
    from scipy.signal import find_peaks
    highs, _ = find_peaks(data['High'], distance=5)
    lows, _ = find_peaks(-data['Low'], distance=5)
    
    # Try pattern detection with current parameters
    pattern = detector.scan(data)
    
    # Analyze double top/bottom requirements
    lookback = 50
    if len(data) >= lookback:
        recent_data = data.iloc[-lookback:]
        recent_highs, _ = find_peaks(recent_data['High'], distance=5)
        recent_lows, _ = find_peaks(-recent_data['Low'], distance=5)
        
        # Check double bottom attempts
        double_bottom_candidates = []
        if len(recent_lows) >= 2:
            for i in range(len(recent_lows) - 1):
                trough1_idx, trough2_idx = recent_lows[i], recent_lows[i+1]
                trough1_price = recent_data['Low'].iloc[trough1_idx]
                trough2_price = recent_data['Low'].iloc[trough2_idx]
                
                price_diff_pct = abs(trough1_price - trough2_price) / trough1_price * 100
                
                if price_diff_pct < 3:  # Within 3% tolerance
                    peak_between = recent_data['High'].iloc[trough1_idx:trough2_idx].max()
                    current_price = data['Close'].iloc[-1]
                    height = peak_between - trough1_price
                    
                    breakout_needed = peak_between
                    distance_to_breakout = breakout_needed - current_price
                    
                    double_bottom_candidates.append({
                        'trough1_price': trough1_price,
                        'trough2_price': trough2_price,
                        'price_diff_pct': price_diff_pct,
                        'peak_between': peak_between,
                        'current_price': current_price,
                        'breakout_needed': breakout_needed,
                        'distance_to_breakout': distance_to_breakout,
                        'distance_pct': (distance_to_breakout / current_price) * 100,
                        'would_confirm': current_price > peak_between,
                        'would_form': current_price > trough1_price * 0.95
                    })
        
        # Check double top attempts
        double_top_candidates = []
        if len(recent_highs) >= 2:
            for i in range(len(recent_highs) - 1):
                peak1_idx, peak2_idx = recent_highs[i], recent_highs[i+1]
                peak1_price = recent_data['High'].iloc[peak1_idx]
                peak2_price = recent_data['High'].iloc[peak2_idx]
                
                price_diff_pct = abs(peak1_price - peak2_price) / peak1_price * 100
                
                if price_diff_pct < 3:  # Within 3% tolerance
                    trough_between = recent_data['Low'].iloc[peak1_idx:peak2_idx].min()
                    current_price = data['Close'].iloc[-1]
                    height = peak1_price - trough_between
                    
                    breakout_needed = trough_between
                    distance_to_breakout = current_price - breakout_needed
                    
                    double_top_candidates.append({
                        'peak1_price': peak1_price,
                        'peak2_price': peak2_price,
                        'price_diff_pct': price_diff_pct,
                        'trough_between': trough_between,
                        'current_price': current_price,
                        'breakout_needed': breakout_needed,
                        'distance_to_breakout': distance_to_breakout,
                        'distance_pct': (distance_to_breakout / current_price) * 100,
                        'would_confirm': current_price < trough_between,
                        'would_form': current_price < peak1_price * 1.05
                    })
    else:
        double_bottom_candidates = []
        double_top_candidates = []
        recent_highs = []
        recent_lows = []
    
    return {
        'symbol': symbol,
        'total_candles': len(data),
        'price_range': price_range,
        'avg_price': avg_price,
        'volatility_pct': volatility,
        'total_highs': len(highs),
        'total_lows': len(lows),
        'recent_highs': len(recent_highs) if len(data) >= lookback else 0,
        'recent_lows': len(recent_lows) if len(data) >= lookback else 0,
        'pattern_detected': pattern.get('pattern_name', 'None'),
        'pattern_status': pattern.get('pattern_status', 'N/A'),
        'double_bottom_candidates': double_bottom_candidates,
        'double_top_candidates': double_top_candidates
    }


def main():
    """Run diagnostic on recent market data"""
    print("=" * 80)
    print("PATTERN DETECTION DIAGNOSTIC")
    print("=" * 80)
    
    # Login
    api_key = input("\nAPI Key: ").strip()
    client_code = input("Client Code: ").strip()
    password = input("Trading Password: ").strip()
    totp = input("TOTP (6-digit code): ").strip()
    
    # Generate JWT
    import requests
    url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '127.0.0.1',
        'X-ClientPublicIP': '127.0.0.1',
        'X-MACAddress': '00:00:00:00:00:00',
        'X-PrivateKey': api_key
    }
    payload = {"clientcode": client_code, "password": password, "totp": totp}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        jwt_token = data['data']['jwtToken']
        print("✅ Logged in successfully\n")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Initialize historical data manager
    hist_manager = HistoricalDataManager(api_key=api_key, jwt_token=jwt_token)
    
    # Test symbols with their tokens
    test_symbols = [
        ('RELIANCE-EQ', '2885', 'NSE'),
        ('TCS-EQ', '11536', 'NSE'),
        ('INFY-EQ', '1594', 'NSE'),
        ('HDFCBANK-EQ', '1333', 'NSE'),
        ('ICICIBANK-EQ', '1330', 'NSE'),
    ]
    
    print("Analyzing 5 symbols for pattern detection issues...\n")
    
    results = []
    for symbol, token, exchange in test_symbols:
        print(f"📊 Analyzing {symbol}...")
        
        # Fetch last 3 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        df = hist_manager.fetch_historical_data(
            symbol=symbol,
            token=token,
            exchange=exchange,
            from_date=start_date,
            to_date=end_date,
            interval='ONE_MINUTE'
        )
        
        if df is not None and len(df) > 0:
            analysis = analyze_pattern_detection(df, symbol)
            results.append(analysis)
            
            print(f"  Candles: {analysis['total_candles']}")
            print(f"  Volatility: {analysis['volatility_pct']:.2f}%")
            print(f"  Swing Highs (last 50): {analysis['recent_highs']}")
            print(f"  Swing Lows (last 50): {analysis['recent_lows']}")
            print(f"  Pattern Detected: {analysis['pattern_detected']}")
            
            if analysis['double_bottom_candidates']:
                print(f"  💡 Double Bottom Candidates: {len(analysis['double_bottom_candidates'])}")
                for idx, cand in enumerate(analysis['double_bottom_candidates'][:3], 1):
                    print(f"     #{idx}: Troughs at ₹{cand['trough1_price']:.2f} & ₹{cand['trough2_price']:.2f} ({cand['price_diff_pct']:.2f}% diff)")
                    print(f"         Current: ₹{cand['current_price']:.2f} | Breakout needed: ₹{cand['breakout_needed']:.2f} ({cand['distance_pct']:.2f}% away)")
                    print(f"         Would confirm: {cand['would_confirm']} | Would form: {cand['would_form']}")
            
            if analysis['double_top_candidates']:
                print(f"  💡 Double Top Candidates: {len(analysis['double_top_candidates'])}")
                for idx, cand in enumerate(analysis['double_top_candidates'][:3], 1):
                    print(f"     #{idx}: Peaks at ₹{cand['peak1_price']:.2f} & ₹{cand['peak2_price']:.2f} ({cand['price_diff_pct']:.2f}% diff)")
                    print(f"         Current: ₹{cand['current_price']:.2f} | Breakout needed: ₹{cand['breakout_needed']:.2f} ({cand['distance_pct']:.2f}% away)")
                    print(f"         Would confirm: {cand['would_confirm']} | Would form: {cand['would_form']}")
            
            print()
        else:
            print(f"  ❌ No data fetched\n")
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_candidates = sum(len(r['double_bottom_candidates']) + len(r['double_top_candidates']) for r in results)
    total_detected = sum(1 for r in results if r['pattern_detected'] != 'None')
    avg_volatility = sum(r['volatility_pct'] for r in results) / len(results) if results else 0
    
    print(f"Total symbols analyzed: {len(results)}")
    print(f"Average volatility: {avg_volatility:.2f}%")
    print(f"Patterns detected: {total_detected}")
    print(f"Pattern candidates found: {total_candidates}")
    print(f"Detection rate: {(total_detected/total_candidates*100) if total_candidates > 0 else 0:.1f}%")
    
    if total_candidates > 0 and total_detected == 0:
        print("\n⚠️  ISSUE IDENTIFIED:")
        print("   Pattern candidates exist but none are being detected!")
        print("   Most candidates are likely in 'forming' state and waiting for breakout.")
        print("   Consider:")
        print("   1. Adding 'forming' patterns to Activity Feed (as watchlist items)")
        print("   2. Further relaxing breakout criteria")
        print("   3. Adding more pattern types (Head & Shoulders, Channels, etc.)")


if __name__ == "__main__":
    main()
