"""
Fetch Official Nifty 200 Constituents from NSE + Angel One Tokens
Uses NSE India official website and maps to Angel One exchange tokens
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime
from typing import List, Dict
from SmartApi import SmartConnect
import pyotp

def fetch_nse_nifty200():
    """Fetch Nifty 200 constituents from NSE official source"""
    print("🔍 Fetching Nifty 200 constituents from NSE India...")
    
    # NSE official CSV endpoint for Nifty 200
    nse_url = "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(nse_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse CSV
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        # Extract symbols (usually in 'Symbol' column)
        if 'Symbol' in df.columns:
            symbols = df['Symbol'].tolist()
        elif 'symbol' in df.columns:
            symbols = df['symbol'].tolist()
        else:
            # Fallback: take first column
            symbols = df.iloc[:, 0].tolist()
        
        # Clean symbols
        symbols = [str(s).strip().upper() for s in symbols if pd.notna(s)]
        symbols = [s for s in symbols if s and s != 'NAN']
        
        print(f"✅ Fetched {len(symbols)} symbols from NSE")
        return symbols
        
    except Exception as e:
        print(f"❌ Error fetching from NSE: {e}")
        print("📋 Using fallback: Hardcoded Nifty 200 list")
        return get_fallback_nifty200()


def get_fallback_nifty200():
    """Hardcoded Nifty 200 list as fallback"""
    return [
        # Nifty 50 (Large Cap)
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 
        'BHARTIARTL', 'KOTAKBANK', 'LT', 'AXISBANK', 'ASIANPAINT', 'MARUTI', 'SUNPHARMA',
        'TITAN', 'BAJFINANCE', 'HCLTECH', 'ULTRACEMCO', 'NESTLEIND', 'WIPRO', 'ADANIENT',
        'ONGC', 'NTPC', 'JSWSTEEL', 'POWERGRID', 'M&M', 'TATAMOTORS', 'TECHM', 'HINDALCO',
        'COALINDIA', 'INDUSINDBK', 'BAJAJFINSV', 'TATASTEEL', 'ADANIPORTS', 'DIVISLAB',
        'HDFCLIFE', 'APOLLOHOSP', 'DRREDDY', 'CIPLA', 'EICHERMOT', 'GRASIM', 'TATACONSUM',
        'SBILIFE', 'HEROMOTOCO', 'BRITANNIA', 'BAJAJ-AUTO', 'BPCL', 'SHRIRAMFIN', 'TRENT',
        
        # Nifty Next 50 (Mid Cap)
        'ADANIGREEN', 'ADANIPOWER', 'ATGL', 'AMBUJACEM', 'BERGEPAINT', 'BOSCHLTD', 'BEL',
        'CANBK', 'CHOLAFIN', 'COLPAL', 'DLF', 'DABUR', 'DMART', 'GAIL', 'GODREJCP',
        'GLAND', 'HAVELLS', 'HINDPETRO', 'ICICIPRULI', 'INDIGO', 'IRCTC', 'JINDALSTEL',
        'LTIM', 'LUPIN', 'NAUKRI', 'NMDC', 'PETRONET', 'PIDILITIND', 'PNB', 'RECLTD',
        'SIEMENS', 'SRF', 'TATAPOWER', 'TVSMOTOR', 'TORNTPHARM', 'UPL', 'VEDL', 'VOLTAS',
        'ZOMATO', 'ZYDUSLIFE', 'MOTHERSON', 'BANKBARODA', 'INDHOTEL', 'LODHA', 'ABB',
        'ACC', 'ALKEM', 'APOLLOTYRE', 'ASHOKLEY',
        
        # Other Nifty 200 Constituents (Small-Mid Cap)
        'AUBANK', 'AUROPHARMA', 'BAJAJHLDNG', 'BANDHANBNK', 'BATAINDIA', 'BHARATFORG',
        'BIOCON', 'CUMMINSIND', 'CONCOR', 'COFORGE', 'CROMPTON', 'DEEPAKNTR', 'DIXON',
        'ESCORTS', 'EXIDEIND', 'FEDERALBNK', 'FORTIS', 'GLAXO', 'GMRINFRA', 'GNFC',
        'GODFRYPHLP', 'GRANULES', 'GUJGASLTD', 'HAL', 'HONAUT', 'IDFCFIRSTB', 'IDFC',
        'IGL', 'INDUSTOWER', 'INDIACEM', 'INDIANB', 'IPCALAB', 'IRFC', 'JKCEMENT',
        'JSWENERGY', 'JUBLFOOD', 'KAJARIACER', 'KPITTECH', 'LICHSGFIN', 'LTF', 'LTTS',
        'LALPATHLAB', 'LAURUSLABS', 'MARICO', 'MANAPPURAM', 'MFSL', 'MAXHEALTH', 'MCX',
        'MPHASIS', 'MRF', 'MUTHOOTFIN', 'NATIONALUM', 'NAVINFLUOR', 'OBEROIRLTY', 'OFSS',
        'OIL', 'PAYTM', 'PERSISTENT', 'PIIND', 'PFC', 'POLYCAB', 'PVRINOX', 'RBLBANK',
        'SAIL', 'SBICARD', 'SCHAEFFLER', 'SHREECEM', 'SONACOMS', 'STARHEALTH', 'SUNPHARMA',
        'SUNTV', 'SUPREMEIND', 'SYNGENE', 'TATACOMM', 'TATAELXSI', 'TATATECH', 'TIINDIA',
        'TORNTPOWER', 'TRENT', 'TRIDENT', 'UBL', 'UNIONBANK', 'WHIRLPOOL', 'YESBANK',
        'ZEEL', '3MINDIA', 'AARTIIND', 'ABBOTINDIA', 'ABCAPITAL', 'ABFRL', 'AJANTPHARM',
        'APLLTD', 'ASTRAL', 'ATUL', 'BALKRISIND', 'BALRAMCHIN', 'BHARTIHEXA', 'BHEL',
        'BSOFT', 'CANBK', 'CANFINHOME', 'CHAMBLFERT', 'CHOLAHLDNG', 'CLEAN', 'COALINDIA',
        'COCHINSHIP', 'COROMANDEL', 'CUB', 'CYIENT', 'DELTACORP', 'DELHIVERY', 'DELTACORP',
        'FACT', 'FLUOROCHEM', 'FSL', 'GICRE', 'GILLETTE', 'GLAXO', 'GODREJIND', 'GODREJPROP',
        'GRINFRA', 'GSPL', 'GUJALKALI', 'HAPPSTMNDS', 'HATSUN', 'HEG', 'HINDZINC',
        'IBULHSGFIN', 'IIFL', 'INOXWIND', 'IOC', 'J&KBANK', 'JBCHEPHARM', 'JKLAKSHMI',
        'JMFINANCIL', 'JUSTDIAL', 'KANSAINER', 'KEI', 'KNRCON', 'L&TFH', 'LEMONTREE',
        'LINDEINDIA', 'M&MFIN', 'MAHABANK', 'MANINFRA', 'MAZDOCK', 'METROPOLIS', 'MINDACORP',
        'MINDAIND', 'MMTC', 'MOREPENLAB', 'MOTILALOFS', 'NAM-INDIA', 'NBCC', 'NCC',
        'NETWORK18', 'NLCINDIA', 'NYKAA', 'ORIENTELEC', 'PAGEIND', 'PATANJALI', 'PGHH',
        'PHOENIXLTD', 'PNBHOUSING', 'POLICYBZR', 'POWERINDIA', 'PRAJIND', 'PRESTIGE',
        'QUESS', 'RADICO', 'RAINBOW', 'RAJESHEXPO', 'RATNAMANI', 'RTNINDIA', 'ROUTE',
        'SANOFI', 'SAPPHIRE', 'SFL', 'SHARDACROP', 'SHOPERSTOP', 'SJVN', 'SKFINDIA',
        'SOBHA', 'SOLARINDS', 'SUMICHEM', 'SUNDARMFIN', 'SUNDRMFAST', 'SUZLON', 'SYMPHONY',
        'TASTYBITE', 'TATACHEM', 'TATACOMM', 'TATAINVEST', 'TATAPOWER', 'THERMAX', 'TIMKEN',
        'TITAN', 'TNPL', 'TTKPRESTIG', 'TV18BRDCST', 'UJJIVAN', 'ULTRACEMCO', 'UNITDSPR',
        'UCOBANK', 'VBL', 'VGUARD', 'VINATIORGA', 'VSTIND', 'WABAG', 'WELCORP', 'WELSPUNIND',
        'WESTLIFE', 'ZENSARTECH'
    ]


def get_angel_tokens(symbols: List[str], client_code: str, password: str, totp_code: str, api_key: str):
    """Get Angel One exchange tokens for given symbols"""
    print(f"\n🔗 Fetching Angel One tokens for {len(symbols)} symbols...")
    
    # Login to Angel One
    try:
        smart_api = SmartConnect(api_key=api_key)
        
        login_response = smart_api.generateSession(client_code, password, totp_code)
        if not login_response or 'data' not in login_response:
            print(f"❌ Login failed: {login_response}")
            return {}
        
        jwt_token = login_response['data']['jwtToken']
        refresh_token = login_response['data']['refreshToken']
        print("✅ Successfully authenticated with Angel One")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return {}
    
    # Use REST API to search for symbols
    search_url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/searchScrip"
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '192.168.1.1',
        'X-ClientPublicIP': '106.193.147.98',
        'X-MACAddress': 'fe:80:00:00:00:00',
        'X-PrivateKey': api_key
    }
    
    symbol_tokens = {}
    failed_symbols = []
    
    for i, symbol in enumerate(symbols, 1):
        try:
            # Try with -EQ suffix for NSE equity
            search_symbol = symbol if '-EQ' in symbol else f"{symbol}-EQ"
            
            payload = {
                "exchange": "NSE",
                "searchscrip": search_symbol
            }
            
            response = requests.post(search_url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract token from response
                if data and 'data' in data and data['data']:
                    token = data['data'].get('symboltoken') or data['data'].get('token')
                    actual_symbol = data['data'].get('symbol') or data['data'].get('tradingsymbol') or search_symbol
                    
                    if token:
                        symbol_tokens[actual_symbol] = str(token)
                    else:
                        failed_symbols.append(symbol)
                else:
                    failed_symbols.append(symbol)
            else:
                failed_symbols.append(symbol)
            
            if i % 20 == 0:
                print(f"   Progress: {i}/{len(symbols)} symbols processed...")
            
            # Rate limiting
            time.sleep(0.15)
            
        except Exception as e:
            # Silently fail individual symbols
            failed_symbols.append(symbol)
            continue
    
    print(f"\n✅ Successfully mapped {len(symbol_tokens)} symbols")
    if failed_symbols:
        print(f"⚠️ Failed to map {len(failed_symbols)} symbols")
    
    return symbol_tokens


def save_watchlist(symbol_tokens: Dict[str, str], output_file: str = "nifty200_watchlist.json"):
    """Save watchlist in format ready for alpha_ensemble_strategy.py"""
    
    watchlist = []
    for symbol, token in symbol_tokens.items():
        watchlist.append({
            "symbol": symbol,
            "token": token
        })
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(watchlist, f, indent=2)
    
    print(f"\n💾 Saved {len(watchlist)} symbols to {output_file}")
    
    # Also print Python code format for direct copy-paste
    print("\n" + "="*80)
    print("📋 WATCHLIST CODE (Copy to alpha_ensemble_strategy.py):")
    print("="*80)
    print("\nWATCHLIST = [")
    for item in watchlist[:5]:  # Show first 5 as example
        print(f'    {{"symbol": "{item["symbol"]}", "token": "{item["token"]}"}},')
    print(f"    # ... {len(watchlist)-5} more symbols")
    print("]\n")
    
    return watchlist


def main():
    print("="*80)
    print("🎯 NIFTY 200 WATCHLIST BUILDER FOR ALPHA-ENSEMBLE STRATEGY")
    print("="*80)
    print()
    
    # Step 1: Fetch NSE symbols
    symbols = fetch_nse_nifty200()
    print(f"\n📊 Total symbols to process: {len(symbols)}")
    
    # Step 2: Get Angel One credentials
    print("\n🔐 Angel One Authentication Required:")
    client_code = input("Enter Client Code: ").strip()
    password = input("Enter Password: ").strip()
    totp_code = input("Enter TOTP Code (6 digits from app): ").strip()
    api_key = input("Enter API Key: ").strip()
    
    # Step 3: Fetch tokens
    symbol_tokens = get_angel_tokens(symbols, client_code, password, totp_code, api_key)
    
    if len(symbol_tokens) < 100:
        print(f"\n⚠️ WARNING: Only {len(symbol_tokens)} symbols mapped (expected ~200)")
        print("This may impact trading opportunities.")
        proceed = input("Continue anyway? (yes/no): ").strip().lower()
        if proceed != 'yes':
            print("❌ Aborted by user")
            return
    
    # Step 4: Save watchlist
    watchlist = save_watchlist(symbol_tokens)
    
    # Final summary
    print("\n" + "="*80)
    print("✅ NIFTY 200 WATCHLIST CREATION COMPLETE!")
    print("="*80)
    print(f"📊 Total Symbols: {len(watchlist)}")
    print(f"📁 Saved to: nifty200_watchlist.json")
    print("\n🎯 NEXT STEPS:")
    print("1. Copy the WATCHLIST code above")
    print("2. Replace the WATCHLIST in alpha_ensemble_strategy.py")
    print("3. Run a quick backtest to verify")
    print("4. Deploy for live trading!")
    print("="*80)


if __name__ == "__main__":
    main()
