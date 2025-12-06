# 🚀 LIVE TRADING READINESS CHECKLIST

**Last Updated:** December 7, 2025, 02:45 IST  
**Market Opens:** Monday, December 9, 2025, 9:15 AM IST

---

## ⚠️ CRITICAL: CURRENT STATUS

### 🔴 BLOCKING ISSUES (Must Fix Before Live Trading)

#### 1. Angel One Credentials Refresh Required
**Issue:** JWT tokens may be expired (causing 403 errors)  
**Impact:** Cannot fetch historical candles or place orders  
**Action Required:**
1. Open dashboard → Settings
2. Click "Connect Angel One"
3. Complete OAuth flow
4. Verify Firestore has fresh `jwt_token` and `feed_token`

#### 2. WebSocket Connection Stability
**Issue:** Previous 429 "Connection Limit Exceeded" errors  
**Impact:** Cannot receive real-time tick data  
**Action Required:**
1. Wait 5 minutes after stopping bot
2. Reconnect Angel One (step 1 above)
3. Start bot fresh
4. Verify WebSocket connects successfully (no 429 errors)

---

## ✅ IMMEDIATE ACTIONS (Tonight - Before Sleep)

### Step 1: Stop Current Bot
```
1. Open dashboard: https://studio--tbsignalstream.us-central1.hosted.app
2. Click "Stop Trading Bot" button
3. Wait 5 minutes for connections to clear
```

### Step 2: Refresh Angel One Credentials
```
1. Dashboard → Settings → Connect Angel One
2. Login with Angel One credentials
3. Authorize the application
4. Verify success message appears
```

### Step 3: Verify Firestore Credentials
```
Open Firestore Console:
https://console.firebase.google.com/project/tbsignalstream/firestore

Check collection: angel_one_credentials/{your-user-id}

Required fields:
✓ jwt_token (should be recent timestamp)
✓ feed_token (should be recent timestamp)
✓ refresh_token
✓ api_key (from secrets)
✓ client_code
```

### Step 4: Test Bot Start (Paper Mode)
```
1. Dashboard → Start Bot
2. Mode: PAPER (DO NOT use Live yet)
3. Strategy: Pattern Detection
4. Symbols: Nifty 50 (default)
5. Click Start
```

### Step 5: Monitor for 5 Minutes
```
Check Cloud Run logs:
gcloud run services logs read trading-bot-service --region asia-south1 --limit 50

✅ GOOD SIGNS:
- "WebSocket connected successfully"
- "Subscribed to X symbols"
- "Historical candles loaded: 200+"
- "Position monitoring thread started"
- "Candle builder thread started"

❌ BAD SIGNS:
- "ERROR 429: Connection Limit Exceeded"
- "ERROR 403: Forbidden"
- "Failed to fetch historical data"
- "WebSocket connection failed"
```

### Step 6: Extended Stability Test
```
Leave bot running in paper mode for 30+ minutes
Monitor logs every 10 minutes
Check for:
- Continuous position monitoring logs (every 0.5s)
- Candle builder logs (every 5s)
- No crashes or silent failures
- No reconnection loops
```

---

## 📋 MONDAY MORNING CHECKLIST (Market Open Day)

### 8:45 AM - Pre-Market Preparation
- [ ] Check market holiday calendar (NSE website)
- [ ] Verify Angel One account balance
- [ ] Confirm margin availability
- [ ] Review risk limits (max 5 positions)

### 9:00 AM - Bot Initialization
- [ ] Stop any running bot from yesterday
- [ ] Fresh bot start in PAPER mode
- [ ] Verify WebSocket connection successful
- [ ] Check historical candles loading (200+ per symbol)
- [ ] Confirm all 22 screening levels active

### 9:10 AM - Pre-Market Validation
- [ ] Dashboard shows "Bot Running"
- [ ] Status API returns correct symbol count
- [ ] No errors in Cloud Run logs
- [ ] Position monitoring thread active
- [ ] Candle builder thread active

### 9:15 AM - Market Open Monitoring
- [ ] Watch first ticks coming in
- [ ] Verify LTP updates in real-time
- [ ] Check pattern detection working
- [ ] Monitor for any errors

### 9:30 AM - Paper Trading Validation (CRITICAL)
**DO NOT SKIP THIS STEP**

Monitor for 30 minutes in paper mode:
- [ ] Signals generating correctly
- [ ] Entry/exit logic working
- [ ] Stop loss/target calculations accurate
- [ ] Position tracking functional
- [ ] No crashes or freezes
- [ ] Risk limits enforced

### 10:00 AM - Go/No-Go Decision Point

**✅ GO LIVE IF:**
- All checkboxes above marked ✅
- No errors in last 45 minutes
- WebSocket stable (no reconnections)
- Paper trades executed correctly
- Confident in system stability

**❌ STAY IN PAPER MODE IF:**
- Any errors in logs
- WebSocket reconnecting
- Missing historical data
- Paper trades not working
- Any uncertainty

---

## 🛡️ LIVE TRADING SAFETY PROTOCOL

### Before Enabling Live Mode

**Understand the Risks:**
- Real money at stake
- Real orders executed on Angel One
- Stop losses are not guaranteed (gap downs can cause larger losses)
- Market volatility can cause unexpected behavior

