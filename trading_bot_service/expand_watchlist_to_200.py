"""
Quick script to expand WATCHLIST from 50 to 200 symbols
Uses existing proven tokens + fetches additional ~150 Nifty Next 50 + MidCap symbols
"""

from SmartApi import SmartConnect
import pyotp
import json
import time

def login_angel_one():
    """Get Angel One credentials and login"""
    print("🔐 Angel One Login")
    client_code = input("Client Code: ").strip()
    password = input("Password: ").strip()
    totp_code = input("TOTP Code: ").strip()
    api_key = input("API Key: ").strip()
    
    smart_api = SmartConnect(api_key=api_key)
    data = smart_api.generateSession(client_code, password, totp_code)
    
    if data['status']:
        print("✅ Login successful!")
        return smart_api, data['data']['jwtToken'], api_key
    else:
        raise Exception("Login failed")


def get_token_manual(smart_api, symbol):
    """Manually fetch token using getInstrument"""
    try:
        # Get instrument list
        instruments = smart_api.getInstruments('NSE')
        
        # Find matching symbol
        for inst in instruments:
            if inst.get('symbol') == symbol or inst.get('name') == symbol:
                return str(inst.get('token') or inst.get('symboltoken'))
        
        return None
    except:
        return None


# Nifty 200 Comprehensive List (without tokens)
NIFTY_200_SYMBOLS = [
    # Existing Nifty 50 with tokens (from test_alpha_ensemble.py)
    'RELIANCE', 'HDFCBANK', 'INFY', 'ICICIBANK', 'TCS', 'KOTAKBANK', 'BHARTIARTL',
    'HINDUNILVR', 'ITC', 'LT', 'AXISBANK', 'ASIANPAINT', 'MARUTI', 'SUNPHARMA',
    'TITAN', 'BAJFINANCE', 'ULTRACEMCO', 'NESTLEIND', 'WIPRO', 'HCLTECH', 
    'M&M', 'TATAMOTORS', 'NTPC', 'ONGC', 'TECHM', 'HINDALCO', 'ADANIENT',
    'COALINDIA', 'TATASTEEL', 'INDUSINDBK', 'BAJAJFINSV', 'POWERGRID', 'JSWSTEEL',
    'ADANIPORTS', 'DIVISLAB', 'HDFCLIFE', 'SBILIFE', 'DRREDDY', 'CIPLA',
    'EICHERMOT', 'GRASIM', 'TATACONSUM', 'BRITANNIA', 'HEROMOTOCO', 'APOLLOHOSP',
    'BAJAJ-AUTO', 'BPCL', 'SHRIRAMFIN', 'SBIN', 'TRENT',
    
    # Nifty Next 50 (add ~50 more)
    'ADANIGREEN', 'ADANIPOWER', 'ATGL', 'AMBUJACEM', 'BERGEPAINT', 'BOSCHLTD',
    'BEL', 'CANBK', 'CHOLAFIN', 'COLPAL', 'DLF', 'DABUR', 'DMART', 'GAIL',
    'GODREJCP', 'HAL', 'HAVELLS', 'HINDPETRO', 'ICICIPRULI', 'INDIGO',
    'IRCTC', 'JINDALSTEL', 'LTIM', 'LUPIN', 'NAUKRI', 'NMDC', 'PETRONET',
    'PIDILITIND', 'PNB', 'RECLTD', 'SIEMENS', 'SRF', 'TATAPOWER', 'TVSMOTOR',
    'TORNTPHARM', 'UPL', 'VEDL', 'VOLTAS', 'ZOMATO', 'ZYDUSLIFE', 'MOTHERSON',
    'BANKBARODA', 'INDHOTEL', 'LODHA', 'ABB', 'ACC', 'ALKEM', 'APOLLOTYRE',
    'ASHOKLEY', 'AUBANK',
    
    # Nifty Midcap 100 (add ~100 more high-liquid stocks)
    'AUROPHARMA', 'BANDHANBNK', 'BATAINDIA', 'BHARATFORG', 'BIOCON', 'CUMMINSIND',
    'CONCOR', 'COFORGE', 'CROMPTON', 'DEEPAKNTR', 'DIXON', 'ESCORTS', 'EXIDEIND',
    'FEDERALBNK', 'FORTIS', 'GLENMARK', 'GMRINFRA', 'GODFRYPHLP', 'GODREJPROP',
    'GUJGASLTD', 'HONAUT', 'IDFCFIRSTB', 'IGL', 'INDUSTOWER', 'INDIANB',
    'IPCALAB', 'IRFC', 'JKCEMENT', 'JSWENERGY', 'JUBLFOOD', 'KAJARIACER',
    'KPITTECH', 'LICHSGFIN', 'LTF', 'LTTS', 'LALPATHLAB', 'LAURUSLABS',
    'MARICO', 'MANAPPURAM', 'MFSL', 'MAXHEALTH', 'MCX', 'MPHASIS', 'MRF',
    'MUTHOOTFIN', 'NATIONALUM', 'NAVINFLUOR', 'OBEROIRLTY', 'OFSS', 'OIL',
    'PAYTM', 'PERSISTENT', 'PIIND', 'PFC', 'POLYCAB', 'PVRINOX', 'RBLBANK',
    'SAIL', 'SBICARD', 'SCHAEFFLER', 'SHREECEM', 'SONACOMS', 'STARHEALTH',
    'SUNTV', 'SUPREMEIND', 'SYNGENE', 'TATACOMM', 'TATAELXSI', 'TATATECH',
    'TIINDIA', 'TORNTPOWER', 'TRIDENT', 'UBL', 'UNIONBANK', 'WHIRLPOOL',
    'YESBANK', 'ZEEL', '3MINDIA', 'AARTIIND', 'ABBOTINDIA', 'ABCAPITAL',
    'ABFRL', 'AJANTPHARM', 'APLLTD', 'ASTRAL', 'ATUL', 'BALKRISIND',
    'BALRAMCHIN', 'BHARTIHEXA', 'BHEL', 'CANFINHOME', 'CHAMBLFERT', 'CHOLAHLDNG',
    'CLEAN', 'COCHINSHIP', 'COROMANDEL', 'CUB', 'CYIENT', 'DELHIVERY',
    'FACT', 'FLUOROCHEM', 'FSL', 'GICRE', 'GILLETTE', 'GLAXO', 'GODREJIND',
    'GRINFRA', 'GSPL', 'GUJALKALI', 'HATSUN', 'HEG', 'HINDZINC', 'IBULHSGFIN',
    'IIFL', 'IOC', 'J&KBANK', 'JBCHEPHARM', 'JKLAKSHMI', 'JMFINANCIL',
    'JUSTDIAL', 'KANSAINER', 'KEI', 'KNRCON', 'L&TFH', 'LEMONTREE',
    'LINDEINDIA', 'M&MFIN', 'MAHABANK', 'MANINFRA', 'MAZDOCK', 'METROPOLIS',
    'MINDACORP', 'MINDAIND', 'MMTC', 'MOREPENLAB', 'MOTILALOFS', 'NAM-INDIA',
    'NBCC', 'NCC', 'NETWORK18', 'NLCINDIA', 'NYKAA', 'ORIENTELEC', 'PAGEIND',
    'PATANJALI', 'PGHH', 'PHOENIXLTD', 'PNBHOUSING', 'POLICYBZR', 'POWERINDIA',
    'PRAJIND', 'PRESTIGE', 'QUESS', 'RADICO', 'RAINBOW', 'RAJESHEXPO',
    'RATNAMANI', 'ROUTE', 'SANOFI', 'SFL', 'SHARDACROP', 'SHOPERSTOP',
    'SJVN', 'SKFINDIA', 'SOBHA', 'SOLARINDS', 'SUMICHEM', 'SUNDARMFIN',
    'SUNDRMFAST', 'SUZLON', 'SYMPHONY', 'TASTYBITE', 'TATACHEM', 'TATAINVEST',
    'THERMAX', 'TIMKEN', 'TNPL', 'TTKPRESTIG', 'TV18BRDCST', 'UJJIVAN',
    'UNITDSPR', 'UCOBANK', 'VBL', 'VGUARD', 'VINATIORGA', 'VSTIND',
    'WABAG', 'WELCORP', 'WELSPUNIND', 'WESTLIFE', 'ZENSARTECH'
]

