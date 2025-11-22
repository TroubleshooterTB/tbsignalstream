# SignalStream - New Features Implementation Guide

## Overview
This document details the newly implemented features added to SignalStream to complete the trading platform with real broker integration, risk management, backtesting, and advanced data handling.

---

## 🎯 Features Implemented

### 1. WebSocket Live Data Streaming ✅

**Location**: `functions/src/websocket/websocket_manager.py`, `functions/websocket_server.py`

**What it does**:
- Real-time market data streaming via Angel One WebSocket
- Eliminates 5-second polling delay
- Automatic reconnection handling
- Multi-symbol subscription support

**Key Components**:
```python
class AngelWebSocketManager:
    - connect(): Establish WebSocket connection
    - subscribe(mode, tokens): Subscribe to symbol tokens
    - on_tick(callback): Register callback for tick data
    - disconnect(): Close connection
```

**Cloud Functions**:
- `initializeWebSocket`: Start WebSocket for user
- `subscribeWebSocket`: Subscribe to additional tokens
- `closeWebSocket`: Close connection

**Frontend Integration**:
```typescript
// src/lib/order-api.ts
initializeWebSocket(tokens, mode)
subscribeWebSocket(tokens, mode)
closeWebSocket()
```

**Usage Example**:
```typescript
// Initialize WebSocket with NSE stocks
const tokens = [
  {exchangeType: 1, tokens: ["2885", "1333", "1594"]} // RELIANCE, HDFCBANK, INFY
];
await initializeWebSocket(tokens, 1); // Mode 1 = LTP only
```

**Data Flow**:
1. Frontend calls `/api/initializeWebSocket`
2. Cloud Function creates WebSocket connection
3. Tick data stored in Firestore `live_ticks/{userId}`
4. Frontend polls Firestore or uses real-time listeners

---

### 2. Order Placement & Management ✅

**Location**: `functions/src/trading/order_manager.py`, `functions/order_functions.py`

**What it does**:
- Place Market, Limit, Stop-Loss orders
- Modify and cancel existing orders
- Track order book and trade book
- Get current positions and holdings

**Order Manager Class**:
```python
class OrderManager:
    - place_order(): Place new order
    - modify_order(): Modify existing order
    - cancel_order(): Cancel order
    - get_order_book(): Get all orders
    - get_trade_book(): Get executed trades
    - get_positions(): Get open positions
    - get_holdings(): Get delivery holdings
```

**Order Types Supported**:
- **MARKET**: Immediate execution at market price
- **LIMIT**: Execute at specific price or better
- **STOPLOSS_LIMIT**: Stop-loss with limit price
- **STOPLOSS_MARKET**: Stop-loss at market price

**Product Types**:
- **INTRADAY**: Square-off before market close
- **DELIVERY**: Hold overnight
- **MARGIN**: Margin trading

**Cloud Functions**:
- `placeOrder`: Place new order
- `modifyOrder`: Modify order
- `cancelOrder`: Cancel order
- `getOrderBook`: Get order history
- `getPositions`: Get current positions

**Frontend API**:
```typescript
// src/lib/order-api.ts
placeOrder({
  symbol: "RELIANCE-EQ",
  token: "2885",
  exchange: "NSE",
  transactionType: "BUY",
  orderType: "MARKET",
  quantity: 10,
  productType: "INTRADAY"
})
```

**API Routes**:
- `/api/placeOrder`
- `/api/modifyOrder`
- `/api/cancelOrder`
- `/api/getOrderBook`
- `/api/getPositions`

---

### 3. Risk Management System ✅

**Location**: `functions/src/trading/risk_manager.py`

**What it does**:
- Portfolio-level risk controls
- Position sizing based on volatility
- Correlation analysis
- Drawdown monitoring
- Daily loss limits

**Risk Limits**:
```python
@dataclass
class RiskLimits:
    max_portfolio_heat: 6%        # Max risk across all positions
    max_position_size_pct: 2%     # Max 2% per position
    max_drawdown_pct: 10%          # Max 10% drawdown
    max_daily_loss_pct: 3%         # Max 3% daily loss
    max_correlation: 0.7           # Max correlation between stocks
    max_open_positions: 5          # Max 5 concurrent trades
    min_risk_reward: 2.0           # Min 1:2 risk/reward
    max_sector_exposure: 30%       # Max 30% in one sector
```