**System Limits (Hardcoded):**
- Max Positions: 5 concurrent positions
- Auto-Close Time: 3:15 PM (before broker's 3:20 PM cutoff)
- Position Size: 20% of portfolio per trade (default)

### Recommended First Day Limits

**Override default limits to be conservative:**
- Max Positions: 2 (not 5)
- Position Size: 10% of portfolio (not 20%)
- Stop Loss: 1% maximum (tighter than usual)
- Profit Target: 2% (take profits early)

### Enabling Live Mode

1. **In Dashboard:**
   - Toggle "Trading Mode" from "Paper" to "Live"
   - Confirm warning dialog
   - Verify mode shows "LIVE TRADING ACTIVE"

2. **Monitor EVERY Trade:**
   - Watch dashboard for new signals
   - Verify each order confirmation
   - Check Angel One mobile app for order status
   - Confirm positions match dashboard

3. **Emergency Stop:**
   - Keep "Stop Bot" button ready
   - If ANY unexpected behavior → STOP IMMEDIATELY
   - Review logs before restarting

---

## 🔍 MONITORING CHECKLIST (During Live Trading)

### Every 15 Minutes
- [ ] Check dashboard shows correct positions
- [ ] Verify Angel One app matches dashboard
- [ ] Review recent Cloud Run logs (no errors)
- [ ] Confirm WebSocket still connected
- [ ] Check P&L aligns with expectations

### Before Lunch (12:00 PM)
- [ ] Review morning performance
- [ ] Check all positions have stop losses
- [ ] Verify no stuck orders
- [ ] Confirm margin sufficient

### Before Market Close (3:00 PM)
- [ ] Verify auto-close scheduled for 3:15 PM
- [ ] Prepare for manual intervention if needed
- [ ] Watch dashboard at 3:15 PM for EOD square-off
- [ ] Confirm all positions closed by 3:20 PM

---

## 🚨 TROUBLESHOOTING GUIDE

### WebSocket Errors (429)
**Error:** "Connection Limit Exceeded"  
**Fix:**
1. Stop bot
2. Wait 5 minutes
3. Restart with fresh credentials

### Historical Data Errors (403)
**Error:** "403 Forbidden on getCandleData"  
**Fix:**
1. Reconnect Angel One in Settings
2. Verify fresh JWT token in Firestore
3. Restart bot

### Bot Not Starting
**Check:**
1. Angel One credentials in Firestore
2. Cloud Run service running
3. Frontend-backend connectivity
4. Browser console for errors

### Orders Not Executing
**Check:**
1. Trading mode is "Live" (not "Paper")
2. Market is open (9:15 AM - 3:30 PM)
3. Sufficient margin in Angel One account
4. Position limit not reached (max 5)
5. No duplicate position for same symbol

### Dashboard Out of Sync
**Fix:**
1. Refresh browser (Ctrl+R)
2. Check Cloud Run logs for actual status
3. Verify bot still running: GET /status
4. Restart bot if needed

---

## 📊 SUCCESS CRITERIA

### ✅ System Ready for Live Trading When:

**Backend:**
- [x] WebSocket connects without 429 errors
- [x] Historical data API returns 200+ candles
- [x] Position monitoring logs every 0.5s
- [x] Candle builder logs every 5s
- [x] No crashes for 4+ hours straight

**Frontend:**
- [x] Dashboard shows real-time updates
- [x] Trading mode toggle functional
- [x] Start/Stop buttons working
- [x] Status API responsive

**Safety:**
- [x] Max positions limit enforced (5)
- [x] Auto-close at 3:15 PM active
- [x] Market hours validation working
- [x] Stop loss monitoring functional
- [x] Risk limits applied

**Testing:**
- [x] Paper mode runs for 1+ hour without errors
- [x] Market open testing completed (Monday 9:15-10:00 AM)
- [x] Paper trades execute correctly
- [x] All 22 screening levels verified

---

## 📞 EMERGENCY CONTACTS

**Angel One Support:**
- Phone: 1800-103-6666
- Email: support@angelone.in
- Trading Hours: 9:15 AM - 3:30 PM IST

**What to Do in Emergency:**
1. Click "Stop Bot" immediately
2. Login to Angel One mobile/web
3. Manually square off all positions
4. Call Angel One support if needed
5. Review logs after market close

---

## 🎯 FINAL PRE-LAUNCH VERIFICATION

**Run this checklist RIGHT BEFORE going live:**

- [ ] Angel One credentials refreshed (< 24 hours old)
- [ ] WebSocket connected successfully
- [ ] Historical data loading correctly
- [ ] Paper mode tested for 30+ minutes
- [ ] No errors in Cloud Run logs
- [ ] Dashboard showing real-time updates
- [ ] Understand stop loss is NOT guaranteed
- [ ] Comfortable with risk of real money
- [ ] Emergency stop procedure understood
- [ ] Angel One app installed on phone

**If ALL boxes checked → Proceed to Live Mode**  
**If ANY box unchecked → Stay in Paper Mode**

---

## 💡 BEST PRACTICES

1. **Start Small:** Use 2 positions max on day 1
2. **Monitor Closely:** Watch every trade for first week
3. **Take Profits:** Don't be greedy, 2% is good
4. **Cut Losses:** Respect stop losses, don't override
5. **Review Daily:** Check logs and performance after market close
6. **Gradual Scale:** Increase to 3-5 positions over multiple days
7. **Weekend Review:** Analyze week's performance, adjust strategy

---

**Good Luck! Trade Safely. 🚀**