# Existing confirmed tokens from test_alpha_ensemble.py
CONFIRMED_TOKENS = {
    'RELIANCE-EQ': '2885',
    'HDFCBANK-EQ': '1333',
    'INFY-EQ': '1594',
    'ICICIBANK-EQ': '4963',
    'TCS-EQ': '11536',
    'KOTAKBANK-EQ': '1922',
    'BHARTIARTL-EQ': '10604',
    'HINDUNILVR-EQ': '1394',
    'ITC-EQ': '1660',
    'LT-EQ': '11483',
    'AXISBANK-EQ': '5900',
    'ASIANPAINT-EQ': '236',
    'MARUTI-EQ': '10999',
    'SUNPHARMA-EQ': '3351',
    'TITAN-EQ': '3506',
    'BAJFINANCE-EQ': '317',
    'ULTRACEMCO-EQ': '11532',
    'NESTLEIND-EQ': '17963',
    'WIPRO-EQ': '3787',
    'HCLTECH-EQ': '7229',
    'M&M-EQ': '2031',
    'TATAMOTORS-EQ': '3456',
    'NTPC-EQ': '11630',
    'ONGC-EQ': '2475',
    'TECHM-EQ': '13538',
    'HINDALCO-EQ': '1363',
    'ADANIENT-EQ': '25',
    'COALINDIA-EQ': '20374',
    'TATASTEEL-EQ': '3499',
    'INDUSINDBK-EQ': '5258',
    'BAJAJFINSV-EQ': '16675',
    'POWERGRID-EQ': '14977',
    'JSWSTEEL-EQ': '11723',
    'ADANIPORTS-EQ': '15083',
    'DIVISLAB-EQ': '10940',
    'HDFCLIFE-EQ': '467',
    'SBILIFE-EQ': '21808',
    'DRREDDY-EQ': '881',
    'CIPLA-EQ': '694',
    'EICHERMOT-EQ': '910',
    'GRASIM-EQ': '1232',
    'TATACONSUM-EQ': '3432',
    'BRITANNIA-EQ': '547',
    'HEROMOTOCO-EQ': '1348',
    'APOLLOHOSP-EQ': '157',
    'BAJAJ-AUTO-EQ': '16669',
    'BPCL-EQ': '526',
    'SHRIRAMFIN-EQ': '5906',
    'SBIN-EQ': '3045',
    'TRENT-EQ': '1964'
}

