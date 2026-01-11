"""
Test if January 9, 2026 has historical data available
"""
import os
import sys
from datetime import datetime
from SmartApi import SmartConnect
import pyotp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'trading_bot_service'))

def test_specific_date(test_date):
    """Test if specific date has data"""
    
    print("=" * 80)
    print(f"🔍 Testing Historical Data for {test_date}")
    print("=" * 80)
    
    # Get credentials
    api_key = os.environ.get('ANGELONE_TRADING_API_KEY', '').strip()
    client_code = os.environ.get('ANGELONE_CLIENT_CODE', '').strip()
    password = os.environ.get('ANGELONE_PASSWORD', '').strip()
    totp_secret = os.environ.get('ANGELONE_TOTP_SECRET', '').strip()
    
    # Authenticate
    print("🔐 Authenticating...")
    smart_api = SmartConnect(api_key=api_key)
    totp = pyotp.TOTP(totp_secret).now()
    session_data = smart_api.generateSession(client_code, password, totp)
    
    if not session_data or not session_data.get('status'):
        print(f"❌ Authentication failed: {session_data}")
        return False
    
    print("✅ Authenticated")
    
    # Get RELIANCE token
    from nifty200_watchlist import NIFTY200_WATCHLIST
    reliance = next((s for s in NIFTY200_WATCHLIST if s['symbol'] == 'RELIANCE-EQ'), None)
    symbol_token = reliance['token']
    
    # Test data fetch
    print(f"\n📊 Fetching data for {test_date}...")
    params = {
        "exchange": "NSE",
        "symboltoken": symbol_token,
        "interval": "ONE_MINUTE",
        "fromdate": f"{test_date} 09:15",
        "todate": f"{test_date} 15:30"
    }
    
    print(f"   Params: {params}")
    hist_data = smart_api.getCandleData(params)
    
    print(f"\n   Response Status: {hist_data.get('status')}")
    print(f"   Message: {hist_data.get('message')}")
    print(f"   Error Code: {hist_data.get('errorcode')}")
    
    if hist_data.get('data'):
        candles = hist_data['data']
        print(f"   ✅ Candles: {len(candles)}")
        if candles:
            print(f"\n   First candle: {candles[0]}")
            print(f"   Last candle: {candles[-1]}")
        return True
    else:
        print(f"   ❌ No data available")
        return False

if __name__ == "__main__":
    # Test multiple dates
    test_dates = [
        '2026-01-09',  # Friday - user's date
        '2026-01-08',  # Thursday
        '2026-01-07',  # Wednesday
        '2026-01-06',  # Tuesday
    ]
    
    results = {}
    for date in test_dates:
        try:
            has_data = test_specific_date(date)
            results[date] = has_data
            print("\n")
        except Exception as e:
            print(f"❌ Error testing {date}: {e}\n")
            results[date] = False
    
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    for date, has_data in results.items():
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        day_name = date_obj.strftime('%A')
        status = "✅ HAS DATA" if has_data else "❌ NO DATA"
        print(f"{date} ({day_name:9s}): {status}")
    print("=" * 80)
