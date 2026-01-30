"""
CoinDCX WebSocket Manager
=========================
Real-time data streaming from CoinDCX using Socket.IO.

Features:
- Real-time price updates
- Orderbook streaming
- Trade stream
- Account updates (balance, orders)
- Auto-reconnection with exponential backoff
- Connection health monitoring
"""

import socketio
import asyncio
import logging
import hmac
import hashlib
import json
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class CoinDCXWebSocket:
    """Real-time WebSocket connection to CoinDCX"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize WebSocket manager.
        
        Args:
            api_key: CoinDCX API key (optional, for private channels)
            api_secret: CoinDCX API secret (optional, for private channels)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws_url = 'wss://stream.coindcx.com'
        
        # Socket.IO client
        self.sio = socketio.AsyncClient(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=10,
            reconnection_delay=1,
            reconnection_delay_max=60
        )
        
        # Connection state
        self.is_connected = False
        self.is_authenticated = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # Data storage
        self.latest_prices = {}  # {symbol: price}
        self.orderbooks = {}  # {symbol: {bids, asks}}
        self.trades = []  # Recent trades
        self.balances = {}  # Account balances
        
        # Subscriptions
        self.subscribed_channels = set()
        
        # Callbacks
        self.on_price_callback = None
        self.on_orderbook_callback = None
        self.on_trade_callback = None
        self.on_balance_callback = None
        self.on_order_callback = None
        
        # Setup event handlers
        self._setup_handlers()
        
        # Health monitoring
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 25  # Send ping every 25 seconds
        
        logger.info("✅ CoinDCX WebSocket initialized")
    
    def _setup_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect():
            """Handle connection event"""
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("🔌 WebSocket connected!")
            
            # Authenticate if credentials provided
            if self.api_key and self.api_secret:
                await self._authenticate()
            
            # Re-subscribe to channels
            await self._resubscribe_all()
        
        @self.sio.event
        async def disconnect():
            """Handle disconnection event"""
            self.is_connected = False
            self.is_authenticated = False
            logger.warning("🔴 WebSocket disconnected")
        
        @self.sio.event
        async def connect_error(data):
            """Handle connection error"""
            logger.error(f"❌ WebSocket connection error: {data}")
            self.reconnect_attempts += 1
            
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error("❌ Max reconnection attempts reached")
        
        # ========================================
        # PUBLIC CHANNEL HANDLERS
        # ========================================
        
        @self.sio.on('price-change')
        async def on_price_change(data):
            """Handle price update"""
            try:
                symbol = data.get('s', '')
                price = float(data.get('p', 0))
                timestamp = data.get('T', time.time())
                
                # Store latest price
                self.latest_prices[symbol] = {
                    'price': price,
                    'timestamp': timestamp
                }
                
                # Call callback if set
                if self.on_price_callback:
                    await self.on_price_callback(symbol, price, timestamp)
                    
            except Exception as e:
                logger.error(f"❌ Error processing price update: {e}")
        
        @self.sio.on('depth-snapshot')
        async def on_depth_snapshot(data):
            """Handle orderbook snapshot"""
            try:
                symbol = data.get('s', '')
                bids = data.get('bids', {})
                asks = data.get('asks', {})
                
                # Store orderbook
                self.orderbooks[symbol] = {
                    'bids': bids,
                    'asks': asks,
                    'timestamp': time.time()
                }
                
                # Call callback if set
                if self.on_orderbook_callback:
                    await self.on_orderbook_callback(symbol, bids, asks)
                    
            except Exception as e:
                logger.error(f"❌ Error processing orderbook snapshot: {e}")
        
        @self.sio.on('depth-update')
        async def on_depth_update(data):
            """Handle orderbook update"""
            try:
                symbol = data.get('s', '')
                
                # Update existing orderbook
                if symbol in self.orderbooks:
                    if 'bids' in data:
                        self.orderbooks[symbol]['bids'].update(data['bids'])
                    if 'asks' in data:
                        self.orderbooks[symbol]['asks'].update(data['asks'])
                    self.orderbooks[symbol]['timestamp'] = time.time()
                    
                    # Call callback if set
                    if self.on_orderbook_callback:
                        await self.on_orderbook_callback(
                            symbol,
                            self.orderbooks[symbol]['bids'],
                            self.orderbooks[symbol]['asks']
                        )
                        
            except Exception as e:
                logger.error(f"❌ Error processing orderbook update: {e}")
        
        @self.sio.on('new-trade')
        async def on_new_trade(data):
            """Handle new trade"""
            try:
                trade = {
                    'symbol': data.get('s', ''),
                    'price': float(data.get('p', 0)),
                    'quantity': float(data.get('q', 0)),
                    'timestamp': data.get('T', time.time()),
                    'is_buyer_maker': data.get('m', False)
                }
                
                # Store trade (keep last 1000)
                self.trades.append(trade)
                if len(self.trades) > 1000:
                    self.trades.pop(0)
                
                # Call callback if set
                if self.on_trade_callback:
                    await self.on_trade_callback(trade)
                    
            except Exception as e:
                logger.error(f"❌ Error processing trade: {e}")
        
        @self.sio.on('candlestick')
        async def on_candlestick(data):
            """Handle candlestick update"""
            # Not actively used, but captured for completeness
            pass
        
        # ========================================
        # PRIVATE CHANNEL HANDLERS (Authenticated)
        # ========================================
        
        @self.sio.on('balance-update')
        async def on_balance_update(data):
            """Handle balance update"""
            try:
                if isinstance(data, list):
                    for balance_item in data:
                        currency = balance_item.get('currency_short_name', '')
                        available = float(balance_item.get('balance', 0))
                        locked = float(balance_item.get('locked_balance', 0))
                        
                        self.balances[currency] = {
                            'available': available,
                            'locked': locked,
                            'total': available + locked,
                            'timestamp': time.time()
                        }
                
                # Call callback if set
                if self.on_balance_callback:
                    await self.on_balance_callback(self.balances)
                    
            except Exception as e:
                logger.error(f"❌ Error processing balance update: {e}")
        
        @self.sio.on('order-update')
        async def on_order_update(data):
            """Handle order update"""
            try:
                # Call callback if set
                if self.on_order_callback:
                    await self.on_order_callback(data)
                    
            except Exception as e:
                logger.error(f"❌ Error processing order update: {e}")
        
        @self.sio.on('trade-update')
        async def on_trade_update(data):
            """Handle user's trade update"""
            # User-specific trade execution notification
            pass
    
    async def connect(self):
        """
        Connect to WebSocket server.
        
        Raises:
            Exception: If connection fails
        """
        try:
            logger.info(f"🔌 Connecting to {self.ws_url}...")
            await self.sio.connect(self.ws_url, transports='websocket')
            
            # Wait for connection to establish
            await asyncio.sleep(1)
            
            if not self.is_connected:
                raise Exception("Failed to establish connection")
            
            logger.info("✅ WebSocket connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        try:
            await self.sio.disconnect()
            self.is_connected = False
            self.is_authenticated = False
            logger.info("🔴 WebSocket disconnected")
        except Exception as e:
            logger.error(f"❌ Error during disconnect: {e}")
    
    async def _authenticate(self):
        """Authenticate for private channels"""
        try:
            if not self.api_key or not self.api_secret:
                logger.warning("⚠️  No credentials - skipping authentication")
                return
            
            # Generate signature
            secret_bytes = bytes(self.api_secret, encoding='utf-8')
            body = {"channel": "coindcx"}
            json_body = json.dumps(body, separators=(',', ':'))
            signature = hmac.new(
                secret_bytes,
                json_body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Join authenticated channel
            await self.sio.emit('join', {
                'channelName': 'coindcx',
                'authSignature': signature,
                'apiKey': self.api_key
            })
            
            self.is_authenticated = True
            logger.info("✅ WebSocket authenticated")
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
    
    async def _resubscribe_all(self):
        """Re-subscribe to all channels after reconnection"""
        if not self.subscribed_channels:
            return
        
        logger.info(f"🔄 Re-subscribing to {len(self.subscribed_channels)} channels...")
        
        for channel in self.subscribed_channels:
            try:
                await self.sio.emit('join', {'channelName': channel})
            except Exception as e:
                logger.error(f"❌ Failed to re-subscribe to {channel}: {e}")
    
    # ========================================
    # SUBSCRIPTION METHODS
    # ========================================
    
    async def subscribe_ticker(self, symbols: List[str]):
        """
        Subscribe to price updates for symbols.
        
        Args:
            symbols: List of trading pairs in WebSocket format (e.g., ["B-BTC_USDT"])
        """
        try:
            for symbol in symbols:
                channel = f"{symbol}@prices"
                await self.sio.emit('join', {'channelName': channel})
                self.subscribed_channels.add(channel)
                logger.info(f"✅ Subscribed to ticker: {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to tickers: {e}")
            raise
    
    async def subscribe_orderbook(self, symbols: List[str], depth: int = 20):
        """
        Subscribe to orderbook updates for symbols.
        
        Args:
            symbols: List of trading pairs in WebSocket format
            depth: Orderbook depth (10, 20, or 50)
        """
        try:
            for symbol in symbols:
                channel = f"{symbol}@orderbook@{depth}"
                await self.sio.emit('join', {'channelName': channel})
                self.subscribed_channels.add(channel)
                logger.info(f"✅ Subscribed to orderbook: {symbol} (depth {depth})")
                
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to orderbook: {e}")
            raise
    
    async def subscribe_trades(self, symbols: List[str]):
        """
        Subscribe to trade stream for symbols.
        
        Args:
            symbols: List of trading pairs in WebSocket format
        """
        try:
            for symbol in symbols:
                channel = f"{symbol}@trades"
                await self.sio.emit('join', {'channelName': channel})
                self.subscribed_channels.add(channel)
                logger.info(f"✅ Subscribed to trades: {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to trades: {e}")
            raise
    
    async def subscribe_candles(self, symbols: List[str], interval: str = '1m'):
        """
        Subscribe to candlestick updates for symbols.
        
        Args:
            symbols: List of trading pairs in WebSocket format
            interval: Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 8h, 1d, 3d, 1w, 1M)
        """
        try:
            for symbol in symbols:
                channel = f"{symbol}_{interval}"
                await self.sio.emit('join', {'channelName': channel})
                self.subscribed_channels.add(channel)
                logger.info(f"✅ Subscribed to candles: {symbol} ({interval})")
                
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to candles: {e}")
            raise
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from a channel"""
        try:
            await self.sio.emit('leave', {'channelName': channel})
            self.subscribed_channels.discard(channel)
            logger.info(f"✅ Unsubscribed from: {channel}")
        except Exception as e:
            logger.error(f"❌ Failed to unsubscribe from {channel}: {e}")
    
    # ========================================
    # DATA ACCESS METHODS
    # ========================================
    
    def get_price(self, symbol: str) -> float:
        """
        Get latest price for symbol.
        
        Args:
            symbol: Trading pair in WebSocket format
            
        Returns:
            Latest price (0 if not available)
        """
        price_data = self.latest_prices.get(symbol, {})
        return price_data.get('price', 0)
    
    def get_orderbook(self, symbol: str) -> Dict:
        """
        Get latest orderbook for symbol.
        
        Args:
            symbol: Trading pair in WebSocket format
            
        Returns:
            Orderbook with bids and asks
        """
        return self.orderbooks.get(symbol, {'bids': {}, 'asks': {}})
    
    def get_best_bid(self, symbol: str) -> float:
        """Get best bid price"""
        orderbook = self.get_orderbook(symbol)
        bids = orderbook.get('bids', {})
        if bids:
            return max(float(price) for price in bids.keys())
        return 0
    
    def get_best_ask(self, symbol: str) -> float:
        """Get best ask price"""
        orderbook = self.get_orderbook(symbol)
        asks = orderbook.get('asks', {})
        if asks:
            return min(float(price) for price in asks.keys())
        return 0
    
    def get_spread(self, symbol: str) -> float:
        """Get bid-ask spread"""
        bid = self.get_best_bid(symbol)
        ask = self.get_best_ask(symbol)
        return ask - bid if (bid and ask) else 0
    
    def get_recent_trades(self, limit: int = 100) -> List[Dict]:
        """Get recent trades"""
        return self.trades[-limit:]
    
    def get_balance(self, currency: str) -> Dict:
        """Get balance for specific currency"""
        return self.balances.get(currency, {
            'available': 0,
            'locked': 0,
            'total': 0
        })
    
    # ========================================
    # CALLBACK REGISTRATION
    # ========================================
    
    def set_price_callback(self, callback: Callable):
        """Set callback for price updates"""
        self.on_price_callback = callback
    
    def set_orderbook_callback(self, callback: Callable):
        """Set callback for orderbook updates"""
        self.on_orderbook_callback = callback
    
    def set_trade_callback(self, callback: Callable):
        """Set callback for trade updates"""
        self.on_trade_callback = callback
    
    def set_balance_callback(self, callback: Callable):
        """Set callback for balance updates"""
        self.on_balance_callback = callback
    
    def set_order_callback(self, callback: Callable):
        """Set callback for order updates"""
        self.on_order_callback = callback
    
    # ========================================
    # HEALTH MONITORING
    # ========================================
    
    async def heartbeat_loop(self):
        """Keep connection alive with periodic pings"""
        while self.is_connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if self.is_connected:
                    await self.sio.emit('ping', {'data': 'keep-alive'})
                    self.last_heartbeat = time.time()
                    
            except Exception as e:
                logger.error(f"❌ Heartbeat error: {e}")
    
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        if not self.is_connected:
            return False
        
        # Check if last heartbeat was recent
        time_since_heartbeat = time.time() - self.last_heartbeat
        if time_since_heartbeat > 60:  # 60 seconds threshold
            logger.warning("⚠️  WebSocket connection may be stale")
            return False
        
        return True
    
    def __repr__(self):
        status = "connected" if self.is_connected else "disconnected"
        auth = "authenticated" if self.is_authenticated else "unauthenticated"
        return f"CoinDCXWebSocket(status={status}, {auth}, channels={len(self.subscribed_channels)})"
