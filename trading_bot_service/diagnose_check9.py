"""
Diagnostic script to see what Check #9 scores patterns are actually getting
"""
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from trading.patterns import PatternDetector
from trading.checkers.pattern_checker import PatternChecker
from historical_data_manager import HistoricalDataManager

def diagnose_pattern_scores():
    """Run pattern detection and show Check #9 scores"""
    
    # Initialize
    hist_manager = HistoricalDataManager()
    pattern_detector = PatternDetector()
    pattern_checker = PatternChecker()
    
    # Test symbols
    symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICI']
    
    print("=" * 80)
    print("CHECK #9 PATTERN QUALITY DIAGNOSTIC")
    print("=" * 80)
    
    for symbol in symbols:
        print(f"\n📊 Analyzing {symbol}...")
        
        # Get 5-minute data for Nov 5-13
        df = hist_manager.fetch_historical_data(
            symbol=symbol,
            interval='5minute',
            start_date='2025-11-05',
            end_date='2025-11-13'
        )
        
        if df is None or len(df) < 50:
            print(f"  ❌ Insufficient data")
            continue
        
        # Detect pattern
        pattern_details = pattern_detector.scan(df)
        
        if not pattern_details:
            print(f"  ℹ️  No pattern detected")
            continue
        
        pattern_name = pattern_details.get('pattern_name', 'Unknown')
        print(f"  ✅ Pattern: {pattern_name}")
        
        # Calculate Check #9 score breakdown
        current_price = df['Close'].iloc[-1]
        breakout_price = pattern_details.get('breakout_price', 0)
        breakout_direction = pattern_details.get('breakout_direction', 'up')
        duration = pattern_details.get('duration', 0)
        target = pattern_details.get('calculated_price_target', 0)
        stop_loss = pattern_details.get('initial_stop_loss', 0)
        pattern_top = pattern_details.get('pattern_top_boundary', 0)
        pattern_bottom = pattern_details.get('pattern_bottom_boundary', 0)
        
        print(f"\n  📋 Pattern Data:")
        print(f"     Duration: {duration} candles")
        print(f"     Current Price: ₹{current_price:.2f}")
        print(f"     Breakout Price: ₹{breakout_price:.2f}")
        print(f"     Direction: {breakout_direction}")
        print(f"     Target: ₹{target:.2f}")
        print(f"     Stop Loss: ₹{stop_loss:.2f}")
        print(f"     Pattern Range: ₹{pattern_bottom:.2f} - ₹{pattern_top:.2f}")
        
        # Score breakdown
        quality_score = 0.0
        
        # 1. Duration Score (30 points)
        duration_score = 0
        if duration >= 30:
            duration_score = 30
        elif duration >= 20:
            duration_score = 20
        elif duration >= 15:
            duration_score = 10
        quality_score += duration_score
        print(f"\n  🎯 Score Breakdown:")
        print(f"     Duration ({duration} candles): {duration_score}/30")
        
        # 2. Breakout Strength (25 points)
        breakout_score = 0
        if breakout_price > 0:
            breakout_distance_pct = abs((current_price - breakout_price) / breakout_price) * 100
            
            if breakout_direction == 'up' and current_price > breakout_price:
                if breakout_distance_pct >= 1.0:
                    breakout_score = 25
                elif breakout_distance_pct >= 0.5:
                    breakout_score = 15
                elif breakout_distance_pct >= 0.2:
                    breakout_score = 10
            elif breakout_direction == 'down' and current_price < breakout_price:
                if breakout_distance_pct >= 1.0:
                    breakout_score = 25
                elif breakout_distance_pct >= 0.5:
                    breakout_score = 15
                elif breakout_distance_pct >= 0.2:
                    breakout_score = 10
            
            quality_score += breakout_score
            print(f"     Breakout Strength ({breakout_distance_pct:.2f}%): {breakout_score}/25")
        
        # 3. Risk-Reward Quality (25 points)
        rr_score = 0
        if target > 0 and stop_loss > 0 and current_price > 0:
            if breakout_direction == 'up':
                potential_reward = target - current_price
                potential_risk = current_price - stop_loss
            else:
                potential_reward = current_price - target
                potential_risk = stop_loss - current_price
            
            if potential_risk > 0:
                rr_ratio = potential_reward / potential_risk
                if rr_ratio >= 3.0:
                    rr_score = 25
                elif rr_ratio >= 2.0:
                    rr_score = 20
                elif rr_ratio >= 1.5:
                    rr_score = 15
                elif rr_ratio >= 1.0:
                    rr_score = 10
                
                quality_score += rr_score
                print(f"     Risk-Reward (1:{rr_ratio:.2f}): {rr_score}/25")
        
        # 4. Pattern Clarity (20 points)
        clarity_score = 0
        if pattern_top > 0 and pattern_bottom > 0:
            pattern_range_pct = ((pattern_top - pattern_bottom) / pattern_bottom) * 100
            
            if 2.0 <= pattern_range_pct <= 15.0:
                clarity_score = 20
            elif 1.0 <= pattern_range_pct <= 20.0:
                clarity_score = 10
            
            quality_score += clarity_score
            print(f"     Pattern Clarity ({pattern_range_pct:.2f}% range): {clarity_score}/20")
        
        print(f"\n  📊 TOTAL SCORE: {quality_score}/100")
        print(f"  {'✅ PASS' if quality_score >= 70 else '❌ FAIL'} (Threshold: 70)")
        print(f"  {'-' * 76}")

if __name__ == '__main__':
    diagnose_pattern_scores()
