"""
Test Mean Reversion Strategy on December 18, 2025 Data
========================================================

This script backtests the new Mean Reversion strategy on today's data
to see if it would have performed better than the failed breakout strategies.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import requests
from strategy_mean_reversion_v1 import MeanReversionStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API Configuration
API_KEY = "jgosiGzs"
CLIENT_CODE = "AABL713311"
PASSWORD = "Sarvesh@7218"
TOTP_SECRET = "OVVDE6DFNRPXMQT3FD5CDZJNCE"

def get_jwt_token(api_key: str, client_code: str, password: str, totp_code: str) -> str:
    """Generate JWT token for Angel One API"""
    
    url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"
    
    payload = {
        "clientcode": client_code,
        "password": password,
        "totp": totp_code
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "192.168.1.1",
        "X-ClientPublicIP": "106.51.74.202",
        "X-MACAddress": "fe80::1",
        "X-PrivateKey": api_key
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') and data.get('data'):
            jwt_token = data['data']['jwtToken']
            logging.info("✅ JWT token generated successfully")
            return jwt_token
        else:
            logging.error(f"❌ Login failed: {data.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        logging.error(f"❌ Error generating JWT token: {e}")
        return None

def test_with_simulated_data():
    """Test Mean Reversion with simulated Dec 18 data (DEMO)"""
    
    logging.info("\n" + "="*80)
    logging.info("DEMO MODE: Testing with simulated December 18, 2025 data")
    logging.info("="*80 + "\n")
    
    # Create simulated data for RELIANCE based on typical patterns
    # Simulating a choppy/ranging day (good for mean reversion)
    dates = pd.date_range(start='2025-12-18 09:15', end='2025-12-18 15:30', freq='5T')
    
    # Simulate price action: Starting at 1540, ranging between 1535-1545
    np.random.seed(42)  # For reproducibility
    
    price_base = 1540
    prices = []
    volumes = []
    
    for i in range(len(dates)):
        # Create mean-reverting price action
        hour = dates[i].hour
        minute = dates[i].minute
        
        # Morning volatility
        if hour == 9:
            offset = np.random.uniform(-5, 5)
        # Mid-day ranging
        elif 11 <= hour <= 14:
            offset = np.random.uniform(-3, 3)
        # Afternoon volatility
        else:
            offset = np.random.uniform(-4, 4)
        
        # Add mean reversion tendency
        if prices:
            prev_price = prices[-1][3]  # Previous close
            mean_price = price_base
            reversion = (mean_price - prev_price) * 0.3  # 30% pull to mean
            offset += reversion
        
        open_price = price_base + offset + np.random.uniform(-1, 1)
        high_price = open_price + abs(np.random.uniform(0, 3))
        low_price = open_price - abs(np.random.uniform(0, 3))
        close_price = np.random.uniform(low_price, high_price)
        
        # Volume: Higher at open/close, lower during lunch
        if hour == 9 or hour == 15:
            volume = np.random.randint(80000, 150000)
        elif 12 <= hour <= 14:
            volume = np.random.randint(20000, 50000)
        else:
            volume = np.random.randint(40000, 80000)
        
        prices.append([open_price, high_price, low_price, close_price])
        volumes.append(volume)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'open': [p[0] for p in prices],
        'high': [p[1] for p in prices],
        'low': [p[2] for p in prices],
        'close': [p[3] for p in prices],
        'volume': volumes
    })
    
    logging.info(f"📊 Simulated data: {len(df)} candles")
    logging.info(f"📊 Price range: ₹{df['low'].min():.2f} - ₹{df['high'].max():.2f}")
    logging.info(f"📊 Avg volume: {df['volume'].mean():.0f}")
    
    # Initialize strategy (dummy tokens)
    strategy = MeanReversionStrategy("dummy_key", "dummy_token")
    
    # Run backtest
    results = strategy.run_backtest('RELIANCE-EQ (SIMULATED)', df, initial_capital=100000)
    
    # Display results
    logging.info(f"\n{'='*80}")
    logging.info(f"SIMULATED RESULTS - MEAN REVERSION on Dec 18, 2025")
    logging.info(f"{'='*80}")
    
    if results['total_trades'] > 0:
        logging.info(f"Total Trades:     {results['total_trades']}")
        logging.info(f"Winning Trades:   {results['winning_trades']}")
        logging.info(f"Losing Trades:    {results['losing_trades']}")
        logging.info(f"Win Rate:         {results['win_rate']:.2f}%")
        logging.info(f"Total P&L:        ₹{results['total_pnl']:.2f}")
        logging.info(f"Return:           {results['return_pct']:.2f}%")
        logging.info(f"Avg Win:          ₹{results['avg_win']:.2f}")
        logging.info(f"Avg Loss:         ₹{results['avg_loss']:.2f}")
        logging.info(f"{'='*80}")
        
        logging.info("\n📝 INTERPRETATION (Simulated Data):")
        if results['win_rate'] > 50 and results['total_pnl'] > 0:
            logging.info("✅ Mean Reversion shows strong potential!")
            logging.info("   - Win rate > 50% (better than breakout's 26-29%)")
            logging.info("   - Positive P&L on ranging day")
            logging.info("   - Strategy logic appears sound")
            logging.info("\n💡 RECOMMENDATION:")
            logging.info("   1. Test with REAL data tomorrow (Dec 19)")
            logging.info("   2. Paper trade for 1 week minimum")
            logging.info("   3. Target: 55%+ win rate, 1.5+ profit factor")
        else:
            logging.info("⚠️ Mixed results even on simulated ranging day")
            logging.info("   - May need parameter tuning")
            logging.info("   - Test other strategies in parallel")
    else:
        logging.info("⚠️ No trades taken (filters too strict)")
        logging.info("   - Need to loosen RSI or BB thresholds")
        logging.info("   - Or reduce volume requirements")
    
    logging.info("\n" + "="*80)
    logging.info("NOTE: This was SIMULATED data for demo purposes")
    logging.info("Run with real TOTP tomorrow to get actual market results")
    logging.info("="*80)

def get_symbol_token(symbol: str, jwt_token: str, api_key: str) -> str:
    """Get symbol token for a given symbol"""
    
    # Hardcoded tokens for common symbols
    symbol_tokens = {
        'RELIANCE-EQ': '2885',
        'HDFCBANK-EQ': '1333',
        'INFY-EQ': '1594',
        'ICICIBANK-EQ': '4963',
        'TCS-EQ': '11536',
        'KOTAKBANK-EQ': '1922',
        'SBIN-EQ': '3045',
        'BHARTIARTL-EQ': '10604',
        'HINDUNILVR-EQ': '1394',
        'ITC-EQ': '1660'
    }
    
    return symbol_tokens.get(symbol, None)

def fetch_historical_data(symbol: str, token: str, from_date: str, to_date: str, 
                         jwt_token: str, api_key: str) -> pd.DataFrame:
    """Fetch 5-minute historical data from Angel One API"""
    
    url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/historical/v1/getCandleData"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "192.168.1.1",
        "X-ClientPublicIP": "106.51.74.202",
        "X-MACAddress": "fe80::1",
        "X-PrivateKey": api_key
    }
    
    payload = {
        "exchange": "NSE",
        "symboltoken": token,
        "interval": "FIVE_MINUTE",
        "fromdate": from_date,
        "todate": to_date
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') and data.get('data'):
            candles = data['data']
            
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Convert to IST
            df['timestamp'] = df['timestamp'] + pd.Timedelta(hours=5, minutes=30)
            
            # Convert price columns to float
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].astype(float)
            df['volume'] = df['volume'].astype(int)
            
            logging.info(f"✅ Fetched {len(df)} candles for {symbol}")
            return df
        else:
            logging.error(f"❌ Failed to fetch data: {data.get('message', 'Unknown error')}")
            return pd.DataFrame()
            
    except Exception as e:
        logging.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

def test_mean_reversion_today():
    """Test Mean Reversion strategy on today's data"""
    
    logging.info("\n" + "="*80)
    logging.info("MEAN REVERSION STRATEGY - BACKTEST ON DECEMBER 18, 2025")
    logging.info("="*80 + "\n")
    
    # Get JWT token from user
    logging.info("Please enter your current TOTP code (6 digits):")
    totp_code = input("TOTP: ").strip()
    
    if not totp_code or len(totp_code) != 6:
        logging.error("❌ Invalid TOTP. Cannot proceed.")
        logging.info("\nAlternative: Using simulated data for demo...")
        test_with_simulated_data()
        return
    
    # Generate JWT token
    logging.info("🔐 Authenticating with Angel One API...")
    jwt_token = get_jwt_token(API_KEY, CLIENT_CODE, PASSWORD, totp_code)
    
    if not jwt_token:
        logging.error("❌ Failed to authenticate. Using simulated data...")
        test_with_simulated_data()
        return
    
    # Initialize strategy
    strategy = MeanReversionStrategy(API_KEY, jwt_token)
    
    # Test symbols (start with just a few)
    test_symbols = [
        ('RELIANCE-EQ', '2885'),
        ('HDFCBANK-EQ', '1333'),
        ('INFY-EQ', '1594')
    ]
    
    # Date range (December 18, 2025)
    from_date = "2025-12-18 09:00"
    to_date = "2025-12-18 15:30"
    
    all_results = []
    
    for symbol, token in test_symbols:
        logging.info(f"\n{'='*80}")
        logging.info(f"Testing: {symbol}")
        logging.info(f"{'='*80}")
        
        # Fetch data
        df = fetch_historical_data(symbol, token, from_date, to_date, jwt_token, API_KEY)
        
        if df.empty:
            logging.warning(f"⚠️ No data for {symbol}, skipping...")
            continue
        
        logging.info(f"📊 Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        logging.info(f"📊 Total candles: {len(df)}")
        logging.info(f"📊 Price range: ₹{df['low'].min():.2f} - ₹{df['high'].max():.2f}")
        
        # Run backtest
        results = strategy.run_backtest(symbol, df, initial_capital=100000)
        
        if results['total_trades'] > 0:
            all_results.append(results)
            
            # Display summary
            logging.info(f"\n{'='*80}")
            logging.info(f"RESULTS: {symbol}")
            logging.info(f"{'='*80}")
            logging.info(f"Total Trades:     {results['total_trades']}")
            logging.info(f"Winning Trades:   {results['winning_trades']}")
            logging.info(f"Losing Trades:    {results['losing_trades']}")
            logging.info(f"Win Rate:         {results['win_rate']:.2f}%")
            logging.info(f"Total P&L:        ₹{results['total_pnl']:.2f}")
            logging.info(f"Return:           {results['return_pct']:.2f}%")
            logging.info(f"Avg Win:          ₹{results['avg_win']:.2f}")
            logging.info(f"Avg Loss:         ₹{results['avg_loss']:.2f}")
            logging.info(f"Largest Win:      ₹{results['largest_win']:.2f}")
            logging.info(f"Largest Loss:     ₹{results['largest_loss']:.2f}")
            logging.info(f"{'='*80}\n")
    
    # Overall summary
    if all_results:
        logging.info("\n" + "="*80)
        logging.info("OVERALL SUMMARY - MEAN REVERSION STRATEGY (Dec 18, 2025)")
        logging.info("="*80)
        
        total_trades = sum(r['total_trades'] for r in all_results)
        total_wins = sum(r['winning_trades'] for r in all_results)
        total_losses = sum(r['losing_trades'] for r in all_results)
        total_pnl = sum(r['total_pnl'] for r in all_results)
        
        overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        logging.info(f"Symbols Tested:   {len(all_results)}")
        logging.info(f"Total Trades:     {total_trades}")
        logging.info(f"Winning Trades:   {total_wins}")
        logging.info(f"Losing Trades:    {total_losses}")
        logging.info(f"Overall Win Rate: {overall_win_rate:.2f}%")
        logging.info(f"Total P&L:        ₹{total_pnl:.2f}")
        logging.info(f"Return:           {(total_pnl / 100000) * 100:.2f}%")
        logging.info("="*80)
        
        # Comparison with failed strategies
        logging.info("\n" + "="*80)
        logging.info("COMPARISON WITH FAILED STRATEGIES")
        logging.info("="*80)
        logging.info(f"Mean Reversion (Today):  {total_trades} trades, {overall_win_rate:.1f}% win rate, ₹{total_pnl:.2f} P&L")
        logging.info(f"v2.1 (1 year avg):       ~1 trade/day, 26.8% win rate, -₹107/day avg")
        logging.info(f"v1.5 (1 year avg):       ~6 trades/day, 29.4% win rate, -₹241/day avg")
        logging.info("="*80)
        
        if overall_win_rate > 40 and total_pnl > 0:
            logging.info("\n✅ MEAN REVERSION SHOWS PROMISE!")
            logging.info("   - Win rate better than breakout strategies (26-29%)")
            logging.info("   - Positive P&L on single day test")
            logging.info("   - Recommend: Continue paper trading for 1 week")
        elif overall_win_rate > 40:
            logging.info("\n⚠️ MIXED RESULTS")
            logging.info("   - Win rate decent but P&L not strong")
            logging.info("   - May need parameter tuning")
            logging.info("   - Recommend: Test on more days before deciding")
        else:
            logging.info("\n❌ MEAN REVERSION ALSO STRUGGLING")
            logging.info("   - Win rate similar to breakout strategies")
            logging.info("   - Need to explore other approaches")
            logging.info("   - Recommend: Try VWAP+SuperTrend or Last Hour strategies")
    else:
        logging.warning("\n⚠️ No trades were taken by Mean Reversion strategy today")
        logging.info("Possible reasons:")
        logging.info("- Market not suitable for mean reversion (strong trending day)")
        logging.info("- Filters too strict (need to loosen RSI/BB thresholds)")
        logging.info("- Volume requirements not met")

if __name__ == "__main__":
    test_mean_reversion_today()
