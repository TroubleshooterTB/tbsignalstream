"""
Fetch correct Angel One tokens for all Nifty 50 symbols
Uses searchScrip API to get current valid tokens
"""

import requests
import time
import json


def generate_jwt_token(client_code: str, password: str, totp: str, api_key: str) -> str:
    """Generate JWT token for Angel One API"""
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


def search_symbol(symbol: str, jwt_token: str, api_key: str) -> dict:
    """Search for symbol and get its token"""
    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/searchScrip"
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
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
        "exchange": "NSE",
        "searchscrip": symbol.replace('-EQ', '')
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        time.sleep(1.1)  # Rate limit: 1 call/second
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') and data.get('data'):
                search_name = symbol.replace('-EQ', '')
                
                # Look for the -EQ segment specifically
                for item in data['data']:
                    trading_symbol = item.get('tradingsymbol', '')
                    
                    # For indices (no -EQ suffix)
                    if symbol == 'NIFTY 50' and 'NIFTY' in trading_symbol and item.get('exchange') == 'NSE':
                        # This is likely the Nifty 50 index
                        return {
                            'symbol': symbol,
                            'token': item.get('symboltoken'),
                            'name': trading_symbol,
                            'trading_symbol': trading_symbol
                        }
                    
                    # For stocks, look for exact match on -EQ segment
                    if trading_symbol == search_name and item.get('exchange') == 'NSE':
                        # Check if there's an -EQ variant in the data
                        eq_variant = next((x for x in data['data'] 
                                          if x.get('tradingsymbol') == search_name + '-EQ'), None)
                        
                        if eq_variant:
                            # Use the -EQ variant token
                            return {
                                'symbol': symbol,
                                'token': eq_variant.get('symboltoken'),
                                'name': search_name,
                                'trading_symbol': search_name
                            }
                        else:
                            # Just use the base symbol
                            return {
                                'symbol': symbol,
                                'token': item.get('symboltoken'),
                                'name': search_name,
                                'trading_symbol': trading_symbol
                            }
        
        print(f"⚠️ Failed to find token for {symbol}: {response.text[:200]}")
        return None
    
    except Exception as e:
        print(f"❌ Error searching {symbol}: {e}")
        return None


def main():
    print("\n" + "=" * 80)
    print("FETCH CORRECT ANGEL ONE TOKENS FOR NIFTY 50")
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
    
    # All Nifty 50 symbols
    nifty_50_symbols = [
        'RELIANCE-EQ', 'HDFCBANK-EQ', 'INFY-EQ', 'ICICIBANK-EQ', 'TCS-EQ',
        'KOTAKBANK-EQ', 'BHARTIARTL-EQ', 'HINDUNILVR-EQ', 'ITC-EQ', 'LT-EQ',
        'AXISBANK-EQ', 'ASIANPAINT-EQ', 'MARUTI-EQ', 'SUNPHARMA-EQ', 'TITAN-EQ',
        'BAJFINANCE-EQ', 'ULTRACEMCO-EQ', 'NESTLEIND-EQ', 'WIPRO-EQ', 'HCLTECH-EQ',
        'M&M-EQ', 'TATAMOTORS-EQ', 'NTPC-EQ', 'ONGC-EQ', 'TECHM-EQ',
        'HINDALCO-EQ', 'ADANIENT-EQ', 'TATASTEEL-EQ', 'CIPLA-EQ', 'BAJAJFINSV-EQ',
        'COALINDIA-EQ', 'DRREDDY-EQ', 'EICHERMOT-EQ', 'HEROMOTOCO-EQ', 'APOLLOHOSP-EQ',
        'DIVISLAB-EQ', 'INDUSINDBK-EQ', 'TATACONSUM-EQ', 'GRASIM-EQ', 'BRITANNIA-EQ',
        'BAJAJ-AUTO-EQ', 'ADANIPORTS-EQ', 'BPCL-EQ', 'UPL-EQ', 'SBILIFE-EQ',
        'HDFCLIFE-EQ', 'JSWSTEEL-EQ', 'TRENT-EQ', 'LTIM-EQ'
    ]
    
    # Also get Nifty 50 index token
    nifty_50_symbols.insert(0, 'NIFTY 50')
    
    print(f"\n📊 Fetching tokens for {len(nifty_50_symbols)} symbols...")
    print("⏱️ This will take ~60 seconds due to rate limits...\n")
    
    results = []
    failed = []
    
    for symbol in nifty_50_symbols:
        print(f"Fetching {symbol}...", end=' ')
        result = search_symbol(symbol, jwt_token, api_key)
        
        if result:
            results.append(result)
            print(f"✅ Token: {result['token']}")
        else:
            failed.append(symbol)
            print("❌ FAILED")
    
    # Print results in Python dict format
    print("\n" + "=" * 80)
    print("RESULTS - Copy this to test_alpha_ensemble.py:")
    print("=" * 80)
    print("\ntest_symbols = [")
    for r in results:
        if r['symbol'] != 'NIFTY 50':
            print(f"    {{'symbol': '{r['symbol']}', 'token': '{r['token']}'}},")
    print("]\n")
    
    # Print Nifty 50 token separately
    nifty_token = next((r for r in results if r['symbol'] == 'NIFTY 50'), None)
    if nifty_token:
        print(f"NIFTY 50 Token: '{nifty_token['token']}'")
    
    print("\n" + "=" * 80)
    print(f"✅ Success: {len(results)} symbols")
    print(f"❌ Failed: {len(failed)} symbols")
    
    if failed:
        print(f"\nFailed symbols: {', '.join(failed)}")
    
    # Save to JSON file
    with open('nifty50_tokens.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Saved to nifty50_tokens.json")


if __name__ == '__main__':
    main()
