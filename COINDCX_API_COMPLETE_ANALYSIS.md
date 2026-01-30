# CoinDCX API - Complete Analysis for Crypto Trading Bot
**Date**: January 30, 2026  
**Purpose**: Dual-bot platform expansion (Stocks + Crypto)  
**Status**: Comprehensive API research for crypto bot implementation

---

## 🎯 EXECUTIVE SUMMARY

**What We're Building**: Second trading bot for 24/7 cryptocurrency trading using CoinDCX (Indian crypto exchange)

**Key Findings**:
- ✅ **FREE API Access** (no subscription fees like TradingView)
- ✅ **Authentication**: API Key + Secret with HMAC SHA256 signatures
- ✅ **Real-time Data**: WebSocket support for live prices/orderbook/trades
- ✅ **Comprehensive**: REST API + WebSocket, 200+ endpoints
- ✅ **24/7 Trading**: No market hours restrictions (unlike stocks)
- ✅ **Product Support**: Spot, Margin, Futures trading available
- ⚠️ **India-Focused**: Primarily serves Indian users (INR/USDT pairs)

---

## 📋 TABLE OF CONTENTS

1. [API Architecture](#api-architecture)
2. [Authentication System](#authentication-system)
3. [REST API Endpoints](#rest-api-endpoints)
4. [WebSocket Channels](#websocket-channels)
5. [Trading Features](#trading-features)
6. [Implementation Plan](#implementation-plan)
7. [Code Samples](#code-samples)
8. [Rate Limits & Policies](#rate-limits--policies)

---

## 🏗️ API ARCHITECTURE

### Base URLs
```python
# REST API
BASE_URL = "https://api.coindcx.com"
PUBLIC_URL = "https://public.coindcx.com"

# WebSocket
WS_URL = "wss://stream.coindcx.com"
```

### API Structure
```
CoinDCX API
├── Public Endpoints (No auth required)
│   ├── Ticker data
│   ├── Market details
│   ├── Order book
│   ├── Trade history
│   ├── Candlestick data
│   └── Market list
│
├── Private Endpoints (Auth required)
│   ├── User info & balances
│   ├── Order management
│   ├── Trade history
│   ├── Wallet operations
│   └── Sub-account management
│
└── WebSocket Streams
    ├── Public channels (price, trades, orderbook)
    └── Private channels (balance, orders, portfolio)
```

### Trading Products Available
1. **Spot Trading** - Direct buy/sell of crypto
2. **Margin Trading** - Leveraged trading (up to 10x)
3. **Futures Trading** - Perpetual contracts (INR/USDT margined)

**Recommendation for Bot**: Start with **Spot Trading** (simpler, less risky)

---

## 🔐 AUTHENTICATION SYSTEM

### API Key Generation
```
1. Login to CoinDCX
2. Go to Profile → API Dashboard
3. Click "Create API Key"
4. Enter label name
5. (Optional) Bind to specific IP address
6. Enter Email + SMS OTP
7. Save Key + Secret (shown once only!)
```

### Authentication Flow
```python
import hmac
import hashlib
import json
import time

# Step 1: Generate timestamp
timestamp = int(round(time.time() * 1000))

# Step 2: Create request body
body = {
    "timestamp": timestamp,
    # ... other parameters
}
json_body = json.dumps(body, separators=(',', ':'))

# Step 3: Generate HMAC signature
secret_bytes = bytes(API_SECRET, encoding='utf-8')
signature = hmac.new(
    secret_bytes, 
    json_body.encode(), 
    hashlib.sha256
).hexdigest()

# Step 4: Send request with headers
headers = {
    'Content-Type': 'application/json',
    'X-AUTH-APIKEY': API_KEY,
    'X-AUTH-SIGNATURE': signature
}

response = requests.post(url, data=json_body, headers=headers)
```

### Key Points
- **Timestamp Required**: Every authenticated request needs current epoch timestamp
- **Signature Expiry**: Requests older than 10 seconds rejected
- **HMAC SHA256**: Industry standard, similar to Angel One
- **IP Binding**: Optional but recommended for security

---

## 🔌 REST API ENDPOINTS

### 1. Market Data (Public - No Auth)

#### Get All Markets
```python
GET /exchange/v1/markets
# Returns: ["BTCUSDT", "ETHUSDT", "ADAUSDT", ...]
```

#### Get Market Details
```python
GET /exchange/v1/markets_details

Response:
{
  "coindcx_name": "BTCUSDT",
  "base_currency_short_name": "USDT",
  "target_currency_short_name": "BTC",
  "min_quantity": 0.001,
  "max_quantity": 1000,
  "min_price": 1000,
  "max_price": 100000,
  "min_notional": 10,  # Min order value in USDT
  "step": 0.001,  # Min increment
  "pair": "B-BTC_USDT",  # Use this for WebSocket
  "status": "active",
  "order_types": ["limit_order", "market_order", "stop_limit"]
}
```

#### Get Current Ticker
```python
GET /exchange/ticker

Response:
{
  "market": "BTCUSDT",
  "bid": 45000.50,  # Highest buy price
  "ask": 45001.00,  # Lowest sell price
  "high": 46000,    # 24h high
  "low": 44000,     # 24h low
  "volume": 1250.5, # 24h volume
  "last_price": 45000.75,
  "timestamp": 1706600000
}
```

#### Get Orderbook
```python
GET https://public.coindcx.com/market_data/orderbook?pair=B-BTC_USDT

Response:
{
  "bids": {
    "45000.00": "0.5",
    "44999.00": "1.2",
    "44998.00": "0.8"
  },
  "asks": {
    "45001.00": "0.3",
    "45002.00": "0.9",
    "45003.00": "1.5"
  }
}
```

#### Get Candlestick Data
```python
GET https://public.coindcx.com/market_data/candles
    ?pair=B-BTC_USDT
    &interval=1m  # 1m,5m,15m,30m,1h,2h,4h,6h,8h,1d,3d,1w,1M
    &limit=500

Response:
[
  {
    "time": 1706600000000,
    "open": 45000.00,
    "high": 45100.00,
    "low": 44950.00,
    "close": 45050.00,
    "volume": 125.5
  },
  ...
]
```

#### Get Trade History
```python
GET https://public.coindcx.com/market_data/trade_history
    ?pair=B-BTC_USDT
    &limit=50

Response:
[
  {
    "p": 45000.50,  # price
    "q": 0.1,       # quantity
    "T": 1706600000,  # timestamp
    "m": false      # maker (false = taker)
  },
  ...
]
```

### 2. Account Management (Private - Auth Required)

#### Get Balances
```python
POST /exchange/v1/users/balances

Response:
[
  {
    "currency": "BTC",
    "balance": 1.5,              # Available balance
    "locked_balance": 0.2        # In open orders
  },
  {
    "currency": "USDT",
    "balance": 10000.0,
    "locked_balance": 500.0
  }
]
```

#### Get User Info
```python
POST /exchange/v1/users/info

Response:
{
  "coindcx_id": "fda259ce-22fc-11e9-ba72-ef9b29b5db2b",
  "first_name": "Tushar",
  "last_name": "Sharma",
  "email": "user@example.com",
  "mobile_number": "9876543210"
}
```

### 3. Order Management (Private - Auth Required)

#### Place Order
```python
POST /exchange/v1/orders/create

Request:
{
  "side": "buy",  # buy or sell
  "order_type": "limit_order",  # market_order, limit_order, stop_limit
  "market": "BTCUSDT",
  "price_per_unit": 45000.00,  # Not needed for market orders
  "total_quantity": 0.1,
  "timestamp": 1706600000000
}

Response:
{
  "orders": [{
    "id": "ead19992-43fd-11e8-b027-bb815bcb14ed",
    "market": "BTCUSDT",
    "order_type": "limit_order",
    "side": "buy",
    "status": "open",  # open, filled, cancelled, rejected
    "fee_amount": 0.00001,
    "fee": 0.1,  # 0.1% fee
    "total_quantity": 0.1,
    "remaining_quantity": 0.1,
    "avg_price": 0.0,
    "price_per_unit": 45000.00,
    "created_at": "2024-01-30T12:00:00.000Z"
  }]
}
```

#### Get Order Status
```python
POST /exchange/v1/orders/status

Request:
{
  "id": "ead19992-43fd-11e8-b027-bb815bcb14ed",
  "timestamp": 1706600000000
}

Response:
{
  "id": "ead19992-43fd-11e8-b027-bb815bcb14ed",
  "status": "filled",  # open, filled, cancelled, partially_filled
  "filled_quantity": 0.1,
  "remaining_quantity": 0.0,
  "avg_price": 45000.50
}
```

#### Cancel Order
```python
POST /exchange/v1/orders/cancel

Request:
{
  "id": "ead19992-43fd-11e8-b027-bb815bcb14ed",
  "timestamp": 1706600000000
}

Response:
{
  "message": "Order cancelled successfully",
  "status": 200
}
```

#### Get Active Orders
```python
POST /exchange/v1/orders/active_orders

Request:
{
  "market": "BTCUSDT",
  "side": "buy",  # optional
  "timestamp": 1706600000000
}

Response:
[
  {
    "id": "...",
    "market": "BTCUSDT",
    "side": "buy",
    "status": "open",
    "remaining_quantity": 0.05,
    ...
  }
]
```

#### Get Trade History
```python
POST /exchange/v1/orders/trade_history

Request:
{
  "from_id": 12345,  # optional
  "limit": 100,      # max 5000
  "symbol": "BTCUSDT",  # optional
  "timestamp": 1706600000000
}

Response:
[
  {
    "id": 564389,
    "order_id": "ee060ab6-40ed-11e8-b4b9-3f2ce29cd280",
    "side": "buy",
    "fee_amount": "0.00001129",
    "quantity": 0.1,
    "price": 45000.50,
    "symbol": "BTCUSDT",
    "timestamp": 1706600000000
  }
]
```

### 4. Wallet Operations

#### Transfer Between Wallets
```python
POST /exchange/v1/wallets/transfer

Request:
{
  "source_wallet_type": "spot",  # spot or futures
  "destination_wallet_type": "futures",
  "currency_short_name": "USDT",
  "amount": 1000.0,
  "timestamp": 1706600000000
}

Response:
{
  "status": "success",
  "message": "Transfer completed",
  "code": 200
}
```

---

## 📡 WEBSOCKET CHANNELS

### Connection
```python
import socketio

sio = socketio.Client()
WS_URL = 'wss://stream.coindcx.com'

@sio.event
def connect():
    print("Connected!")
    # Join channel
    sio.emit('join', {'channelName': 'B-BTC_USDT@prices'})

sio.connect(WS_URL, transports='websocket')
```

### Public Channels (No Auth)

#### 1. Real-time Price Updates
```python
Channel: {pair}@prices
Event: price-change

@sio.on('price-change')
def on_price(data):
    # data = {"T": timestamp, "p": price, "pr": "spot"}
    print(f"BTC Price: {data['p']}")

# Subscribe
sio.emit('join', {'channelName': 'B-BTC_USDT@prices'})
```

#### 2. Orderbook Updates
```python
Channel: {pair}@orderbook@20  # 10, 20, or 50 levels
Event: depth-update

@sio.on('depth-snapshot')
def on_orderbook(data):
    # Initial snapshot
    bids = data['bids']  # {"45000": "0.5", ...}
    asks = data['asks']

@sio.on('depth-update')
def on_update(data):
    # Incremental updates
    pass

sio.emit('join', {'channelName': 'B-BTC_USDT@orderbook@20'})
```

#### 3. Trade Stream
```python
Channel: {pair}@trades
Event: new-trade

@sio.on('new-trade')
def on_trade(data):
    # data = {"T": timestamp, "p": price, "q": quantity, "m": maker, "s": symbol}
    print(f"Trade: {data['q']} @ {data['p']}")

sio.emit('join', {'channelName': 'B-BTC_USDT@trades'})
```

#### 4. Candlestick Stream
```python
Channel: {pair}_1m  # 1m, 5m, 15m, 30m, 1h, 4h, 8h, 1d, 3d, 1w, 1M
Event: candlestick

@sio.on('candlestick')
def on_candle(data):
    # data = {
    #   "t": start_time,
    #   "o": open, "c": close, "h": high, "l": low,
    #   "v": volume, "s": symbol, "i": interval
    # }
    pass

sio.emit('join', {'channelName': 'B-BTC_USDT_1m'})
```

#### 5. Bulk Price Updates
```python
Channel: currentPrices@spot@10s  # or 1s
Event: currentPrices@spot#update

@sio.on('currentPrices@spot#update')
def on_prices(data):
    # data = {"prices": {"BTCUSDT": 45000, "ETHUSDT": 2500, ...}}
    prices = data['prices']

sio.emit('join', {'channelName': 'currentPrices@spot@10s'})
```

### Private Channels (Auth Required)

#### Authentication
```python
import hmac
import hashlib
import json

# Generate signature
secret_bytes = bytes(API_SECRET, encoding='utf-8')
body = {"channel": "coindcx"}
json_body = json.dumps(body, separators=(',', ':'))
signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

# Join authenticated channel
@sio.event
def connect():
    sio.emit('join', {
        'channelName': 'coindcx',
        'authSignature': signature,
        'apiKey': API_KEY
    })
```

#### 1. Balance Updates
```python
Event: balance-update

@sio.on('balance-update')
def on_balance(data):
    # data = [{
    #   "currency_short_name": "USDT",
    #   "balance": 10000.0,
    #   "locked_balance": 500.0
    # }]
    pass
```

#### 2. Order Updates
```python
Event: order-update

@sio.on('order-update')
def on_order(data):
    # data = [{
    #   "id": "order_id",
    #   "market": "BTCUSDT",
    #   "status": "filled",
    #   "filled_quantity": 0.1,
    #   "avg_price": 45000.50
    # }]
    pass
```

#### 3. Trade Updates
```python
Event: trade-update

@sio.on('trade-update')
def on_trade(data):
    # data = [{
    #   "o": order_id,
    #   "t": trade_id,
    #   "s": symbol,
    #   "p": price,
    #   "q": quantity,
    #   "f": fee,
    #   "x": status
    # }]
    pass
```

### WebSocket Best Practices
```python
# 1. Keep connection alive with ping
async def ping_task():
    while True:
        await asyncio.sleep(25)  # Every 25 seconds
        await sio.emit('ping', {'data': 'keep-alive'})

# 2. Handle disconnections
@sio.event
def disconnect():
    print("Disconnected! Reconnecting...")
    # Implement exponential backoff retry

# 3. Monitor connection health
@sio.event
def connect_error(data):
    print(f"Connection failed: {data}")
```

---

## 💰 TRADING FEATURES

### Order Types

1. **Market Order**
```python
{
  "order_type": "market_order",
  "side": "buy",
  "total_quantity": 0.1,
  # No price needed - executes at best available
}
# ✅ Instant execution
# ⚠️ Price slippage possible
# 💰 Higher fees (taker)
```

2. **Limit Order**
```python
{
  "order_type": "limit_order",
  "side": "buy",
  "price_per_unit": 45000.00,
  "total_quantity": 0.1
}
# ✅ Price guarantee
# ⚠️ May not fill immediately
# 💰 Lower fees if maker
```

3. **Stop-Limit Order**
```python
{
  "order_type": "stop_limit",
  "side": "sell",
  "stop_price": 44000.00,    # Trigger price
  "price_per_unit": 43900.00,  # Limit price
  "total_quantity": 0.1
}
# ✅ Stop-loss protection
# ⚠️ Limit may not fill in fast market
```

### Fees
```
Maker Fee: 0.025%  (limit orders that add liquidity)
Taker Fee: 0.075%  (market orders that take liquidity)

Example:
Buy 1 BTC @ ₹45,00,000
Fee = ₹45,00,000 × 0.00075 = ₹337.50
```

### Trading Limits
```
Min Order Value: 10 USDT (varies by pair)
Max Orders: 25 open orders per market
Rate Limits: ~100 requests/minute (varies by endpoint)
```

### Available Pairs (Examples)
```
USDT Pairs:
- BTC/USDT, ETH/USDT, ADA/USDT
- MATIC/USDT, DOT/USDT, LINK/USDT
- SOL/USDT, AVAX/USDT, UNI/USDT

INR Pairs:
- BTC/INR, ETH/INR, USDT/INR
- (Limited compared to USDT pairs)

Recommendation: Use USDT pairs (more options, better liquidity)
```

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Broker Connector (Week 1)

**File**: `trading_bot_service/brokers/coindcx_broker.py`

```python
class CoinDCXBroker:
    """CoinDCX broker connector for crypto trading"""
    
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.coindcx.com"
        self.session = requests.Session()
    
    def _generate_signature(self, body):
        """Generate HMAC SHA256 signature"""
        secret_bytes = bytes(self.api_secret, encoding='utf-8')
        json_body = json.dumps(body, separators=(',', ':'))
        return hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
    
    def _request(self, method, endpoint, params=None):
        """Make authenticated API request with retry logic"""
        timestamp = int(time.time() * 1000)
        body = params or {}
        body['timestamp'] = timestamp
        
        signature = self._generate_signature(body)
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }
        
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=body, headers=headers)
        return response.json()
    
    # Market Data
    def get_ticker(self, symbol):
        """Get current price for symbol"""
        pass
    
    def get_orderbook(self, symbol, depth=20):
        """Get orderbook depth"""
        pass
    
    def get_historical_candles(self, symbol, interval, limit=500):
        """Get candlestick data"""
        pass
    
    # Account
    def get_balance(self):
        """Get account balances"""
        return self._request('POST', '/exchange/v1/users/balances')
    
    # Trading
    def place_order(self, symbol, side, order_type, quantity, price=None):
        """Place order"""
        params = {
            'market': symbol,
            'side': side,
            'order_type': order_type,
            'total_quantity': quantity
        }
        if price:
            params['price_per_unit'] = price
        
        return self._request('POST', '/exchange/v1/orders/create', params)
    
    def cancel_order(self, order_id):
        """Cancel order"""
        return self._request('POST', '/exchange/v1/orders/cancel', {'id': order_id})
    
    def get_order_status(self, order_id):
        """Get order status"""
        return self._request('POST', '/exchange/v1/orders/status', {'id': order_id})
    
    def get_active_orders(self, symbol=None):
        """Get open orders"""
        params = {}
        if symbol:
            params['market'] = symbol
        return self._request('POST', '/exchange/v1/orders/active_orders', params)
```

### Phase 2: WebSocket Manager (Week 1)

**File**: `trading_bot_service/brokers/coindcx_websocket.py`

```python
import socketio
import asyncio

class CoinDCXWebSocket:
    """Real-time WebSocket data for CoinDCX"""
    
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sio = socketio.AsyncClient()
        self.ws_url = 'wss://stream.coindcx.com'
        
        # Data storage
        self.prices = {}
        self.orderbooks = {}
        self.trades = []
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.sio.event
        async def connect():
            logger.info("WebSocket connected!")
            # Subscribe to authenticated channel if credentials provided
            if self.api_key and self.api_secret:
                await self._authenticate()
        
        @self.sio.on('price-change')
        async def on_price(data):
            symbol = data.get('s', '')
            price = float(data.get('p', 0))
            self.prices[symbol] = price
        
        @self.sio.on('depth-snapshot')
        async def on_orderbook(data):
            symbol = data.get('s', '')
            self.orderbooks[symbol] = {
                'bids': data.get('bids', {}),
                'asks': data.get('asks', {})
            }
        
        @self.sio.on('new-trade')
        async def on_trade(data):
            self.trades.append(data)
            # Keep only last 1000 trades
            if len(self.trades) > 1000:
                self.trades.pop(0)
    
    async def connect(self):
        """Connect to WebSocket"""
        await self.sio.connect(self.ws_url, transports='websocket')
    
    async def subscribe_ticker(self, symbols):
        """Subscribe to price updates"""
        for symbol in symbols:
            channel = f"{symbol}@prices"
            await self.sio.emit('join', {'channelName': channel})
    
    async def subscribe_orderbook(self, symbols):
        """Subscribe to orderbook updates"""
        for symbol in symbols:
            channel = f"{symbol}@orderbook@20"
            await self.sio.emit('join', {'channelName': channel})
    
    async def subscribe_trades(self, symbols):
        """Subscribe to trade stream"""
        for symbol in symbols:
            channel = f"{symbol}@trades"
            await self.sio.emit('join', {'channelName': channel})
    
    async def _authenticate(self):
        """Authenticate for private channels"""
        secret_bytes = bytes(self.api_secret, encoding='utf-8')
        body = {"channel": "coindcx"}
        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
        
        await self.sio.emit('join', {
            'channelName': 'coindcx',
            'authSignature': signature,
            'apiKey': self.api_key
        })
    
    def get_price(self, symbol):
        """Get latest price"""
        return self.prices.get(symbol, 0)
    
    def get_orderbook(self, symbol):
        """Get latest orderbook"""
        return self.orderbooks.get(symbol, {'bids': {}, 'asks': {}})
```

### Phase 3: Crypto Bot Engine (Week 2)

**File**: `trading_bot_service/crypto_bot_engine.py`

```python
class CryptoBotEngine:
    """24/7 Cryptocurrency trading bot for CoinDCX"""
    
    def __init__(self, user_id, credentials, trading_pairs, strategy):
        self.user_id = user_id
        self.trading_pairs = trading_pairs  # ["B-BTC_USDT", "B-ETH_USDT"]
        self.strategy = strategy  # "day" or "night"
        
        # Initialize broker
        self.broker = CoinDCXBroker(
            api_key=credentials['api_key'],
            api_secret=credentials['api_secret']
        )
        
        # Initialize WebSocket
        self.ws = CoinDCXWebSocket(
            api_key=credentials['api_key'],
            api_secret=credentials['api_secret']
        )
        
        # State
        self.is_running = False
        self.positions = {}
        self.candles = {}  # Historical data
        
    async def start(self, running_flag):
        """Start crypto bot - runs 24/7"""
        logger.info("🚀 Starting CryptoBot...")
        
        # Step 1: Connect WebSocket
        await self.ws.connect()
        await self.ws.subscribe_ticker(self.trading_pairs)
        await self.ws.subscribe_orderbook(self.trading_pairs)
        
        # Step 2: Bootstrap historical data
        self._bootstrap_historical_data()
        
        # Step 3: Main trading loop (NO MARKET HOURS!)
        self.is_running = True
        while running_flag() and self.is_running:
            try:
                # Analyze and trade
                await self._analyze_and_trade()
                
                # Sleep (adjust based on strategy)
                await asyncio.sleep(5)  # 5 second scan interval
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(30)
    
    def _bootstrap_historical_data(self):
        """Load historical candles for analysis"""
        for pair in self.trading_pairs:
            candles = self.broker.get_historical_candles(
                symbol=pair,
                interval='1m',
                limit=500
            )
            self.candles[pair] = candles
    
    async def _analyze_and_trade(self):
        """Analyze market and execute trades"""
        for pair in self.trading_pairs:
            # Get current data
            current_price = self.ws.get_price(pair)
            orderbook = self.ws.get_orderbook(pair)
            
            # Strategy-specific analysis
            if self.strategy == "day":
                signal = self._day_strategy_analysis(pair, current_price)
            else:  # night
                signal = self._night_strategy_analysis(pair, current_price)
            
            # Execute if signal
            if signal == "BUY":
                await self._execute_buy(pair, current_price)
            elif signal == "SELL":
                await self._execute_sell(pair, current_price)
    
    def _day_strategy_analysis(self, pair, price):
        """Day trading strategy - higher frequency"""
        # TODO: Implement day strategy
        # - Trend following
        # - Breakout detection
        # - Quick scalps
        pass
    
    def _night_strategy_analysis(self, pair, price):
        """Night trading strategy - conservative"""
        # TODO: Implement night strategy
        # - Mean reversion
        # - Range trading
        # - Lower risk
        pass
    
    async def _execute_buy(self, pair, price):
        """Execute buy order"""
        try:
            # Calculate position size
            balance = self.broker.get_balance()
            usdt_available = balance.get('USDT', {}).get('balance', 0)
            
            # Risk management: max 10% per trade
            order_value = usdt_available * 0.10
            quantity = order_value / price
            
            # Place order
            order = self.broker.place_order(
                symbol=pair,
                side='buy',
                order_type='limit_order',
                quantity=quantity,
                price=price
            )
            
            logger.info(f"✅ BUY {quantity} {pair} @ {price}")
            
        except Exception as e:
            logger.error(f"Buy order failed: {e}")
    
    async def _execute_sell(self, pair, price):
        """Execute sell order"""
        # Similar to buy logic
        pass
```

### Phase 4: Credential Management (Week 2)

**Firestore Structure**:
```
/coindcx_credentials/{user_id}
  - api_key: "XXXX"
  - api_secret: "YYYY"  # Encrypted
  - timestamp: 1706600000
  - ip_binding: "123.45.67.89"  # optional
```

**File**: `trading_bot_service/coindcx_credentials.py`

```python
class CoinDCXCredentials:
    """Manage CoinDCX API credentials"""
    
    @staticmethod
    def save_credentials(user_id, api_key, api_secret):
        """Save encrypted credentials to Firestore"""
        from cryptography.fernet import Fernet
        
        # Encrypt secret
        cipher = Fernet(ENCRYPTION_KEY)
        encrypted_secret = cipher.encrypt(api_secret.encode())
        
        db.collection('coindcx_credentials').document(user_id).set({
            'api_key': api_key,
            'api_secret': encrypted_secret.decode(),
            'timestamp': firestore.SERVER_TIMESTAMP
        })
    
    @staticmethod
    def get_credentials(user_id):
        """Get and decrypt credentials"""
        doc = db.collection('coindcx_credentials').document(user_id).get()
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # Decrypt secret
        cipher = Fernet(ENCRYPTION_KEY)
        decrypted_secret = cipher.decrypt(data['api_secret'].encode()).decode()
        
        return {
            'api_key': data['api_key'],
            'api_secret': decrypted_secret
        }
```

### Phase 5: Dual-Bot Manager (Week 3)

**File**: `trading_bot_service/dual_bot_manager.py`

```python
class DualBotManager:
    """Manage both stock and crypto bots"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.stock_bot = None
        self.crypto_bot = None
    
    def start_stock_bot(self, config):
        """Start Angel One stock trading bot"""
        self.stock_bot = RealtimeBotEngine(
            user_id=self.user_id,
            trading_symbols=config['symbols'],
            trading_strategy=config['strategy']
        )
        
        threading.Thread(
            target=self.stock_bot.start,
            daemon=True
        ).start()
    
    def start_crypto_bot(self, config):
        """Start CoinDCX crypto trading bot"""
        credentials = CoinDCXCredentials.get_credentials(self.user_id)
        
        self.crypto_bot = CryptoBotEngine(
            user_id=self.user_id,
            credentials=credentials,
            trading_pairs=config['pairs'],
            strategy=config['strategy']
        )
        
        asyncio.run(self.crypto_bot.start())
    
    def get_combined_status(self):
        """Get status of both bots"""
        return {
            'stock_bot': {
                'status': 'running' if self.stock_bot and self.stock_bot.is_running else 'stopped',
                'positions': len(self.stock_bot.positions) if self.stock_bot else 0,
                'pnl_today': self._get_stock_pnl()
            },
            'crypto_bot': {
                'status': 'running' if self.crypto_bot and self.crypto_bot.is_running else 'stopped',
                'positions': len(self.crypto_bot.positions) if self.crypto_bot else 0,
                'pnl_today': self._get_crypto_pnl()
            }
        }
```

---

## 📝 CODE SAMPLES

### Complete Trading Example
```python
import hmac
import hashlib
import json
import time
import requests

API_KEY = "your_api_key_here"
API_SECRET = "your_api_secret_here"
BASE_URL = "https://api.coindcx.com"

def create_signature(body):
    """Generate HMAC signature"""
    secret_bytes = bytes(API_SECRET, encoding='utf-8')
    json_body = json.dumps(body, separators=(',', ':'))
    return hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

def api_request(endpoint, params):
    """Make authenticated API request"""
    timestamp = int(time.time() * 1000)
    body = params.copy()
    body['timestamp'] = timestamp
    
    signature = create_signature(body)
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature
    }
    
    url = f"{BASE_URL}{endpoint}"
    response = requests.post(url, json=body, headers=headers)
    return response.json()

# Example 1: Get Balance
balance = api_request('/exchange/v1/users/balances', {})
print("Balance:", balance)

# Example 2: Place Buy Order
buy_order = api_request('/exchange/v1/orders/create', {
    'side': 'buy',
    'order_type': 'limit_order',
    'market': 'BTCUSDT',
    'price_per_unit': 45000.00,
    'total_quantity': 0.001
})
print("Order:", buy_order)

# Example 3: Check Order Status
order_id = buy_order['orders'][0]['id']
status = api_request('/exchange/v1/orders/status', {'id': order_id})
print("Status:", status)

# Example 4: Cancel Order
cancel = api_request('/exchange/v1/orders/cancel', {'id': order_id})
print("Cancelled:", cancel)
```

---

## ⚡ RATE LIMITS & POLICIES

### Rate Limits
```
General: ~100 requests/minute
Order Creation: 10 orders/second
WebSocket: Unlimited (recommended ping every 25s)
```

### API Terms
```
✅ FREE: No subscription fees
✅ Algorithmic Trading: Allowed
✅ High-Frequency Trading: Available (contact support for HFT access)
⚠️ IP Binding: Optional but recommended
⚠️ Token Expiry: API keys don't expire (until revoked)
```

### Error Handling
```python
Common Errors:
400 - Bad Request (invalid parameters)
401 - Unauthorized (wrong API key/signature)
404 - Not Found
422 - Validation Error (insufficient funds, invalid quantity, etc.)
429 - Too Many Requests (rate limit exceeded)
500 - Internal Server Error
503 - Service Unavailable (maintenance)
```

---

## 🎯 NEXT STEPS

### Immediate (Next 3 Days)
1. ✅ CoinDCX API research - COMPLETE
2. ⏳ Test API authentication locally
3. ⏳ Test market data endpoints
4. ⏳ Test order placement (paper trading)

### Week 1 (Feb 5-11)
1. Implement `CoinDCXBroker` class
2. Implement `CoinDCXWebSocket` class
3. Unit tests for API calls
4. Error handling & retry logic

### Week 2 (Feb 12-18)
1. Implement `CryptoBotEngine` class
2. Create crypto trading strategies (day/night)
3. Firestore credential management
4. Integration testing

### Week 3 (Feb 19-25)
1. Implement `DualBotManager`
2. Dashboard UI updates (dual-bot view)
3. Activity feed for both bots
4. Performance monitoring

### Week 4 (Feb 26 - Mar 3)
1. End-to-end testing (stock + crypto)
2. Deploy to Cloud Run
3. Production monitoring setup
4. Documentation & user guide

---

## 🔍 KEY DECISIONS NEEDED FROM YOU

### 1. Trading Pairs
**Question**: Which cryptocurrencies do you want to trade?

**Options**:
- Major: BTC, ETH (most liquid, lower volatility)
- Mid-cap: ADA, MATIC, DOT (moderate risk/reward)
- Small-cap: Various altcoins (higher risk/reward)

**Recommendation**: Start with BTC + ETH (most stable, best liquidity)

### 2. Trading Capital
**Question**: How much capital to allocate to crypto?

**Example Split**:
- Stocks (Angel One): 70% (₹7,00,000)
- Crypto (CoinDCX): 30% (₹3,00,000)

### 3. Strategy Specifics
**Day Strategy** (9 AM - 9 PM IST):
- Frequency: High (multiple trades per day)
- Indicators: ?
- Entry rules: ?
- Exit rules: ?

**Night Strategy** (9 PM - 9 AM IST):
- Frequency: Low (fewer trades)
- Indicators: ?
- Entry rules: ?
- Exit rules: ?

### 4. Risk Management
- Max position size per trade: 10% of capital?
- Stop-loss: 2% per trade?
- Max daily loss: 5% of capital?
- Max open positions: 3?

### 5. Deployment
- Run both bots on same Cloud Run service? (simpler)
- OR separate services? (better isolation)

---

## 📊 COMPARISON: CoinDCX vs Angel One

| Feature | CoinDCX (Crypto) | Angel One (Stocks) |
|---------|------------------|-------------------|
| **Market Hours** | 24/7 | 9:15 AM - 3:30 PM |
| **Weekends** | Yes, 24/7 | No |
| **Authentication** | API Key + Secret (HMAC) | JWT Tokens (24hr expiry) |
| **WebSocket** | Socket.IO | SmartAPI WebSocket |
| **Fees** | 0.025% - 0.075% | Brokerage + taxes |
| **Volatility** | High (crypto nature) | Moderate |
| **Liquidity** | Good (major pairs) | Excellent (NIFTY 50) |
| **API Quality** | Good documentation | Good documentation |
| **Products** | Spot, Margin, Futures | Equity, F&O, Commodity |

---

## ✅ READINESS ASSESSMENT

### Stock Bot (Angel One)
- [x] Broker connector - ✅ Working
- [x] WebSocket integration - ✅ Working
- [x] Trading strategies - ✅ Alpha-Ensemble
- [x] Self-healing system - ✅ Implemented
- [x] Error handling - ✅ Production-grade
- [x] Local testing - ✅ Proven working
- [ ] Production deployment - ⏳ Ready to deploy

### Crypto Bot (CoinDCX)
- [x] API research - ✅ COMPLETE (this document)
- [ ] Broker connector - ⏳ Week 1
- [ ] WebSocket integration - ⏳ Week 1
- [ ] Trading strategies - ⏳ Week 2 (needs your input)
- [ ] Self-healing system - ⏳ Week 2 (reuse stock bot patterns)
- [ ] Testing - ⏳ Week 3
- [ ] Production deployment - ⏳ Week 4

### Platform Infrastructure
- [ ] Dual-bot manager - ⏳ Week 3
- [ ] Multi-broker credentials - ⏳ Week 2
- [ ] Unified dashboard - ⏳ Week 3
- [ ] Combined monitoring - ⏳ Week 3

---

## 🚨 RISKS & MITIGATION

### Technical Risks
1. **24/7 Uptime**: Crypto bot must run continuously
   - Mitigation: Cloud Run auto-scaling, health checks, self-healing

2. **WebSocket Stability**: Connection must stay alive 24/7
   - Mitigation: Auto-reconnection (same as stock bot), keep-alive pings

3. **Crypto Volatility**: Prices can move 10%+ in minutes
   - Mitigation: Tight stop-losses, position sizing, circuit breakers

4. **API Rate Limits**: 100 req/min across both bots
   - Mitigation: Request batching, caching, WebSocket for real-time data

### Financial Risks
1. **Crypto Volatility**: Can lose 20% in a day
   - Mitigation: Conservative position sizing, strict risk rules

2. **Exchange Risk**: CoinDCX could go down
   - Mitigation: Multi-exchange support (future), diversification

3. **Strategy Risk**: Crypto strategies untested
   - Mitigation: Paper trading first, small capital initially

---

## 📚 RESOURCES

### CoinDCX Resources
- **API Docs**: https://docs.coindcx.com/
- **Dashboard**: https://coindcx.com/api-dashboard
- **Support**: support@coindcx.com

### Development Tools
- **socketio client**: `pip install python-socketio`
- **cryptography**: `pip install cryptography`
- **Testing**: Postman, Python unittest

### Learning Resources
- Crypto trading basics
- Technical analysis for crypto
- Risk management in volatile markets

---

## 🎉 SUCCESS METRICS

### Bot Health
- Uptime: 99%+ (24/7 operation)
- WebSocket: <1% disconnections
- Order fill rate: >90%
- API errors: <0.1%

### Trading Performance
- Win rate: Target 40%+
- Profit factor: Target 1.5+
- Max drawdown: <10%
- Sharpe ratio: Target 1.0+

### Platform Metrics
- Dual-bot sync: <100ms latency
- Dashboard load: <2s
- Activity feed: Real-time (<1s delay)
- Credential security: 100% encrypted

---

**END OF DOCUMENT**

Last Updated: January 30, 2026 11:57 PM IST  
Next Review: After user feedback on trading strategies  
Status: READY FOR IMPLEMENTATION
