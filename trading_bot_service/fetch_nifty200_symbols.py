"""
Nifty 200 Symbol & Token Manager
=================================

Automatically fetches complete Nifty 200 constituent list with:
- Symbol names
- Angel One tokens
- Sector classification
- Market cap ranking

Saves to JSON for quick access during screening
"""

import requests
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Nifty200Manager:
    """Manage Nifty 200 constituents with Angel One tokens"""
    
    def __init__(self, api_key: str, jwt_token: str):
        self.api_key = api_key
        self.jwt_token = jwt_token
        
        # Sector mapping for Nifty 200 stocks
        self.SECTOR_MAPPING = {
            # Banking & Financial Services
            'HDFCBANK': 'BANK', 'ICICIBANK': 'BANK', 'KOTAKBANK': 'BANK',
            'AXISBANK': 'BANK', 'SBIN': 'BANK', 'INDUSINDBK': 'BANK',
            'BANDHANBNK': 'BANK', 'FEDERALBNK': 'BANK', 'IDFCFIRSTB': 'BANK',
            'BAJFINANCE': 'FINANCIAL_SERVICES', 'BAJAJFINSV': 'FINANCIAL_SERVICES',
            'SBILIFE': 'FINANCIAL_SERVICES', 'HDFCLIFE': 'FINANCIAL_SERVICES',
            'ICICIPRULI': 'FINANCIAL_SERVICES', 'BAJAJHLDNG': 'FINANCIAL_SERVICES',
            'CHOLAFIN': 'FINANCIAL_SERVICES', 'MUTHOOTFIN': 'FINANCIAL_SERVICES',
            
            # IT & Software
            'INFY': 'IT', 'TCS': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT',
            'TECHM': 'IT', 'LTIM': 'IT', 'PERSISTENT': 'IT', 'COFORGE': 'IT',
            'MPHASIS': 'IT', 'LTTS': 'IT',
            
            # Auto & Auto Components
            'MARUTI': 'AUTO', 'TATAMOTORS': 'AUTO', 'M&M': 'AUTO',
            'BAJAJ-AUTO': 'AUTO', 'EICHERMOT': 'AUTO', 'HEROMOTOCO': 'AUTO',
            'ASHOKLEY': 'AUTO', 'TVSMOTOR': 'AUTO', 'MOTHERSON': 'AUTO',
            'BOSCHLTD': 'AUTO', 'EXIDEIND': 'AUTO', 'APOLLOTYRE': 'AUTO',
            'MRF': 'AUTO', 'BHARATFORG': 'AUTO',
            
            # Energy & Oil/Gas
            'RELIANCE': 'ENERGY', 'ONGC': 'ENERGY', 'BPCL': 'ENERGY',
            'IOC': 'ENERGY', 'HINDPETRO': 'ENERGY', 'GAIL': 'ENERGY',
            'ADANIGREEN': 'ENERGY', 'ADANITRANS': 'ENERGY', 'ATUL': 'ENERGY',
            
            # Metals & Mining
            'TATASTEEL': 'METALS', 'HINDALCO': 'METALS', 'COALINDIA': 'METALS',
            'VEDL': 'METALS', 'JINDALSTEL': 'METALS', 'SAIL': 'METALS',
            'HINDZINC': 'METALS', 'NMDC': 'METALS', 'NATIONALUM': 'METALS',
            'JSWSTEEL': 'METALS',
            
            # Pharma & Healthcare
            'SUNPHARMA': 'PHARMA', 'CIPLA': 'PHARMA', 'DRREDDY': 'PHARMA',
            'DIVISLAB': 'PHARMA', 'APOLLOHOSP': 'HEALTHCARE', 'BIOCON': 'PHARMA',
            'LAURUSLABS': 'PHARMA', 'TORNTPHARM': 'PHARMA', 'ALKEM': 'PHARMA',
            'LUPIN': 'PHARMA', 'AUROPHARMA': 'PHARMA', 'GLENMARK': 'PHARMA',
            'MANKIND': 'PHARMA', 'MAXHEALTH': 'HEALTHCARE', 'FORTIS': 'HEALTHCARE',
            
            # FMCG & Consumer
            'HINDUNILVR': 'FMCG', 'ITC': 'FMCG', 'NESTLEIND': 'FMCG',
            'BRITANNIA': 'FMCG', 'TATACONSUM': 'FMCG', 'DABUR': 'FMCG',
            'MARICO': 'FMCG', 'GODREJCP': 'FMCG', 'COLPAL': 'FMCG',
            'MCDOWELL-N': 'FMCG', 'EMAMILTD': 'FMCG', 'VBL': 'FMCG',
            
            # Consumer Durables
            'TITAN': 'CONSUMER_DURABLES', 'ASIANPAINT': 'CONSUMER_DURABLES',
            'HAVELLS': 'CONSUMER_DURABLES', 'VOLTAS': 'CONSUMER_DURABLES',
            'WHIRLPOOL': 'CONSUMER_DURABLES', 'CROMPTON': 'CONSUMER_DURABLES',
            'DIXON': 'CONSUMER_DURABLES', 'AMBER': 'CONSUMER_DURABLES',
            
            # Telecom
            'BHARTIARTL': 'TELECOM', 'IDEA': 'TELECOM',
            
            # Cement
            'ULTRACEMCO': 'CEMENT', 'AMBUJACEM': 'CEMENT', 'ACC': 'CEMENT',
            'SHREECEM': 'CEMENT', 'DALMIACEM': 'CEMENT', 'JKCEMENT': 'CEMENT',
            
            # Capital Goods
            'LT': 'CAPITAL_GOODS', 'SIEMENS': 'CAPITAL_GOODS', 'ABB': 'CAPITAL_GOODS',
            'BHEL': 'CAPITAL_GOODS', 'CUMMINSIND': 'CAPITAL_GOODS',
            'THERMAX': 'CAPITAL_GOODS', 'SCHAEFFLER': 'CAPITAL_GOODS',
            
            # Power
            'NTPC': 'POWER', 'POWERGRID': 'POWER', 'ADANIPOWER': 'POWER',
            'TATAPOWER': 'POWER', 'TORNTPOWER': 'POWER',
            
            # Infrastructure & Realty
            'ADANIPORTS': 'INFRASTRUCTURE', 'DLF': 'REALTY', 'OBEROIRLTY': 'REALTY',
            'GODREJPROP': 'REALTY', 'PHOENIXLTD': 'REALTY', 'PRESTIGE': 'REALTY',
            
            # Retail
            'TRENT': 'RETAIL', 'DMART': 'RETAIL', 'ABFRL': 'RETAIL',
            'SHOPERSTOP': 'RETAIL', 'RELAXO': 'RETAIL',
            
            # Agro Chemicals
            'UPL': 'AGRO_CHEMICALS', 'PIIND': 'AGRO_CHEMICALS', 'SUMICHEM': 'AGRO_CHEMICALS',
            
            # Diversified
            'ADANIENT': 'DIVERSIFIED', 'GRASIM': 'DIVERSIFIED', 'IEX': 'DIVERSIFIED',
        }
    
    def search_scrip(self, symbol: str) -> Dict:
        """
        Search for a symbol using Angel One's searchScrip API
        Returns token and trading symbol
        """
        try:
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/searchScrip"
            
            headers = {
                'Authorization': f'Bearer {self.jwt_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
                'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
                'X-MACAddress': 'MAC_ADDRESS',
                'X-PrivateKey': self.api_key
            }
            
            payload = {
                "exchange": "NSE",
                "searchscrip": symbol
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    # Find exact match for EQ segment
                    for item in data['data']:
                        if item['symbol'].startswith(symbol) and item['symbol'].endswith('-EQ'):
                            return {
                                'symbol': item['symbol'],
                                'token': item['symboltoken'],
                                'name': item.get('name', symbol)
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching {symbol}: {e}")
            return None
    
    def fetch_nifty_200_list(self) -> List[Dict]:
        """
        Fetch complete Nifty 200 constituent list
        
        In production, this would fetch from NSE India website
        For now, using curated list
        """
        # Complete Nifty 200 symbols (alphabetically)
        nifty_200_symbols = [
            'ABB', 'ACC', 'ABFRL', 'ADANIENT', 'ADANIGREEN', 'ADANIPORTS', 'ADANIPOWER',
            'ADANITRANS', 'ALKEM', 'AMBUJACEM', 'APOLLOHOSP', 'APOLLOTYRE', 'ASHOKLEY',
            'ASIANPAINT', 'ASTRAL', 'ATUL', 'AUROPHARMA', 'AXISBANK', 'BAJAJ-AUTO',
            'BAJAJFINSV', 'BAJFINANCE', 'BAJAJHLDNG', 'BALKRISIND', 'BANDHANBNK',
            'BANKBARODA', 'BATAINDIA', 'BEL', 'BERGEPAINT', 'BHARATFORG', 'BHARTIARTL',
            'BHEL', 'BIOCON', 'BOSCHLTD', 'BPCL', 'BRITANNIA', 'BSOFT', 'CANBK',
            'CANFINHOME', 'CHAMBLFERT', 'CHOLAFIN', 'CIPLA', 'COALINDIA', 'COFORGE',
            'COLPAL', 'CONCOR', 'COROMANDEL', 'CROMPTON', 'CUMMINSIND', 'DABUR',
            'DALBHARAT', 'DEEPAKNTR', 'DIVISLAB', 'DIXON', 'DLF', 'DRREDDY', 'EICHERMOT',
            'EXIDEIND', 'FEDERALBNK', 'FORTIS', 'GAIL', 'GLENMARK', 'GMRINFRA', 'GNFC',
            'GODREJCP', 'GODREJPROP', 'GRANULES', 'GRASIM', 'GUJGASLTD', 'HAL',
            'HAVELLS', 'HCLTECH', 'HDFCAMC', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO',
            'HINDALCO', 'HINDCOPPER', 'HINDPETRO', 'HINDUNILVR', 'ICICIBANK', 'ICICIGI',
            'ICICIPRULI', 'IDEA', 'IDFCFIRSTB', 'IEX', 'IGL', 'INDHOTEL', 'INDIACEM',
            'INDIAMART', 'INDIGO', 'INDUSINDBK', 'INDUSTOWER', 'INFY', 'IOC', 'IPCALAB',
            'ITC', 'JINDALSTEL', 'JKCEMENT', 'JSWSTEEL', 'JUBLFOOD', 'KOTAKBANK',
            'L&TFH', 'LALPATHLAB', 'LAURUSLABS', 'LICHSGFIN', 'LT', 'LTIM', 'LTTS',
            'LUPIN', 'M&M', 'M&MFIN', 'MANAPPURAM', 'MARICO', 'MARUTI', 'MAXHEALTH',
            'MCDOWELL-N', 'METROPOLIS', 'MFSL', 'MGL', 'MOTHERSON', 'MPHASIS', 'MRF',
            'MUTHOOTFIN', 'NATIONALUM', 'NAUKRI', 'NAVINFLUOR', 'NESTLEIND', 'NMDC',
            'NTPC', 'OBEROIRLTY', 'OFSS', 'ONGC', 'PAGEIND', 'PEL', 'PERSISTENT',
            'PETRONET', 'PFC', 'PHOENIXLTD', 'PIDILITIND', 'PIIND', 'PNB', 'POLYCAB',
            'POWERGRID', 'PVRINOX', 'RAIN', 'RAJESHEXPO', 'RAMCOCEM', 'RBLBANK',
            'RECLTD', 'RELIANCE', 'SAIL', 'SBICARD', 'SBILIFE', 'SBIN', 'SHREECEM',
            'SHRIRAMFIN', 'SIEMENS', 'SRF', 'SUNPHARMA', 'SUNTV', 'SYNGENE', 'TATACHEM',
            'TATACOMM', 'TATACONSUM', 'TATAMOTORS', 'TATAPOWER', 'TATASTEEL', 'TCS',
            'TECHM', 'TITAN', 'TORNTPHARM', 'TORNTPOWER', 'TRENT', 'TVSMOTOR', 'UBL',
            'ULTRACEMCO', 'UPL', 'VEDL', 'VOLTAS', 'WHIRLPOOL', 'WIPRO', 'YESBANK',
            'ZEEL', 'ZYDUSLIFE'
        ]
        
        logger.info(f"📊 Fetching tokens for {len(nifty_200_symbols)} Nifty 200 symbols...")
        
        constituents = []
        
        for i, symbol in enumerate(nifty_200_symbols, 1):
            result = self.search_scrip(symbol)
            
            if result:
                # Get sector from mapping
                base_symbol = symbol.replace('-', '&')  # Handle M&M, L&TFH, etc.
                sector = self.SECTOR_MAPPING.get(base_symbol, 'OTHER')
                
                constituents.append({
                    'symbol': result['symbol'],
                    'token': result['token'],
                    'name': result['name'],
                    'sector': sector,
                    'rank': i  # Market cap rank (approximate)
                })
                
                logger.info(f"   ✅ {i:3d}. {result['symbol']:<20} Token: {result['token']:<8} Sector: {sector}")
            else:
                logger.warning(f"   ❌ {i:3d}. {symbol:<20} NOT FOUND")
        
        logger.info(f"\n✅ Successfully fetched {len(constituents)}/{len(nifty_200_symbols)} symbols")
        
        return constituents
    
    def save_to_json(self, constituents: List[Dict], filename: str = 'nifty200_constituents.json'):
        """Save constituents to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(constituents, f, indent=2)
            
            logger.info(f"✅ Saved {len(constituents)} constituents to {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving to JSON: {e}")
    
    def load_from_json(self, filename: str = 'nifty200_constituents.json') -> List[Dict]:
        """Load constituents from JSON file"""
        try:
            with open(filename, 'r') as f:
                constituents = json.load(f)
            
            logger.info(f"✅ Loaded {len(constituents)} constituents from {filename}")
            return constituents
            
        except FileNotFoundError:
            logger.warning(f"⚠️ File {filename} not found")
            return []
        except Exception as e:
            logger.error(f"❌ Error loading from JSON: {e}")
            return []


def main():
    """Fetch and save Nifty 200 constituents"""
    print("\n" + "=" * 80)
    print("NIFTY 200 SYMBOL & TOKEN MANAGER")
    print("=" * 80)
    print("\nEnter your Angel One credentials:")
    
    client_code = input("Client Code: ").strip()
    password = input("Password/MPIN: ").strip()
    totp = input("TOTP Code: ").strip()
    api_key = input("API Key: ").strip()
    
    # Authenticate
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
            jwt_token = data['data']['jwtToken']
            print("✅ Authentication successful!\n")
        else:
            print("❌ Authentication failed")
            return
    else:
        print("❌ Authentication failed")
        return
    
    # Create manager and fetch constituents
    manager = Nifty200Manager(api_key, jwt_token)
    
    print("Fetching Nifty 200 constituents...")
    print("This will take ~2-3 minutes...\n")
    
    constituents = manager.fetch_nifty_200_list()
    
    # Save to JSON
    manager.save_to_json(constituents)
    
    # Print summary by sector
    print("\n" + "=" * 80)
    print("SECTOR DISTRIBUTION")
    print("=" * 80)
    
    sector_counts = {}
    for c in constituents:
        sector = c['sector']
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
    
    for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{sector:<25} {count:3d} stocks")
    
    print("\n" + "=" * 80)
    print(f"✅ Total: {len(constituents)} stocks ready for screening")
    print("=" * 80)


if __name__ == "__main__":
    main()
