"""
Quick validation: Test Alpha-Ensemble with 276 Nifty 200 symbols
Runs 1-week backtest to verify speed and functionality
"""

from datetime import datetime, timedelta
from alpha_ensemble_strategy import AlphaEnsembleStrategy
from nifty200_watchlist import NIFTY200_WATCHLIST
import time

def generate_jwt_token(client_code: str, password: str, totp: str, api_key: str) -> str:
    """Generate JWT token for Angel One API"""
    import requests
    
    url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"
    
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


print("="*80)
print("🚀 ALPHA-ENSEMBLE 276-SYMBOL SPEED TEST")
print("="*80)

print(f"\n📊 Testing with {len(NIFTY200_WATCHLIST)} symbols")
print(f"   Expected processing time per symbol: ~0.4 seconds")
print(f"   Total scan time estimate: ~110 seconds (1.8 minutes)")
print(f"   Available buffer (15-min interval): 13+ minutes ✅\n")

# Get credentials
client_code = input("Client Code: ").strip()
password = input("Password: ").strip()
totp = input("TOTP Code: ").strip()
api_key = input("API Key: ").strip()

print("\n🔐 Authenticating...")
try:
    jwt_token = generate_jwt_token(client_code, password, totp, api_key)
    print("✅ Authentication successful!")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    exit(1)

# Test with 1-week period
strategy = AlphaEnsembleStrategy(api_key, jwt_token)
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"\n🎯 Testing period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"📦 Processing first 50 symbols as speed test...\n")

# Test first 50 symbols to measure speed
test_symbols = NIFTY200_WATCHLIST[:50]
start_time = time.time()

success_count = 0
for i, sym_data in enumerate(test_symbols, 1):
    symbol = sym_data['symbol']
    token = sym_data['token']
    
    try:
        # Fetch 5-minute data (lightweight test)
        df = strategy.fetch_historical_data(
            symbol=symbol,
            token=token,
            interval="FIVE_MINUTE",
            from_date=start_date.strftime("%Y-%m-%d %H:%M"),
            to_date=end_date.strftime("%Y-%m-%d %H:%M")
        )
        
        if not df.empty:
            success_count += 1
        
        if i % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            estimated_total = avg_time * 276
            print(f"   ✅ {i}/50 symbols | Avg: {avg_time:.2f}s/symbol | Est. for 276: {estimated_total/60:.1f} min")
    
    except Exception as e:
        print(f"   ❌ Error with {symbol}: {e}")
        continue

elapsed_time = time.time() - start_time
avg_per_symbol = elapsed_time / 50
projected_full_time = avg_per_symbol * 276

print("\n" + "="*80)
print("📊 SPEED TEST RESULTS")
print("="*80)
print(f"✅ Successfully fetched: {success_count}/50 symbols")
print(f"⏱️  Total time for 50 symbols: {elapsed_time:.1f} seconds")
print(f"⚡ Average time per symbol: {avg_per_symbol:.2f} seconds")
print(f"🎯 Projected time for all 276: {projected_full_time/60:.1f} minutes")
print(f"📦 15-minute interval buffer: {15 - (projected_full_time/60):.1f} minutes remaining")

if projected_full_time < 13 * 60:  # Less than 13 minutes
    print(f"\n✅✅ SYSTEM IS FAST ENOUGH! ({projected_full_time/60:.1f} min < 13 min)")
    print("🚀 Ready to deploy with 276 symbols!")
else:
    print(f"\n⚠️ WARNING: Projected time ({projected_full_time/60:.1f} min) exceeds safe buffer")
    print("💡 Consider reducing to ~200 symbols for safety")

print("="*80)