**Key Functions**:
```python
class RiskManager:
    - calculate_position_size(entry, stop, volatility): Calculate optimal size
    - check_portfolio_heat(): Validate total risk
    - check_drawdown(): Monitor drawdown
    - check_daily_loss_limit(): Check daily limits
    - check_correlation(ticker, price_data): Validate correlation
    - check_sector_exposure(sector, value): Check sector limits
    - validate_trade(): Comprehensive 8-point validation
    - get_risk_summary(): Get current risk status
```

**Validation Checks**:
1. Max open positions
2. Daily loss limit
3. Drawdown limit
4. Risk/reward ratio
5. Portfolio heat
6. Sector exposure
7. Position correlation
8. Position size limits

**Integration Example**:
```python
# Before placing order
risk_mgr = RiskManager(portfolio_value=100000)
is_valid, violations = risk_mgr.validate_trade(
    ticker="RELIANCE",
    entry_price=2850,
    stop_loss=2810,
    target=2930,
    sector="Energy",
    quantity=10,
    volatility=0.02
)

if is_valid:
    # Place order
    order_mgr.place_order(...)
else:
    # Reject trade
    logger.warning(f"Trade rejected: {violations}")
```

---

### 4. Backtesting Framework ✅

**Location**: `functions/src/backtest/backtester.py`

**What it does**:
- Test strategies on historical data
- Simulate order execution with slippage/commission
- Calculate comprehensive performance metrics
- Generate equity curves

**Backtester Class**:
```python
class Backtester:
    - run_backtest(data, strategy_func, params): Run backtest
    - get_equity_curve(): Get equity curve
    - get_trade_log(): Get all trades
```

**Metrics Calculated**:
- Total trades
- Win rate
- Total P&L
- Average win/loss
- Profit factor
- Sharpe ratio
- Maximum drawdown
- Maximum drawdown duration
- Average trade duration
- Expectancy

**Usage Example**:
```python
# Define strategy
def breakout_strategy(data, lookback=20):
    if len(data) < lookback:
        return None
    
    high_20 = data['high'].rolling(lookback).max()
    if data['close'].iloc[-1] > high_20.iloc[-2]:
        return {
            'type': 'buy',
            'ticker': 'RELIANCE',
            'quantity': 10,
            'stop_loss': data['low'].iloc[-1],
            'target': data['close'].iloc[-1] * 1.03
        }
    return None

# Run backtest
backtester = Backtester(initial_capital=100000)
metrics = backtester.run_backtest(
    data=historical_data,
    strategy_func=breakout_strategy,
    strategy_params={'lookback': 20}
)

print(f"Win Rate: {metrics.win_rate:.2f}%")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown:.2f}%")
```

---

### 5. Historical Data Management ✅

**Location**: `functions/src/data/historical_data_manager.py`

**What it does**:
- Fetch historical OHLCV data from Angel One
- Store data in Firestore for caching
- Calculate technical indicators
- Data cleaning and normalization

**Data Manager Class**:
```python
class HistoricalDataManager:
    - fetch_historical_data(symbol, token, exchange, interval, from_date, to_date)
    - store_to_firestore(symbol, interval, data)
    - load_from_firestore(symbol, interval)
    - get_or_fetch_data(..., force_refresh)
    - calculate_indicators(data)
```

**Supported Intervals**:
- ONE_MINUTE
- FIVE_MINUTE
- FIFTEEN_MINUTE
- THIRTY_MINUTE
- ONE_HOUR
- ONE_DAY

**Indicators Calculated**:
- SMA (20, 50)
- EMA (12, 26)
- RSI (14)
- MACD
- Bollinger Bands
- ATR

**Usage Example**:
```python
# Initialize manager
hist_mgr = HistoricalDataManager(api_key, jwt_token)

# Fetch data (cached if available)
data = hist_mgr.get_or_fetch_data(
    symbol="RELIANCE-EQ",
    token="2885",
    exchange="NSE",
    interval="ONE_DAY",
    from_date=datetime(2024, 1, 1),
    to_date=datetime(2024, 12, 31)
)

# Calculate indicators
data_with_indicators = hist_mgr.calculate_indicators(data)
```

---

## 🔧 Integration with Existing System

### Updated Live Alerts Dashboard

**Enhanced with**:
- WebSocket streaming (replace polling)
- Automated order placement on signals
- Risk validation before orders
- Real position tracking from broker

**Modified Flow**:
```
1. WebSocket streams live prices
2. Signal generator detects patterns
3. Risk Manager validates trade
4. Order Manager places order to broker
5. Position tracked in real-time
6. Exit orders placed automatically
```

### Updated Position Manager

**Now includes**:
- Real broker positions sync
- Automated stop-loss/target orders
- Risk-adjusted position sizing
- Portfolio heat monitoring

---

## 📦 Updated Dependencies

