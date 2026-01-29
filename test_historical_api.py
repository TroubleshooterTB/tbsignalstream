import os
import sys
from datetime import datetime, timedelta
from trading_bot_service.historical_data_manager import HistoricalDataManager

# Load credentials
api_key = os.getenv('ANGEL_API_KEY', '1s0GDpz1')
jwt_token = os.getenv('ANGEL_JWT_TOKEN')

if not jwt_token:
    print("ERROR: No JWT token found. Please login first.")
    sys.exit(1)

# Initialize manager
manager = HistoricalDataManager(api_key, jwt_token)

# Test with RELIANCE
now = datetime.now()
yesterday = now - timedelta(days=1)
while yesterday.weekday() >= 5:
    yesterday -= timedelta(days=1)

from_date = yesterday.replace(hour=9, minute=15, second=0, microsecond=0)
to_date = yesterday.replace(hour=15, minute=30, second=0, microsecond=0)

print(f"\n🧪 Testing historical API for RELIANCE")
print(f"📅 From: {from_date}")
print(f"📅 To: {to_date}")
print(f"⏰ Now: {now}\n")

df = manager.fetch_historical_data(
    symbol='RELIANCE',
    token='2885',  # RELIANCE token
    exchange='NSE',
    interval='ONE_MINUTE',
    from_date=from_date,
    to_date=to_date
)

if df is not None:
    print(f"✅ Got DataFrame with {len(df)} rows")
    print(f"📊 Columns: {list(df.columns)}")
    print(f"📊 Shape: {df.shape}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nLast 5 rows:")
    print(df.tail())
else:
    print("❌ No data returned")
