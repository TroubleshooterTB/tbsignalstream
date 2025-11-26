# Ironclad Trading Strategy - Integration Guide

## ✅ What Was Done

### 1. Created `ironclad_logic.py` (Sidecar Module)
**Location:** `functions/ironclad_logic.py`

A completely standalone, stateless trading strategy module with:
- ✅ **Defining Range (DR) Logic** - Captures 09:15-10:15 IST high/low
- ✅ **Regime Detection** - NIFTY trend analysis with ADX filter
- ✅ **Multi-Indicator Confirmation** - MACD, RSI, Volume, VWAP
- ✅ **ATR-Based Risk Management** - 3x ATR stops, 1.5:1 risk-reward
- ✅ **Firestore State Persistence** - Survives Cloud Function restarts
- ✅ **100% pandas_ta Integration** - All indicators use pandas_ta library

### 2. Modified `main.py`
**Changes:**
- ✅ Added import: `from ironclad_logic import IroncladStrategy`
- ✅ Added new Cloud Function: `runIroncladAnalysis`
- ✅ Added to `__all__` exports
- ✅ Added `datetime` import

### 3. Updated `requirements.txt`
**Added:** `pandas-ta==0.3.14b`

---

## 🎯 How It Works

### Strategy Flow:
```
1. 09:15-10:15 IST → OBSERVING (defining range period)
2. 10:15+ → Calculate DR High/Low (save to Firestore)
3. Check NIFTY regime (ADX + SMA alignment)
4. Check stock trigger (breakout + confirmations)
5. If signal → Calculate ATR-based stop & target
6. Return decision dictionary
```

### Entry Conditions:

**BUY Signal:**
- Price breaks above DR High
- NIFTY regime = BULLISH (10>20>50>100>200 SMA)
- NIFTY ADX > 20
- Stock price > VWAP
- MACD line > Signal line
- RSI >= 40
- Volume > Volume SMA(10)

**SELL Signal:**
- Price breaks below DR Low
- NIFTY regime = BEARISH (10<20<50<100<200 SMA)
- NIFTY ADX > 20
- Stock price < VWAP
- MACD line < Signal line
- RSI <= 60
- Volume > Volume SMA(10)

### Risk Management:
- **Stop Loss:** Entry ± (3.0 × ATR)
- **Target:** Entry ± (1.5 × Distance to Stop)
- **Risk:Reward:** 1:1.5 minimum

---

## 🚀 Usage Examples

### Example 1: Direct API Call (Frontend)
```typescript
// Call from your frontend
const response = await fetch(
  'https://us-central1-tbsignalstream.cloudfunctions.net/runIroncladAnalysis',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      symbols: ['RELIANCE', 'TCS', 'INFY'],
      niftySymbol: 'NIFTY50'
    })
  }
);

const data = await response.json();
// data.signals.RELIANCE = { signal: "BUY", entry_price: 2850, ... }
```

### Example 2: Integration in `live_trading_bot.py`
```python
from ironclad_logic import IroncladStrategy

class LiveTradingBot:
    def __init__(self, user_id: str, symbols: List[str]):
        self.db = firestore.client()
        
        # Initialize Ironclad Strategy
        self.ironclad = IroncladStrategy(self.db)
        
    async def analyze_and_trade(self, symbol: str):
        # Fetch data (your existing code)
        nifty_df = await self.fetch_historical_data('NIFTY50')
        stock_df = await self.fetch_historical_data(symbol)
        
        # Run Ironclad analysis
        decision = self.ironclad.run_analysis_cycle(nifty_df, stock_df, symbol)
        
        # Execute based on signal
        if decision['signal'] == 'BUY':
            await self.place_order(
                symbol=symbol,
                quantity=self.calculate_quantity(decision['entry_price']),
                order_type='LIMIT',
                price=decision['entry_price'],
                stop_loss=decision['stop_loss'],
                target=decision['target']
            )
```

### Example 3: Standalone Testing
```python
# Test the strategy locally
from ironclad_logic import IroncladStrategy
from firebase_admin import firestore
import firebase_admin

# Initialize
firebase_admin.initialize_app()
db = firestore.client()

# Create strategy
strategy = IroncladStrategy(db)

# Run analysis (with your data)
decision = strategy.run_analysis_cycle(nifty_df, stock_df, "RELIANCE")

print(f"Signal: {decision['signal']}")
print(f"Entry: {decision.get('entry_price')}")
print(f"Stop: {decision.get('stop_loss')}")
print(f"Target: {decision.get('target')}")
```

