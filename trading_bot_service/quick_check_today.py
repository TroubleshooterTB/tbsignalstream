"""
Quick Check: Today's Market Data & Bot Status
"""
import os
import sys
from datetime import datetime

# Check if we can fetch today's data
print("=" * 80)
print("CHECKING TODAY'S MARKET DATA (December 18, 2025)")
print("=" * 80)

# Get credentials
api_key = os.environ.get('ANGELONE_API_KEY', 'jgosiGzs')
client_code = os.environ.get('ANGELONE_CLIENT_CODE', 'AABL713311')
password = os.environ.get('ANGELONE_PASSWORD', '1012')
totp = input("\nEnter TOTP: ").strip()

# Import strategy to get JWT function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "strategy_module",
    os.path.join(os.path.dirname(__file__), "run_backtest_defining_order_v2.1_51PCT.py")
)
strategy_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strategy_module)

# Login
print("\n🔐 Logging in...")
jwt_token = strategy_module.generate_jwt_token(api_key, client_code, password, totp)

if jwt_token:
    print("✅ Login successful!")
    
    # Fetch today's data for RELIANCE
    strategy = strategy_module.DefiningOrderStrategy(api_key, jwt_token)
    
    print("\n📊 Fetching RELIANCE-EQ data for today...")
    try:
        data = strategy.fetch_historical_data(
            symbol='RELIANCE-EQ',
            token='2885',
            interval='FIVE_MINUTE',
            from_date='2025-12-18 09:00',
            to_date='2025-12-18 15:30'
        )
        
        if data is not None and len(data) > 0:
            print(f"✅ Data found: {len(data)} candles")
            print(f"\nFirst candle: {data.index[0]}")
            print(f"Last candle: {data.index[-1]}")
            print(f"\nDefining Range period (9:30-10:30):")
            dr_data = data.between_time('09:30', '10:30')
            print(f"  Candles in DR: {len(dr_data)}")
            if len(dr_data) > 0:
                print(f"  DR High: ₹{dr_data['High'].max():.2f}")
                print(f"  DR Low: ₹{dr_data['Low'].min():.2f}")
                print("\n✅ DEFINING RANGE DATA IS AVAILABLE")
                print("   The bot SHOULD have been able to calculate DR")
            else:
                print("\n❌ NO DATA IN DEFINING RANGE PERIOD!")
                print("   This is why bot didn't trade - missing morning data")
        else:
            print("❌ No data available for today!")
            print("   Possible reasons:")
            print("   - Market holiday")
            print("   - API returning no data")
            print("   - Network/authentication issue")
            
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        
else:
    print("❌ Login failed")

print("\n" + "=" * 80)
print("KEY FINDINGS:")
print("=" * 80)
print("""
If data IS available:
  → Bot should have traded but filters rejected everything
  → OR there's a live vs backtest code difference
  → Need to check what filters rejected today's signals

If data is NOT available:
  → Market might be closed/holiday
  → API issue preventing data fetch
  → This explains why bot didn't trade
""")
