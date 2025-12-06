# 🚀 QUICK START GUIDE - GET READY FOR LIVE TRADING

**Time Required:** 30-45 minutes  
**Current Time:** ~2:45 AM IST  
**Market Opens:** Monday 9:15 AM (31 hours from now)

---

## 🎯 TONIGHT'S MISSION (Before Sleep)

### Step 1: Wait for Deployment to Complete (~5 minutes)
The backend is currently deploying with critical fixes:
- ✅ Added `/market_data` endpoint (fixes dashboard 404 errors)
- ✅ Improved WebSocket data handling
- ✅ Better error handling for market closed scenarios

**Check deployment status:**
```powershell
gcloud run services list --region asia-south1
```

Look for `trading-bot-service` status: **READY** ✅

---

### Step 2: Run Automated Readiness Check
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
.\check_readiness.ps1
```

**What it checks:**
- Cloud Run service health
- Recent error logs
- Environment variables
- Critical file structure
- Git status

**Expected output:**
- ✅ No 429 WebSocket errors
- ✅ No 403 authentication errors
- ⚠️ May show "bot not running" (expected if stopped)

---

### Step 3: Refresh Angel One Credentials (CRITICAL)

**Why?** JWT tokens expire, causing 403 errors

**How:**
1. Open: https://studio--tbsignalstream.us-central1.hosted.app
2. Click **Settings** (gear icon)
3. Click **Connect Angel One**
4. Login with your Angel One credentials:
   - Client Code: Your Angel One ID
   - Password: Your Angel One password
   - TOTP: From Google Authenticator app
5. Authorize the application
6. Wait for success message: "Connected to Angel One successfully"

**Verify in Firestore:**
```
https://console.firebase.google.com/project/tbsignalstream/firestore/databases/-default-/data/~2Fangel_one_credentials

Check your user document has:
- jwt_token (recent timestamp)
- feed_token (recent timestamp)
- refresh_token
- api_key (should match secrets)
```

---

### Step 4: Test Bot Start (Paper Mode)

**Dashboard:** https://studio--tbsignalstream.us-central1.hosted.app

1. **Verify Settings:**
   - Trading Mode: **PAPER** (toggle should be OFF/gray)
   - Strategy: Pattern Detection
   - Symbols: Nifty 50 (default 49 stocks)

2. **Click "Start Trading Bot"**

3. **Watch for Success Message:**
   ```
   ✅ Trading bot started for 49 symbols
   Mode: paper
   Strategy: pattern
   ```

4. **DO NOT CLOSE BROWSER** - Keep dashboard open

---

### Step 5: Monitor Initial Startup (5 minutes)

**Check Cloud Run Logs:**
```powershell
# Watch logs in real-time
gcloud run services logs tail trading-bot-service --region asia-south1
```

**✅ GOOD SIGNS (What to look for):**
```
✓ Bot engine initialized successfully
✓ WebSocket connected successfully  
✓ Subscribed to 49 symbols
✓ Historical candles loaded: 200+ (per symbol)
✓ Position monitoring thread started
✓ Candle builder thread started
✓ All 22 screening levels initialized
```

**❌ BAD SIGNS (STOP and troubleshoot):**
```
✗ ERROR 429: Connection Limit Exceeded
   → FIX: Stop bot, wait 5 min, try again

✗ ERROR 403: Forbidden (getCandleData)
   → FIX: Reconnect Angel One (Step 3)

✗ ERROR: Missing credentials
   → FIX: Check Firestore, reconnect Angel One

✗ WebSocket connection failed
   → FIX: Wait 5 min, restart bot
```

---

### Step 6: Extended Stability Test (30 minutes)

**What to do:**
- Leave bot running
- Keep Cloud Run logs open
- Set a timer for 30 minutes
- Check logs every 10 minutes

**Every 10 Minutes Check:**
```powershell
gcloud run services logs read trading-bot-service --region asia-south1 --limit 30
```

**Look for:**
- ✅ Continuous position monitoring logs (every 0.5 seconds)
- ✅ Candle builder logs (every 5 seconds)
- ✅ NO error messages
- ✅ NO reconnection attempts
- ✅ WebSocket stays connected

**After 30 Minutes:**
- If stable → ✅ **READY FOR MONDAY**
- If any errors → ❌ **TROUBLESHOOT** (see guide below)

---

### Step 7: Stop Bot Before Sleep

**Why?** 
- Market is closed (weekend)
- Save server resources
- Fresh start Monday morning

**How:**
```
1. Dashboard → Click "Stop Trading Bot"
2. Wait for confirmation: "Bot stopped successfully"
3. Verify status shows "Stopped"
```

---

## 🔍 TROUBLESHOOTING COMMON ISSUES

### Issue: WebSocket 429 "Connection Limit Exceeded"

**Cause:** Too many connections to Angel One  
**Fix:**
1. Stop bot in dashboard
2. Wait **5 full minutes**
3. Reconnect Angel One in Settings
4. Start bot again
5. Should work now ✅

---

### Issue: API 403 "Forbidden" on Historical Data

**Cause:** Expired JWT tokens  
**Fix:**
1. Settings → Connect Angel One
2. Complete OAuth flow
3. Verify fresh tokens in Firestore
4. Restart bot
5. Should load candles now ✅

---

### Issue: Bot Starts but Dashboard Shows "No Data"

**Cause:** Market is closed (weekend/after hours)  
**Fix:** This is **EXPECTED** behavior
- Real data comes only during market hours (9:15 AM - 3:30 PM)
- During closed hours, bot waits for Monday open
- Historical candles still load (check logs)
- Dashboard will populate Monday at 9:15 AM ✅

---

### Issue: "Failed to Start Bot" Error

**Possible Causes:**
1. **Missing credentials** → Reconnect Angel One
2. **Backend down** → Check Cloud Run service running
3. **Invalid token** → Login again to dashboard
4. **Previous bot not stopped** → Stop, wait 1 min, retry

**Debug Steps:**
```powershell
# Check Cloud Run is running
gcloud run services list --region asia-south1