print("="*80)
print("📊 NIFTY 200 WATCHLIST EXPANDER")
print("="*80)
print(f"\nTarget: Expand from 50 to ~200 symbols")
print(f"Confirmed tokens available: {len(CONFIRMED_TOKENS)}")
print(f"Additional symbols to fetch: {len(NIFTY_200_SYMBOLS) - len(CONFIRMED_TOKENS)}")

proceed = input("\n⚠️ This will take ~5-10 minutes. Proceed? (yes/no): ").strip().lower()
if proceed != 'yes':
    print("❌ Aborted")
    exit()

# Login
smart_api, jwt_token, api_key = login_angel_one()

# Build final watchlist
final_watchlist = []

# Add confirmed tokens first
for symbol, token in CONFIRMED_TOKENS.items():
    final_watchlist.append({"symbol": symbol, "token": token})

print(f"\n✅ Added {len(CONFIRMED_TOKENS)} confirmed tokens")

# Now fetch remaining symbols
remaining = [s for s in NIFTY_200_SYMBOLS if f"{s}-EQ" not in CONFIRMED_TOKENS]
print(f"\n🔍 Fetching tokens for {len(remaining)} additional symbols...")

success_count = 0
for i, symbol in enumerate(remaining, 1):
    try:
        token = get_token_manual(smart_api, symbol)
        if token:
            final_watchlist.append({"symbol": f"{symbol}-EQ", "token": token})
            success_count += 1
        
        if i % 20 == 0:
            print(f"   Progress: {i}/{len(remaining)} ({success_count} successful)")
        
        time.sleep(0.1)  # Rate limiting
    except:
        continue

print(f"\n✅ Total symbols in watchlist: {len(final_watchlist)}")

# Save to JSON
with open('nifty200_final_watchlist.json', 'w') as f:
    json.dump(final_watchlist, f, indent=2)

# Print Python code for direct copy-paste
print("\n" + "="*80)
print("📋 WATCHLIST CODE (Copy to test_alpha_ensemble.py):")
print("="*80)
print("\ntest_symbols = [")
for item in final_watchlist[:10]:
    print(f"    {{'symbol': '{item['symbol']}', 'token': '{item['token']}'}},")
print(f"    # ... {len(final_watchlist)-10} more symbols")
print("]")
print(f"\n💾 Full list saved to: nifty200_final_watchlist.json")
print(f"📊 Total: {len(final_watchlist)} symbols ready for trading!")