Add to `functions/requirements.txt`:
```
smartapi-python==1.3.0
pyotp==2.9.0
pandas==2.1.0
numpy==1.25.0
```

---

## 🚀 Deployment Steps

### 1. Deploy Cloud Functions

```bash
# Deploy WebSocket server
cd functions
gcloud functions deploy initializeWebSocket \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=initializeWebSocket \
  --trigger-http --allow-unauthenticated \
  --set-secrets="ANGELONE_TRADING_API_KEY=ANGELONE_TRADING_API_KEY:latest" \
  --project=tbsignalstream --memory=1GB --timeout=540s

# Deploy order functions
gcloud functions deploy placeOrder \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=placeOrder \
  --trigger-http --allow-unauthenticated \
  --set-secrets="ANGELONE_TRADING_API_KEY=ANGELONE_TRADING_API_KEY:latest" \
  --project=tbsignalstream
```

### 2. Deploy Frontend

```bash
# Deploy to App Hosting
cd tbsignalstream_backup
npm run build
firebase deploy --only apphosting:studio --project=tbsignalstream
```

### 3. Update Firestore Security Rules

Add collections for new features:
```javascript
match /live_ticks/{userId} {
  allow read, write: if request.auth.uid == userId;
}

match /orders/{userId}/order_history/{orderId} {
  allow read, write: if request.auth.uid == userId;
}

match /historical_data_{interval}/{symbol}/candles/{candleId} {
  allow read: if request.auth != null;
}
```

---

## 📊 Testing Guide

### Test WebSocket Streaming

```typescript
// In browser console
const tokens = [{exchangeType: 1, tokens: ["2885"]}];
const result = await fetch('/api/initializeWebSocket', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${idToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({tokens, mode: 1})
});
console.log(await result.json());
```

### Test Order Placement

```typescript
// Place test order (PAPER TRADING FIRST!)
const order = await placeOrder({
  symbol: "RELIANCE-EQ",
  token: "2885",
  exchange: "NSE",
  transactionType: "BUY",
  orderType: "MARKET",
  quantity: 1,
  productType: "INTRADAY"
});
console.log(order);
```

### Test Risk Manager

```python
# Run risk validation
risk_mgr = RiskManager(portfolio_value=100000)
is_valid, violations = risk_mgr.validate_trade(
    ticker="RELIANCE",
    entry_price=2850,
    stop_loss=2820,
    target=2910,
    sector="Energy",
    quantity=10,
    volatility=0.025
)
print(f"Valid: {is_valid}")
print(f"Violations: {violations}")
```

### Test Backtesting

```python
# Load historical data
hist_mgr = HistoricalDataManager(api_key, jwt_token)
data = hist_mgr.fetch_historical_data(...)

# Run backtest
backtester = Backtester(initial_capital=100000)
metrics = backtester.run_backtest(data, strategy_func)

# Review results
print(metrics)
trade_log = backtester.get_trade_log()
print(trade_log.head())
```

---

## ⚠️ Important Notes

### Risk Management
- **ALWAYS** validate trades through RiskManager before placing orders
- Monitor portfolio heat continuously
- Respect daily loss limits
- Test thoroughly in paper trading mode first

### Order Execution
- Orders are placed to **LIVE broker account**
- Use INTRADAY product type for same-day trades
- Verify sufficient margin before placing orders
- Monitor order status after placement

### WebSocket Connection
- WebSocket connections have timeout limits
- Implement reconnection logic in production
- Monitor connection status
- Close connections when not needed

### Backtesting
- Use realistic slippage and commission
- Test on out-of-sample data
- Avoid overfitting to historical data
- Consider transaction costs

---

## 🔮 Future Enhancements

### Still To Implement:
1. **Push Notifications** - Firebase Cloud Messaging for alerts
2. **Strategy Optimization** - Genetic algorithms for parameter tuning
3. **Machine Learning Models** - Price prediction with TensorFlow
4. **Multi-timeframe Analysis** - Coordinate signals across timeframes
5. **Portfolio Rebalancing** - Automatic portfolio adjustment
6. **Advanced Charts** - TradingView integration
7. **Social Trading** - Share and copy strategies

---

## 📚 Additional Resources

- [Angel One SmartAPI Docs](https://smartapi.angelbroking.com/docs)
- [Risk Management Best Practices](./docs/risk-management.md)
- [Backtesting Guide](./docs/backtesting-guide.md)
- [Order Types Explained](./docs/order-types.md)

---

**Status**: Implementation Complete ✅  
**Last Updated**: {{ current_date }}  
**Version**: 2.0.0