# Check recent errors
gcloud run services logs read trading-bot-service --region asia-south1 --limit 50 | Select-String "ERROR|CRITICAL"

# Check Firestore credentials
# Go to: https://console.firebase.google.com/project/tbsignalstream/firestore
```

---

## 📋 MONDAY MORNING PROCEDURE (Dec 9, 9:00 AM)

### 8:45 AM - Wake Up Early!
- Have coffee ☕
- Open Angel One mobile app
- Open dashboard in browser
- Open Cloud Run logs in another tab

### 9:00 AM - Fresh Bot Start
1. **Stop** any running bot (if left from yesterday)
2. **Verify** Angel One credentials still valid
3. **Start** bot in **PAPER MODE**
4. **Watch** logs for successful WebSocket connection
5. **Confirm** historical candles loading

### 9:10 AM - Pre-Market Validation
- Dashboard shows "Bot Running" ✅
- Cloud Run logs show no errors ✅
- WebSocket connected ✅
- All 22 screening levels active ✅

### 9:15 AM - MARKET OPENS! 🔔
- **Watch dashboard populate with LIVE DATA**
- LTP (Last Traded Price) updating every second
- Volume, high, low showing real numbers
- This confirms bot is getting real-time ticks ✅

### 9:30 AM - Paper Trading Validation (30 minutes)
**CRITICAL: DO NOT SKIP THIS**

Monitor bot in paper mode:
- Watch for pattern detection signals
- Check entry/exit logic
- Verify stop loss calculations
- Confirm position tracking
- Ensure no crashes

### 10:00 AM - GO/NO-GO DECISION

**✅ GO LIVE IF:**
- All above checks passed
- No errors in 45 minutes
- Paper trades executed correctly
- Confident in system

**❌ STAY IN PAPER MODE IF:**
- Any errors in logs
- Missing data
- Paper trades incorrect
- ANY uncertainty

**To Enable Live Mode:**
1. Dashboard → Toggle "Trading Mode" to **LIVE**
2. **READ WARNING CAREFULLY**
3. Understand: Real money, real orders, real risk
4. Start with **2 positions max** (not 5)
5. **Monitor EVERY trade**

---

## 🛡️ SAFETY REMINDERS

**Before Going Live:**
- ✅ Understand stop losses are NOT guaranteed
- ✅ Gap downs can cause larger losses
- ✅ Start with small position sizes (10% of portfolio)
- ✅ Max 2 positions on day 1 (not 5)
- ✅ Keep emergency stop button ready
- ✅ Have Angel One mobile app open

**During Live Trading:**
- Monitor every 15 minutes
- Check Angel One app matches dashboard
- Review logs for errors
- Stop immediately if unexpected behavior
- Don't override stop losses manually

**Emergency Stop:**
1. Click "Stop Bot" in dashboard
2. Login to Angel One app/web
3. Manually square off all positions
4. Call Angel One support if needed: 1800-103-6666

---

## ✅ TONIGHT'S SUCCESS CRITERIA

**Before you sleep, confirm:**
- [x] Deployment completed successfully
- [ ] Readiness script shows ✅ (no critical errors)
- [ ] Angel One credentials refreshed
- [ ] Bot started successfully in paper mode
- [ ] Ran for 30 minutes without errors
- [ ] Bot stopped cleanly
- [ ] Read LIVE_TRADING_READINESS.md checklist

**If all checked → Sleep well, ready for Monday! 🚀**  
**If any unchecked → Fix issues, run readiness script again**

---

## 📞 NEED HELP?

**Check These Documents:**
1. `LIVE_TRADING_READINESS.md` - Comprehensive checklist
2. `ARCHITECTURE.md` - System architecture
3. `check_readiness.ps1` - Automated validation

**Review Logs:**
```powershell
# Last 50 log entries
gcloud run services logs read trading-bot-service --region asia-south1 --limit 50

# Filter errors only
gcloud run services logs read trading-bot-service --region asia-south1 --limit 100 | Select-String "ERROR|CRITICAL|429|403"
```

---

**Good luck! You've got this! 💪**

**Remember:**
- Start in PAPER mode Monday morning
- Validate for 45 minutes before considering live
- Start small (2 positions max day 1)
- Monitor closely
- Trade safely! 🚀
