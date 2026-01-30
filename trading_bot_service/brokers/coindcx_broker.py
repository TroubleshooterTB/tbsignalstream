"""
CoinDCX Broker Connector
========================
Handles all REST API interactions with CoinDCX exchange.

Features:
- HMAC SHA256 authentication
- Automatic retry with exponential backoff
- Rate limit handling
- Error handling and logging
- Support for BTC and ETH trading
"""

import hmac
import hashlib
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CoinDCXBroker:
    """CoinDCX broker connector for cryptocurrency trading"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize CoinDCX broker connector.
        
        Args:
            api_key: CoinDCX API key
            api_secret: CoinDCX API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.coindcx.com"
        self.public_url = "https://public.coindcx.com"
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.01  # 10ms between requests
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        logger.info("✅ CoinDCX broker initialized")
    
    def _generate_signature(self, body: Dict) -> str:
        """
        Generate HMAC SHA256 signature for authentication.
        
        Args:
            body: Request body dictionary
            
        Returns:
            Hexadecimal signature string
        """
        secret_bytes = bytes(self.api_secret, encoding='utf-8')
        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(
            secret_bytes,
            json_body.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                 authenticated: bool = True, use_public_url: bool = False) -> Any:
        """
        Make HTTP request to CoinDCX API with retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            params: Request parameters
            authenticated: Whether authentication is required
            use_public_url: Use public URL instead of base URL
            
        Returns:
            JSON response data
            
        Raises:
            Exception: If request fails after all retries
        """
        self._rate_limit()
        
        # Prepare request
        base = self.public_url if use_public_url else self.base_url
        url = f"{base}{endpoint}"
        body = params or {}
        
        # Add timestamp for authenticated requests
        if authenticated:
            body['timestamp'] = int(time.time() * 1000)
        
        # Retry loop
        for attempt in range(1, self.max_retries + 1):
            try:
                if authenticated:
                    # Generate signature
                    signature = self._generate_signature(body)
                    headers = {
                        'X-AUTH-APIKEY': self.api_key,
                        'X-AUTH-SIGNATURE': signature
                    }
                    response = self.session.post(url, json=body, headers=headers, timeout=10)
                else:
                    # Public endpoint
                    if method == 'GET':
                        response = self.session.get(url, params=body, timeout=10)
                    else:
                        response = self.session.post(url, json=body, timeout=10)
                
                # Check response
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error("❌ Authentication failed - check API credentials")
                    raise Exception("Authentication failed - Invalid API key or secret")
                elif response.status_code == 429:
                    logger.warning(f"⚠️  Rate limit hit - waiting {self.retry_delay * attempt}s")
                    time.sleep(self.retry_delay * attempt)
                    continue
                else:
                    logger.error(f"❌ API error {response.status_code}: {response.text}")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    raise Exception(f"API request failed: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️  Request timeout (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                raise Exception("Request timeout after retries")
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)
                    continue
                raise Exception("Connection error after retries")
                
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                raise
        
        raise Exception(f"Request failed after {self.max_retries} retries")
    
    # ========================================
    # MARKET DATA METHODS (Public)
    # ========================================
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data for symbol.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            Ticker data with bid, ask, last price, volume, etc.
        """
        try:
            endpoint = "/exchange/ticker"
            data = self._request('GET', endpoint, authenticated=False)
            
            # Find the specific symbol
            for ticker in data:
                if ticker.get('market') == symbol:
                    return ticker
            
            logger.warning(f"⚠️  Symbol {symbol} not found in ticker data")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get ticker for {symbol}: {e}")
            raise
    
    def get_all_tickers(self) -> List[Dict]:
        """Get ticker data for all trading pairs"""
        try:
            endpoint = "/exchange/ticker"
            return self._request('GET', endpoint, authenticated=False)
        except Exception as e:
            logger.error(f"❌ Failed to get all tickers: {e}")
            raise
    
    def get_market_details(self) -> List[Dict]:
        """Get detailed information about all markets"""
        try:
            endpoint = "/exchange/v1/markets_details"
            return self._request('GET', endpoint, authenticated=False)
        except Exception as e:
            logger.error(f"❌ Failed to get market details: {e}")
            raise
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """
        Get orderbook for symbol.
        
        Args:
            symbol: Trading pair in CoinDCX format (e.g., "B-BTC_USDT")
            depth: Depth level (10, 20, or 50)
            
        Returns:
            Orderbook with bids and asks
        """
        try:
            endpoint = f"/market_data/orderbook"
            params = {'pair': symbol}
            return self._request('GET', endpoint, params=params, 
                               authenticated=False, use_public_url=True)
        except Exception as e:
            logger.error(f"❌ Failed to get orderbook for {symbol}: {e}")
            raise
    
    def get_historical_candles(self, symbol: str, interval: str, 
                              limit: int = 500) -> List[Dict]:
        """
        Get historical candlestick data.
        
        Args:
            symbol: Trading pair in CoinDCX format (e.g., "B-BTC_USDT")
            interval: Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)
            limit: Number of candles (max 1000)
            
        Returns:
            List of candle data
        """
        try:
            endpoint = "/market_data/candles"
            params = {
                'pair': symbol,
                'interval': interval,
                'limit': min(limit, 1000)
            }
            return self._request('GET', endpoint, params=params,
                               authenticated=False, use_public_url=True)
        except Exception as e:
            logger.error(f"❌ Failed to get candles for {symbol}: {e}")
            raise
    
    def get_trade_history(self, symbol: str, limit: int = 50) -> List[Dict]:
        """
        Get recent trade history for symbol.
        
        Args:
            symbol: Trading pair in CoinDCX format
            limit: Number of trades (max 500)
            
        Returns:
            List of recent trades
        """
        try:
            endpoint = "/market_data/trade_history"
            params = {
                'pair': symbol,
                'limit': min(limit, 500)
            }
            return self._request('GET', endpoint, params=params,
                               authenticated=False, use_public_url=True)
        except Exception as e:
            logger.error(f"❌ Failed to get trade history for {symbol}: {e}")
            raise
    
    # ========================================
    # ACCOUNT METHODS (Private)
    # ========================================
    
    def get_balance(self) -> List[Dict]:
        """
        Get account balances for all currencies.
        
        Returns:
            List of balances with currency, balance, and locked_balance
        """
        try:
            endpoint = "/exchange/v1/users/balances"
            return self._request('POST', endpoint)
        except Exception as e:
            logger.error(f"❌ Failed to get balance: {e}")
            raise
    
    def get_balance_by_currency(self, currency: str) -> Dict:
        """
        Get balance for specific currency.
        
        Args:
            currency: Currency code (e.g., "BTC", "USDT")
            
        Returns:
            Balance data with available and locked amounts
        """
        try:
            balances = self.get_balance()
            for balance in balances:
                if balance.get('currency') == currency:
                    return balance
            
            logger.warning(f"⚠️  Currency {currency} not found in balance")
            return {'currency': currency, 'balance': 0, 'locked_balance': 0}
            
        except Exception as e:
            logger.error(f"❌ Failed to get balance for {currency}: {e}")
            raise
    
    def get_user_info(self) -> Dict:
        """Get user account information"""
        try:
            endpoint = "/exchange/v1/users/info"
            return self._request('POST', endpoint)
        except Exception as e:
            logger.error(f"❌ Failed to get user info: {e}")
            raise
    
    # ========================================
    # TRADING METHODS (Private)
    # ========================================
    
    def place_order(self, symbol: str, side: str, order_type: str,
                   quantity: float, price: Optional[float] = None,
                   client_order_id: Optional[str] = None) -> Dict:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: Order side ("buy" or "sell")
            order_type: Order type ("market_order", "limit_order", "stop_limit")
            quantity: Order quantity
            price: Limit price (required for limit orders)
            client_order_id: Custom order ID for tracking
            
        Returns:
            Order response with order ID and details
        """
        try:
            endpoint = "/exchange/v1/orders/create"
            params = {
                'market': symbol,
                'side': side,
                'order_type': order_type,
                'total_quantity': quantity
            }
            
            if price is not None:
                params['price_per_unit'] = price
            
            if client_order_id:
                params['client_order_id'] = client_order_id
            
            response = self._request('POST', endpoint, params)
            
            logger.info(f"✅ Order placed: {side} {quantity} {symbol} @ {price or 'MARKET'}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to place order: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an open order"""
        try:
            endpoint = "/exchange/v1/orders/cancel"
            params = {'id': order_id}
            response = self._request('POST', endpoint, params)
            
            logger.info(f"✅ Order cancelled: {order_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel order {order_id}: {e}")
            raise
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get status of specific order"""
        try:
            endpoint = "/exchange/v1/orders/status"
            params = {'id': order_id}
            return self._request('POST', endpoint, params)
        except Exception as e:
            logger.error(f"❌ Failed to get order status for {order_id}: {e}")
            raise
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all active orders.
        
        Args:
            symbol: Filter by trading pair (optional)
            
        Returns:
            List of active orders
        """
        try:
            endpoint = "/exchange/v1/orders/active_orders"
            params = {}
            if symbol:
                params['market'] = symbol
            
            return self._request('POST', endpoint, params)
            
        except Exception as e:
            logger.error(f"❌ Failed to get active orders: {e}")
            raise
    
    def get_order_history(self, symbol: Optional[str] = None,
                         limit: int = 100) -> List[Dict]:
        """
        Get order history.
        
        Args:
            symbol: Filter by trading pair (optional)
            limit: Number of orders to return (max 5000)
            
        Returns:
            List of historical orders
        """
        try:
            endpoint = "/exchange/v1/orders/trade_history"
            params = {'limit': min(limit, 5000)}
            if symbol:
                params['symbol'] = symbol
            
            return self._request('POST', endpoint, params)
            
        except Exception as e:
            logger.error(f"❌ Failed to get order history: {e}")
            raise
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> Dict:
        """
        Cancel all open orders.
        
        Args:
            symbol: Cancel orders for specific pair only (optional)
            
        Returns:
            Cancellation response
        """
        try:
            endpoint = "/exchange/v1/orders/cancel_all"
            params = {}
            if symbol:
                params['market'] = symbol
            
            response = self._request('POST', endpoint, params)
            logger.info(f"✅ All orders cancelled for {symbol or 'all pairs'}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel all orders: {e}")
            raise
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """
        Get detailed information about a trading symbol.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            Symbol info with min/max quantities, prices, etc.
        """
        try:
            markets = self.get_market_details()
            for market in markets:
                if market.get('coindcx_name') == symbol:
                    return market
            
            logger.warning(f"⚠️  Symbol {symbol} not found in market details")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get symbol info for {symbol}: {e}")
            raise
    
    def format_pair_for_websocket(self, symbol: str) -> str:
        """
        Convert symbol to WebSocket format.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            WebSocket format (e.g., "B-BTC_USDT")
        """
        # Get market details to find the 'pair' field
        try:
            info = self.get_symbol_info(symbol)
            return info.get('pair', f"B-{symbol[:3]}_{symbol[3:]}")
        except:
            # Fallback: simple conversion
            if '_' not in symbol:
                # BTCUSDT -> B-BTC_USDT
                return f"B-{symbol[:3]}_{symbol[3:]}"
            return symbol
    
    def validate_order_params(self, symbol: str, quantity: float,
                             price: Optional[float] = None) -> bool:
        """
        Validate order parameters against symbol requirements.
        
        Args:
            symbol: Trading pair
            quantity: Order quantity
            price: Order price (optional)
            
        Returns:
            True if valid, raises Exception if invalid
        """
        try:
            info = self.get_symbol_info(symbol)
            
            if not info:
                raise Exception(f"Symbol {symbol} not found")
            
            # Check quantity limits
            min_qty = float(info.get('min_quantity', 0))
            max_qty = float(info.get('max_quantity', float('inf')))
            
            if quantity < min_qty:
                raise Exception(f"Quantity {quantity} below minimum {min_qty}")
            
            if quantity > max_qty:
                raise Exception(f"Quantity {quantity} above maximum {max_qty}")
            
            # Check price limits (if price provided)
            if price is not None:
                min_price = float(info.get('min_price', 0))
                max_price = float(info.get('max_price', float('inf')))
                
                if price < min_price:
                    raise Exception(f"Price {price} below minimum {min_price}")
                
                if price > max_price:
                    raise Exception(f"Price {price} above maximum {max_price}")
                
                # Check min notional (min order value)
                min_notional = float(info.get('min_notional', 0))
                order_value = quantity * price
                
                if order_value < min_notional:
                    raise Exception(
                        f"Order value {order_value} below minimum {min_notional}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Order validation failed: {e}")
            raise
    
    def __repr__(self):
        return f"CoinDCXBroker(api_key={self.api_key[:8]}...)"
