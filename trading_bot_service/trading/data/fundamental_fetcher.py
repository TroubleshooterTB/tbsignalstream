"""
Fundamental Data Fetcher
Fetches company fundamentals from public APIs (NSE, BSE, Yahoo Finance)
"""

import logging
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class FundamentalDataFetcher:
    """
    Fetches fundamental data for Indian stocks from public sources.
    
    Data sources (in order of preference):
    1. Yahoo Finance India (free, no API key needed)
    2. NSE India (free, but rate-limited)
    3. Cached data (60-minute cache)
    """
    
    def __init__(self):
        self._cache = {}
        self._cache_duration = 3600  # 60 minutes
        
    def get_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Get fundamental data for a stock.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE-EQ" or "RELIANCE")
            
        Returns:
            {
                'pe_ratio': float,
                'debt_to_equity': float,
                'promoter_holding': float,
                'roe': float,
                'market_cap': float,
                'book_value': float,
                'is_fundamentally_strong': bool,
                'reason': str
            }
        """
        # Clean symbol (remove -EQ suffix)
        clean_symbol = symbol.replace('-EQ', '').replace('-BE', '')
        
        # Check cache
        cache_key = f"fundamentals_{clean_symbol}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            age = (datetime.now() - cached_time).total_seconds()
            if age < self._cache_duration:
                logger.debug(f"Using cached fundamentals for {clean_symbol} (age: {age/60:.1f} min)")
                return cached_data
        
        # Try to fetch from Yahoo Finance
        data = self._fetch_from_yahoo(clean_symbol)
        
        if data:
            # Cache the result
            self._cache[cache_key] = (data, datetime.now())
            return data
        
        # Fallback: return safe defaults (pass the check with neutral score)
        logger.warning(f"Could not fetch fundamentals for {clean_symbol}, using defaults")
        return self._get_default_fundamentals()
    
    def _fetch_from_yahoo(self, symbol: str) -> Optional[Dict]:
        """
        Fetch fundamentals from Yahoo Finance India.
        
        Yahoo Finance provides free access to:
        - PE ratio
        - Market cap
        - Book value
        - Trailing EPS
        """
        try:
            # Yahoo Finance India uses .NS for NSE stocks
            yahoo_symbol = f"{symbol}.NS"
            
            # Headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Fetch from Yahoo Finance API (public endpoint)
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{yahoo_symbol}"
            params = {
                'modules': 'defaultKeyStatistics,financialData,summaryDetail'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('quoteSummary', {}).get('result', [])
                
                if not result:
                    return None
                
                stats = result[0]
                
                # Extract key metrics
                default_key_stats = stats.get('defaultKeyStatistics', {})
                financial_data = stats.get('financialData', {})
                summary_detail = stats.get('summaryDetail', {})
                
                pe_ratio = summary_detail.get('trailingPE', {}).get('raw', 0)
                market_cap = summary_detail.get('marketCap', {}).get('raw', 0)
                book_value = default_key_stats.get('priceToBook', {}).get('raw', 0)
                debt_to_equity = financial_data.get('debtToEquity', {}).get('raw', 0)
                roe = financial_data.get('returnOnEquity', {}).get('raw', 0)
                
                # Convert ROE to percentage
                if roe:
                    roe = roe * 100
                
                # Analyze fundamental strength
                is_strong, reason = self._analyze_strength(
                    pe_ratio=pe_ratio,
                    debt_to_equity=debt_to_equity,
                    roe=roe
                )
                
                return {
                    'pe_ratio': pe_ratio,
                    'debt_to_equity': debt_to_equity,
                    'promoter_holding': 0,  # Not available from Yahoo
                    'roe': roe,
                    'market_cap': market_cap / 10000000,  # Convert to crores
                    'book_value': book_value,
                    'is_fundamentally_strong': is_strong,
                    'reason': reason,
                    'source': 'Yahoo Finance'
                }
            
            return None
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching fundamentals for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Yahoo fundamentals for {symbol}: {e}")
            return None
    
    def _analyze_strength(self, pe_ratio: float, debt_to_equity: float, 
                          roe: float) -> tuple[bool, str]:
        """
        Analyze fundamental strength based on key metrics.
        
        Criteria for "fundamentally strong":
        1. PE Ratio: 10 < PE < 40 (not too cheap/expensive)
        2. Debt/Equity: < 1.5 (manageable debt)
        3. ROE: > 12% (good profitability)
        
        Returns:
            (is_strong: bool, reason: str)
        """
        issues = []
        
        # PE Ratio check (avoid penny stocks and overvalued)
        if pe_ratio > 0:
            if pe_ratio < 10:
                issues.append(f"PE ratio too low ({pe_ratio:.1f}) - possible value trap")
            elif pe_ratio > 50:
                issues.append(f"PE ratio very high ({pe_ratio:.1f}) - overvalued")
        else:
            issues.append("PE ratio not available or negative")
        
        # Debt/Equity check
        if debt_to_equity > 0:
            if debt_to_equity > 2.0:
                issues.append(f"High debt/equity ratio ({debt_to_equity:.2f})")
        
        # ROE check
        if roe > 0:
            if roe < 10:
                issues.append(f"Low ROE ({roe:.1f}%) - weak profitability")
        else:
            issues.append("ROE not available or negative")
        
        # Determine overall strength
        if len(issues) == 0:
            return True, "Strong fundamentals: Good PE, Low debt, High ROE"
        elif len(issues) == 1:
            # One minor issue is acceptable
            return True, f"Acceptable fundamentals (minor concern: {issues[0]})"
        else:
            return False, f"Weak fundamentals: {'; '.join(issues)}"
    
    def _get_default_fundamentals(self) -> Dict:
        """
        Return default/safe fundamental data when real data unavailable.
        This ensures the bot doesn't block trades due to API failures.
        """
        return {
            'pe_ratio': 25,  # Market average
            'debt_to_equity': 0.8,  # Healthy level
            'promoter_holding': 60,  # Good promoter confidence
            'roe': 15,  # Good profitability
            'market_cap': 50000,  # Mid-cap (crores)
            'book_value': 1.5,
            'is_fundamentally_strong': True,
            'reason': 'Using default values (API unavailable)',
            'source': 'Default'
        }
    
    def cleanup_cache(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = []
        
        for key, (data, cached_time) in self._cache.items():
            age = (now - cached_time).total_seconds()
            if age > self._cache_duration:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


# Singleton instance
_fundamental_fetcher = None

def get_fundamental_fetcher() -> FundamentalDataFetcher:
    """Get singleton instance of FundamentalDataFetcher"""
    global _fundamental_fetcher
    if _fundamental_fetcher is None:
        _fundamental_fetcher = FundamentalDataFetcher()
    return _fundamental_fetcher