---

## 📦 Firestore Collections Used

### `bot_state/{symbol}`
Stores strategy state per symbol:
```json
{
  "dr_high": 2855.50,
  "dr_low": 2830.25,
  "regime": "BULLISH",
  "last_updated": "2025-11-23T14:30:00+05:30"
}
```

---

## ⚠️ Important Notes

### 1. Data Source Integration Required
The current implementation uses **sample data** in `_fetch_sample_data()`.

**You MUST replace this with real data from:**
- Angel One historical data API
- Your existing `HistoricalDataManager`
- Firestore cached data

**How to fix:**
```python
def _fetch_sample_data(symbol: str):
    # Replace this entire function with:
    from src.data.historical_data_manager import HistoricalDataManager
    
    manager = HistoricalDataManager(user_id)
    return manager.get_or_fetch_data(
        symbol=symbol,
        interval='5minute',
        from_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        to_date=datetime.now().strftime('%Y-%m-%d')
    )
```

### 2. Timezone Handling
- All time checks use **IST (Asia/Kolkata)**
- Ensure your data timestamps are timezone-aware
- The strategy auto-converts UTC to IST

### 3. pandas_ta Dependency
- Added to `requirements.txt`
- Will be installed on next deployment
- Version: `0.3.14b` (stable beta)

### 4. Stateless Design
- No global variables
- All state in Firestore
- Safe for Cloud Function cold starts
- Each analysis cycle is independent

---

## 🔧 Deployment Checklist

- [x] Created `ironclad_logic.py`
- [x] Modified `main.py` (added import + new function)
- [x] Updated `requirements.txt` (added pandas-ta)
- [x] Added `runIroncladAnalysis` to `__all__`
- [ ] **TODO:** Replace `_fetch_sample_data()` with real data source
- [ ] **TODO:** Deploy Cloud Functions
- [ ] **TODO:** Test during market hours
- [ ] **TODO:** Verify Firestore permissions for `bot_state` collection

---

## 🚀 Deployment Commands

```bash
# Deploy all Cloud Functions
cd functions
firebase deploy --only functions --project=tbsignalstream

# Or deploy just the new function
firebase deploy --only functions:runIroncladAnalysis --project=tbsignalstream
```

---

## 🧪 Testing

### Manual Test (After Deployment)
```bash
# Get your Firebase ID token first
curl -X POST \
  https://us-central1-tbsignalstream.cloudfunctions.net/runIroncladAnalysis \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE"],
    "niftySymbol": "NIFTY50"
  }'
```

### Expected Response:
```json
{
  "status": "success",
  "timestamp": "2025-11-23T14:30:00",
  "signals": {
    "RELIANCE": {
      "signal": "BUY",
      "regime": "BULLISH",
      "entry_price": 2850.50,
      "stop_loss": 2820.00,
      "target": 2895.75,
      "dr_high": 2855.00,
      "dr_low": 2830.00,
      "atr": 12.50,
      "rsi": 58.30
    }
  }
}
```

---

## 🔒 What Was NOT Modified

✅ **NO changes to:**
- `angel_login.py` (broker connection untouched)
- `firebase_config.py` (config untouched)
- Existing Cloud Functions (directAngelLogin, getMarketData, etc.)
- WebSocket server
- Order functions
- Live trading bot class structure

✅ **Completely standalone:**
- Can be removed without breaking anything
- Independent Firestore collection (`bot_state`)
- No dependencies on existing strategy code

---

## 📊 Next Steps

1. **Replace sample data function** with real Angel One API integration
2. **Deploy Cloud Functions** to test the new endpoint
3. **Test during market hours** (09:15-15:30 IST)
4. **Integrate into live trading bot** once validated
5. **Add frontend UI** to display Ironclad signals
6. **Monitor Firestore** `bot_state` collection for state persistence

---

## 🐛 Troubleshooting

### Issue: "pandas_ta not found"
**Solution:** Redeploy functions after updating requirements.txt

### Issue: "No data in DR period"
**Solution:** Ensure you're testing after 10:15 IST with intraday data

### Issue: "Firestore permission denied"
**Solution:** Add `bot_state` collection to firestore.rules:
```javascript
match /bot_state/{symbol} {
  allow read, write: if request.auth != null;
}
```

### Issue: Sample data being used
**Solution:** Replace `_fetch_sample_data()` function in main.py

---

**Status:** ✅ Integration Complete - Ready for Data Source Connection
**Version:** 1.0.0
**Date:** November 23, 2025
