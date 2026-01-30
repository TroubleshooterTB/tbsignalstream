# 🚀 Quick Start Guide - Crypto Bot

**Ready to test your new crypto trading bot!**

---

## ⚡ Prerequisites

### 1. Install New Dependencies
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
pip install python-socketio[asyncio_client] aiohttp requests cryptography
```

### 2. Create CoinDCX Account
1. Visit https://coindcx.com
2. Sign up and complete KYC
3. Enable 2FA (security)
4. Go to Settings → API Management
5. Create new API key with permissions:
   - ✅ **Read** (view balances, orders)
   - ✅ **Trade** (place/cancel orders)
   - ❌ **Withdraw** (keep disabled for security)
6. **Save your API Key and API Secret securely**

### 3. Add Credentials to Firestore

**Option A: Using Python Script (Recommended)**
```python
# Run in Python console or create script
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('firestore-key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Add your credentials
from trading_bot_service.coindcx_credentials import CoinDCXCredentials

CoinDCXCredentials.save_credentials(
    user_id="your_user_id",  # e.g., "default_user"
    api_key="YOUR_COINDCX_API_KEY",
    api_secret="YOUR_COINDCX_API_SECRET"
)

print("✅ Credentials saved!")
```

**Option B: Manually in Firebase Console**
1. Go to Firebase Console → Firestore Database
2. Create collection: `coindcx_credentials`
3. Add document with ID: `your_user_id`
4. Add fields:
   - `api_key`: (string) Your CoinDCX API key
   - `api_secret_encrypted`: (string) Your secret (use Option A for encryption)
   - `enabled`: (boolean) `true`
   - `timestamp`: (timestamp) Auto

---

## 🎯 Quick Test

### 1. Start the Bot Locally
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
python start_crypto_bot_locally.py --user your_user_id --pair BTC
```

### 2. What You'll See
```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║               🚀 24/7 CRYPTO TRADING BOT (LOCAL)                ║
║                                                                  ║
║  Exchange: CoinDCX                                               ║
║  Pairs: BTC/USDT, ETH/USDT                                       ║
║  Hours: 24/7 (no restrictions)                                   ║
║                                                                  ║
║  Press Ctrl+C to stop gracefully                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

🚀 STARTING 24/7 CRYPTO TRADING BOT
User: your_user_id
Trading Pair: BTC (BTCUSDT)
Time: 2026-01-31 10:30:00

🔐 Retrieving CoinDCX credentials...
✅ Credentials retrieved
   API Key: ABC12345...

🤖 Creating crypto bot instance...
✅ CryptoBotEngine initialized
   Active pair: BTC (BTCUSDT)
   Day Strategy: Momentum Scalping (5m candles, Triple EMA + RSI)
   Night Strategy: Mean Reversion (1h candles, Bollinger Bands + RSI)
   Risk Management: 25% target volatility

🔌 Connecting WebSocket...
✅ WebSocket connected and subscribed

📊 Bootstrapping historical data...
   BTC Balance: 0.000000
   ETH Balance: 0.000000
   USDT Balance: 1000.00
   Daily Starting Capital: $1,000.00
   Current Price: $42,567.89
   5m Candles: 500
   1h Candles: 200
   4h Candles: 100
   
📊 Pre-calculating indicators (warm-up period)...
✅ Bootstrap complete

🔄 Starting 24/7 trading loop...
💓 Loop 60: BTC = $42,567.89
💓 Loop 120: BTC = $42,578.12
...
```

### 3. Test Scenarios

**Scenario 1: Day Strategy Entry**
```
🚀 DAY ENTRY SIGNAL:
   EMA8: 42,567 > EMA16: 42,450 (bullish crossover)
   EMA16: 42,450 > EMA32: 42,200 (uptrend)
   RSI: 62.3 (momentum zone)
   Position Size: 0.015 BTC
   
📊 Position Sizing:
   Available Capital: $1,000.00
   Current Volatility: 30.2%
   Target Volatility: 25.0%
   Weight: 82.8%
   Position Value: $828.00
   Position Size: 0.019 BTC

✅ BUY position opened: 0.019 BTC @ $42,567.00
```

**Scenario 2: Day Strategy Exit**
```
🔻 DAY EXIT: EMA8 crossed below EMA16 (momentum loss)
✅ Position closed: BTCUSDT
   Entry: $42,567 → Exit: $43,120
   P&L: +$553 (+1.3%)
```

**Scenario 3: Night Strategy Entry**
```
🌙 NIGHT ENTRY SIGNAL:
   Price: $41,850 <= Lower BB: $41,900
   RSI: 27.4 < 30 (oversold)
   Target: $42,500 (middle band)
   Position Size: 0.012 BTC
   
✅ BUY position opened: 0.012 BTC @ $41,850.00
```

**Scenario 4: Stop Loss**
```
⛔ DAY STOP LOSS: Loss -2.05% triggered
✅ Position closed: BTCUSDT
   Entry: $42,567 → Exit: $41,695
   P&L: -$872 (-2.05%)
```

---

## 📊 Monitoring

### Watch the Logs
The bot logs everything in real-time:
- ✅ Green: Successful actions
- ⚠️ Yellow: Warnings (skipped trades, etc.)
- ❌ Red: Errors or stop losses
- 💓 Blue: Heartbeat (bot is alive)

### Key Metrics to Track
1. **Win Rate:** % of profitable trades
2. **Avg Win vs Avg Loss:** Should be positive
3. **Profit Factor:** Total wins / Total losses (target >1.5)
4. **Max Drawdown:** Largest peak-to-valley decline
5. **Daily P&L:** Track against 5% loss limit

---

## 🛑 Stopping the Bot

**Graceful Shutdown:**
```
Press Ctrl+C

⚠️  Keyboard interrupt received - stopping bot...
🛑 Stopping crypto bot...
✅ Crypto bot stopped
```

The bot will:
1. Close WebSocket connection
2. Close all open positions (if safe)
3. Save final state to Firestore
4. Exit cleanly

---

## 🔧 Troubleshooting

### Bot Won't Start - Missing Credentials
```
❌ No CoinDCX credentials found!
   Please add credentials for user 'your_user_id' to Firestore
```
**Fix:** Follow step 3 in Prerequisites above

### Bot Won't Start - Missing Dependencies
```
ModuleNotFoundError: No module named 'socketio'
```
**Fix:** Run `pip install python-socketio[asyncio_client] aiohttp requests cryptography`

### No Trading Signals
**Possible Reasons:**
1. **Day Strategy:** No EMA crossovers (market is flat or trending opposite)
2. **Night Strategy:** Price not touching Bollinger Bands (market is stable)
3. **Liquidity Filter:** Trading volume too low (<$1M)
4. **Fee Barrier:** Projected profit < 0.15% (move too small)

**What to Do:**
- Be patient - strategies don't signal every minute
- Check current market conditions (trending vs ranging)
- Day strategy needs volatility and momentum
- Night strategy needs mean-reverting behavior

### Daily Loss Limit Triggered
```
❌ DAILY LOSS LIMIT TRIGGERED: -5.2% loss
   Starting Capital: $1,000.00
   Current Capital: $948.00
   Loss: $52.00
```
**What Happens:**
- All positions closed immediately
- Trading paused for rest of day
- Resumes next day at midnight IST

**What to Do:**
- Review trades that lost money
- Check if strategy needs tuning
- Consider lowering position sizes

---

## 📈 Strategy Quick Reference

### When to Expect Signals

**Day Strategy (9 AM - 9 PM IST):**
- **Best:** Strong trending markets (bull or bear runs)
- **Worst:** Choppy, sideways markets
- **Frequency:** 2-5 signals per day (depends on volatility)

**Night Strategy (9 PM - 9 AM IST):**
- **Best:** Ranging, consolidating markets
- **Worst:** Strong trending markets (trends don't revert)
- **Frequency:** 1-3 signals per night (less volatile hours)

### Strategy Switching

**Current:** Automatic based on time
- 9 AM - 9 PM IST: Day Strategy
- 9 PM - 9 AM IST: Night Strategy

**BTC/ETH Switching:** Manual (for now)
```python
# While bot is running, call:
bot.switch_pair("ETH")  # Switch to Ethereum
bot.switch_pair("BTC")  # Switch back to Bitcoin
```

---

## 🎓 Learning Resources

### Understanding the Strategies
- [CRYPTO_STRATEGIES_IMPLEMENTED.md](CRYPTO_STRATEGIES_IMPLEMENTED.md) - Full strategy documentation
- [COINDCX_API_COMPLETE_ANALYSIS.md](COINDCX_API_COMPLETE_ANALYSIS.md) - API reference

### Risk Management
- Start small ($100-500 test capital)
- Never risk more than 5% per day
- Monitor for first 1-2 weeks
- Scale up gradually if profitable

### Expected Performance
- **Win Rate:** 40-65% (normal!)
- **Profit Factor:** Target 1.5-2.0
- **Good Month:** 5-15% return
- **Bad Month:** -2% to +2% (breakeven or small loss)

---

## ✅ Final Checklist

Before starting real trading:

- [ ] CoinDCX account created and verified
- [ ] API keys generated (Read + Trade only)
- [ ] Credentials added to Firestore
- [ ] Dependencies installed (`pip install...`)
- [ ] Test run completed with small capital
- [ ] Understand both strategies (read docs)
- [ ] Know how to stop bot (Ctrl+C)
- [ ] Set realistic expectations (40-60% win rate is good!)
- [ ] Ready to monitor for 1-2 weeks

---

## 🚀 Ready to Go!

```powershell
# Start trading BTC
python start_crypto_bot_locally.py --user your_user_id --pair BTC

# Or start with ETH
python start_crypto_bot_locally.py --user your_user_id --pair ETH
```

**Good luck and happy trading!** 💰📈

Remember:
- Start small
- Monitor closely
- Be patient
- Trust the strategy (it's backed by research!)
- Don't overtrade

---

**Questions?** Check the full documentation:
- [CRYPTO_STRATEGIES_IMPLEMENTED.md](CRYPTO_STRATEGIES_IMPLEMENTED.md)
- [CRYPTO_BOT_NEXT_STEPS.md](CRYPTO_BOT_NEXT_STEPS.md)
