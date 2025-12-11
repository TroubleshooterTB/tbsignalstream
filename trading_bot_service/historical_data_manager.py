"""
Historical Data Management
Fetch, store, and manage historical market data from Angel One
"""

import pandas as pd
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from firebase_admin import firestore
import logging

logger = logging.getLogger(__name__)


def _get_db():
    """Get Firestore client (lazy initialization)"""
    return firestore.client()


class HistoricalDataManager:
    """
    Manages historical market data fetching and storage.
    """
    
    def __init__(self, api_key: str, jwt_token: str):
        """
        Initialize Historical Data Manager.
        
        Args:
            api_key: Angel One API key
            jwt_token: User's JWT token
        """
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.base_url = "https://apiconnect.angelone.in"
        
    def _get_headers(self) -> Dict:
        """Get API request headers"""
        return {
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': '127.0.0.1',
            'X-ClientPublicIP': '127.0.0.1',
            'X-MACAddress': '00:00:00:00:00:00',
            'X-PrivateKey': self.api_key
        }
    
    def fetch_historical_data(
        self,
        symbol: str,
        token: str,
        exchange: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
        max_retries: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical candle data from Angel One with retry logic.
        
        Angel One Rate Limits (per client_code):
        - 3 requests/second
        - 180 requests/minute
        - 5000 requests/day
        
        Args:
            symbol: Trading symbol
            token: Symbol token
            exchange: Exchange (NSE/BSE)
            interval: Timeframe (ONE_MINUTE, FIVE_MINUTE, ONE_DAY, etc.)
            from_date: Start date
            to_date: End date
            max_retries: Maximum retry attempts for rate limit errors (default: 3)
            
        Returns:
            DataFrame with OHLCV data or None
        """
        import time
        
        url = f"{self.base_url}/rest/secure/angelbroking/historical/v1/getCandleData"
        
        payload = {
            "exchange": exchange,
            "symboltoken": str(token),
            "interval": interval,
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M")
        }
        
        logger.info(f"Fetching historical data for {symbol} ({interval})")
        
        # Retry loop for rate limiting (403 errors)
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                
                # Check for rate limit (403) - retry with exponential backoff
                if response.status_code == 403:
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        wait_time = 2 ** attempt
                        logger.warning(f"{symbol}: Rate limit hit (403), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"{symbol}: Rate limit exceeded after {max_retries} attempts")
                        return None
                
                response.raise_for_status()
                result = response.json()
                
                # CRITICAL FIX: Angel One returns {"status": true, "message": "SUCCESS", "data": null}
                # when no data is available (e.g., before market open). We need to check data is not null/empty.
                data = result.get('data')
                
                if result.get('status') and data is not None and len(data) > 0:
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    
                    # Convert to numeric
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col])
                    
                    # CRITICAL FIX: Capitalize column names for pattern detector compatibility
                    # Pattern detector expects: 'Open', 'High', 'Low', 'Close', 'Volume'
                    df.columns = [col.capitalize() for col in df.columns]
                    
                    logger.info(f"✅ Fetched {len(df)} candles for {symbol}")
                    return df
                else:
                    # Don't log as ERROR - this is EXPECTED before market open or for invalid date ranges
                    msg = result.get('message', 'No data available')
                    logger.debug(f"{symbol}: {msg} (data={data})")
                    return None
                    
            except requests.exceptions.HTTPError as e:
                # HTTP errors other than 403 (already handled above)
                logger.error(f"{symbol}: HTTP error: {e}")
                return None
            except Exception as e:
                logger.error(f"{symbol}: Error fetching historical data: {e}")
                return None
        
        # Should not reach here, but return None if we do
        return None
    
    def store_to_firestore(
        self,
        symbol: str,
        interval: str,
        data: pd.DataFrame
    ):
        """
        Store historical data to Firestore.
        
        Args:
            symbol: Stock symbol
            interval: Timeframe
            data: OHLCV DataFrame
        """
        try:
            collection_name = f"historical_data_{interval}"
            doc_ref = _get_db().collection(collection_name).document(symbol)
            
            # Convert DataFrame to dict
            data_dict = data.reset_index().to_dict('records')
            
            # Store in batches (Firestore has size limits)
            batch_size = 100
            for i in range(0, len(data_dict), batch_size):
                batch = data_dict[i:i+batch_size]
                doc_ref.collection('candles').add({
                    'data': batch,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
            
            logger.info(f"Stored {len(data_dict)} candles for {symbol}")
            
        except Exception as e:
            logger.error(f"Error storing data to Firestore: {e}")
    
    def load_from_firestore(
        self,
        symbol: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """
        Load historical data from Firestore.
        
        Args:
            symbol: Stock symbol
            interval: Timeframe
            
            Returns:
            DataFrame or None
        """
        try:
            collection_name = f"historical_data_{interval}"
            doc_ref = _get_db().collection(collection_name).document(symbol)            # Get all candle documents
            candles_docs = doc_ref.collection('candles').stream()
            
            all_data = []
            for doc in candles_docs:
                data = doc.to_dict().get('data', [])
                all_data.extend(data)
            
            if not all_data:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"Loaded {len(df)} candles for {symbol} from Firestore")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data from Firestore: {e}")
            return None
    
    def get_or_fetch_data(
        self,
        symbol: str,
        token: str,
        exchange: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Get data from cache or fetch if not available.
        
        Args:
            symbol: Stock symbol
            token: Symbol token
            exchange: Exchange
            interval: Timeframe
            from_date: Start date
            to_date: End date
            force_refresh: Force fetch from API
            
        Returns:
            DataFrame or None
        """
        if not force_refresh:
            # Try to load from Firestore
            cached_data = self.load_from_firestore(symbol, interval)
            if cached_data is not None:
                # Filter by date range
                mask = (cached_data.index >= from_date) & (cached_data.index <= to_date)
                filtered = cached_data[mask]
                if len(filtered) > 0:
                    return filtered
        
        # Fetch from API
        data = self.fetch_historical_data(
            symbol, token, exchange, interval, from_date, to_date
        )
        
        if data is not None:
            # Store for future use
            self.store_to_firestore(symbol, interval, data)
        
        return data
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate common technical indicators.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with indicators
        """
        df = data.copy()
        
        # Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # RSI - prevent division by zero
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 1e-10)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        
        return df
