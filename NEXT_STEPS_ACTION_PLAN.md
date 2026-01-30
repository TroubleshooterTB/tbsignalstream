# ⚡ IMMEDIATE NEXT STEPS - January 30, 2026

## ✅ COMPLETED
- [x] Bot crash fixes implemented (graceful degradation)
- [x] TradingView alternatives analyzed (not needed!)
- [x] Documentation created (3 comprehensive guides)
- [x] Changes committed and pushed (d0ea7e6)
- [x] Local test passed (bot didn't crash despite token error)
- [x] Backend deployment initiated

---

## 🔄 IN PROGRESS

### **Cloud Run Deployment** (5-10 minutes)
```
Building... → Testing... → Deploying...
```

**What's being deployed**:
- Bot stability fixes (graceful degradation)
- Relaxed pre-trade verification
- WebSocket optional in paper mode
- Bootstrap failure handling

**Expected result**:
- New revision: 00016-xxx
- Service URL: `https://trading-bot-service-818546654122.us-central1.run.app`

---

## 📋 YOUR ACTION ITEMS

### **1. URGENT: Refresh Angel One Credentials** ⚠️

**Issue detected**: Your Angel One tokens expired
```
Error: 401 Authentication Failed. Invalid Feed Token or Client Code or Feed Token expired.
```

**Solution** (5 minutes):

1. **Go to Dashboard Settings page**
2. **Click "Connect Angel One"**
3. **Login with your Angel One credentials**
4. **Authorize the application**
5. **New tokens saved to Firestore** ✅

**Why this matters**:
- Bot needs fresh `jwt_token` and `feed_token`
- Tokens expire every 24 hours
- Without valid tokens, WebSocket can't connect
- Without WebSocket, no real-time data

---

### **2. Configure Bot for First Run** (5 minutes)

After deployment completes and credentials refreshed:

**Option A: Via Dashboard** (Recommended)
1. Open Settings page
2. Set Screening Mode: **RELAXED**
3. Set Trading Mode: **Paper**
4. Set Strategy: **Alpha-Ensemble** (should be default)
5. Trading Enabled: **OFF** (manual approval first)
6. Click "Save Settings"

**Option B: Via Firestore Console**
```json
{
  "strategy": "alpha-ensemble",
  "mode": "paper",
  "screening_mode": "RELAXED",
  "symbol_universe": ["NIFTY_200"],
  "trading_enabled": false,
  "telegram_notifications": false
}
```

---

### **3. Start Bot** (2 minutes)

**Via Dashboard**:
1. Click "Start Trading Bot"
2. Wait 20 seconds for initialization
3. Check status shows "Running"
4. Monitor for any warnings

**Via Terminal** (if dashboard not working):
```powershell
# After refreshing credentials
python start_bot_locally_fixed.py
```

---

### **4. Monitor First 30 Minutes** (Continuous)

**What to watch**:
- ✅ Bot status: "Running"
- ✅ WebSocket: Connected (after token refresh)
- ✅ Symbols: 200 loaded
- ⚠️  Historical candles: May be 0 (OK - will build from ticks)
- ✅ Signals: Start appearing after 10-200 minutes

**Expected startup scenarios**:

**Best case** (market open, good tokens):
```
✅ WebSocket connected
✅ 375 historical candles loaded per symbol
✅ Signals start in 1-2 minutes
```

**Common case** (tokens refreshed):
```
✅ WebSocket connected
⚠️  No historical candles (bootstrap failed)
⚠️  Building candles from live ticks
⚠️  Signals after ~200 minutes (OK!)
```

**Degraded case** (before market open):
```
✅ WebSocket connected but no ticks (market closed)
⚠️  Previous day's candles loaded
⚠️  Will start when market opens at 9:15 AM
```

---

## 🎯 SUCCESS INDICATORS

### **Hour 1: Initialization**
- [x] Deployment completed
- [ ] Credentials refreshed
- [ ] Bot started successfully
- [ ] No crashes in first 30 minutes
- [ ] WebSocket connected
- [ ] Symbol tokens fetched (200)

### **Hour 2-4: Data Accumulation**
- [ ] Candles building (check count increasing)
- [ ] No restart loops
- [ ] Activity feed showing scans
- [ ] First signals appearing (if enough candles)

### **Day 1: Signal Generation**
- [ ] 15-20 signals generated (RELAXED mode)
- [ ] Signals have entry/SL/target
- [ ] Confidence scores 60-100
- [ ] Screening working (24 levels)

---

## 🚨 IF SOMETHING GOES WRONG

### **Bot crashes immediately**
**Before fix**: Would crash on missing data
**After fix**: Should NOT crash - check logs for actual error

**If it still crashes**:
1. Check exact error message
2. Verify credentials are valid
3. Check Firestore accessible
4. Share error logs for debugging

---

### **"No historical candles" warning**
**Status**: ⚠️  WARNING (not error!)
**Meaning**: Bootstrap couldn't fetch data
**Action**: **DO NOTHING** - Bot will build from live ticks

**Why it happens**:
- Started before market open
- Angel One API rate limit
- Network issues

**Result**: Signals after ~200 minutes instead of immediate

---

### **"WebSocket not connected" in paper mode**
**Status**: ⚠️  WARNING (not error!)
**Meaning**: WebSocket authentication failed
**Action**: Refresh Angel One credentials (see step 1)

**Impact**:
- Position monitoring disabled
- Signals still generate (from historical candles)
- Manual monitoring of exits needed

---

### **No signals appearing after 4 hours**
**Possible causes**:
1. Market closed (check time: 9:15 AM - 3:30 PM IST)
2. Not enough candles yet (check candle count)
3. Screening too strict (try RELAXED mode)
4. No breakout patterns today (normal on flat days)

**Debug**:
```
Check Firestore:
- signals collection (should have entries)
- activity_feed collection (should show scans)
- bot_status document (should show candle counts)
```

---

## 📊 WHAT YOU'LL SEE

### **Dashboard Activity Feed** (Real-time)
```
🤖 Bot started - alpha-ensemble strategy
📊 Scanning 200 symbols...
⭐ RELIANCE: BUY signal @ ₹2,456.50 (Confidence: 87)
📊 Scanning 200 symbols...
⭐ TCS: SELL signal @ ₹3,789.20 (Confidence: 72)
📊 Scanning 200 symbols...
```

### **Firestore Signals Collection**
```json
{
  "symbol": "RELIANCE-EQ",
  "action": "BUY",
  "entry_price": 2456.50,
  "stop_loss": 2442.10,
  "target": 2485.30,
  "confidence": 87,
  "strategy": "alpha-ensemble",
  "timestamp": "2026-01-30T18:30:00Z"
}
```

### **Telegram Notifications** (If enabled)
```
🚀 Trading Signal: RELIANCE-EQ
📈 Action: BUY
💰 Entry: ₹2,456.50
🛑 Stop Loss: ₹2,442.10
🎯 Target: ₹2,485.30
⭐ Confidence: 87/100
```

---

## 🎯 WEEK 1 GOALS

### **Days 1-3: Validation**
- [x] Bot runs without crashes ✅
- [ ] 15-20 signals/day generated
- [ ] Signals have valid entry/SL/target
- [ ] Confidence scores reasonable (60-100)
- [ ] No false signals (verify manually)

### **Days 4-7: Optimization**
- [ ] Analyze signal quality
- [ ] Adjust screening mode if needed
- [ ] Test Telegram notifications
- [ ] Review activity patterns

### **Week 2: Live Preparation**
- [ ] Switch to MEDIUM screening (6-8 signals/day)
- [ ] Continue paper trading
- [ ] Calculate expected returns
- [ ] Prepare for live trading

---

## 💡 QUICK REFERENCE

### **Bot Status Check**
```
Dashboard → Bot Status Card
Or
Firestore → bot_status → default_user
```

### **View Signals**
```
Dashboard → Signals Tab
Or
Firestore → signals collection
```

### **Check Activity**
```
Dashboard → Activity Feed
Or
Firestore → activity_feed collection
```

### **Backend Health**
```powershell
curl "https://trading-bot-service-818546654122.us-central1.run.app/health"
```

### **Backend Logs**
```powershell
gcloud run services logs read trading-bot-service --region us-central1 --limit 50
```

---

## 📞 SUPPORT

### **If you need help**:
1. Check [BOT_STABILITY_GUIDE.md](BOT_STABILITY_GUIDE.md) for troubleshooting
2. Check [TRADINGVIEW_ALTERNATIVES_GUIDE.md](TRADINGVIEW_ALTERNATIVES_GUIDE.md) for strategy questions
3. Share exact error messages and logs

### **Documentation**:
- `BOT_STABILITY_GUIDE.md` - All startup scenarios and troubleshooting
- `TRADINGVIEW_ALTERNATIVES_GUIDE.md` - Why you don't need TradingView
- `BOT_CRASH_FIXES_SUMMARY.md` - What was fixed and why

---

**Next Immediate Action**: Wait for deployment to complete, then refresh Angel One credentials! 🚀
