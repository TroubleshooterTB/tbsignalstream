# PRE-MARKET CHECKLIST - Run This Every Trading Day
# Time: 9:00 AM IST (Before Market Opens at 9:15 AM)

## WHAT WENT WRONG ON DECEMBER 22, 2025 (MONDAY)

**Problem**: Bot didn't place any trades or show activity
**Root Cause**: Backend service was COMPLETELY BROKEN
- Firebase credentials error caused service to crash on startup
- Service restarted every 3-5 minutes but immediately crashed
- No API endpoints were available
- Bot frontend couldn't communicate with backend

**Why It Happened**: 
- An old broken revision (pre-fix) got deployed somehow
- The working revision 00074 (with Firebase ADC fix) wasn't running

**Lesson Learned**: Always verify backend health BEFORE starting bot!

---

## ✅ PRE-MARKET CHECKLIST (9:00 AM IST - Every Trading Day)

### Step 1: Check Backend Health (CRITICAL)

Open PowerShell and run:
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
.\check_backend_health.ps1
```

**Expected Output:**
```
✅ BACKEND IS HEALTHY
   Status: healthy
   Active Bots: 0
✅ SAFE TO START BOT
```

**If you see ❌ BACKEND NOT RESPONDING:**
1. DO NOT START THE BOT
2. Check logs: 
   ```powershell
   gcloud logging read "resource.labels.service_name=trading-bot-service AND severity>=ERROR" --limit 5 --project tbsignalstream
   ```
3. Contact support or check GitHub issues

---

### Step 2: Verify Current Time & Market Hours

```powershell
# Check IST time (Market: 9:15 AM - 3:30 PM IST, Mon-Fri)
[System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'India Standard Time')
```

**Market Hours:**
- **Opens**: 9:15 AM IST
- **Closes**: 3:30 PM IST
- **Best Entry Window**: 10:00 AM - 3:00 PM IST
- **No Trading**: Weekends, Market Holidays

---

### Step 3: Open Dashboard

1. Navigate to: https://studio--tbsignalstream.us-central1.hosted.app
2. Press **Ctrl + Shift + R** (hard refresh)
3. Press **F12** (open DevTools for logs)
4. Check Mode: **Paper Trading** (for testing)

---

### Step 4: Start Bot (9:15 AM IST or Later)

1. Click **"Start Trading Bot"** button
2. Wait 20 seconds for health check
3. Watch for toast message:
   - ✅ "Bot Started Successfully - Trading with 50 symbols. WebSocket connected."
   - ⚠️ "Bot Started with Warnings" → Check Activity Feed
   - ❌ "Bot Started but Has Errors" → STOP and investigate

---

### Step 5: Monitor Activity Feed (First 10 Minutes)

**Expected Activity (9:15-9:25 AM):**
- Bot scanning symbols
- "Market data received" messages
- "Calculating indicators" messages
- WebSocket connection confirmed

**Red Flags:**
- No activity for 5+ minutes
- "WebSocket disconnected" error
- "Failed to fetch data" errors
- No price updates

---

### Step 6: Verify Trading Logic

**Why No Trades Yet?**

The bot uses **Defining Order Strategy**:
1. **Defining Range Period**: 9:30 AM - 10:30 AM IST
   - Bot collects data and establishes DR High/Low
   - **NO TRADES during this hour** (by design)

2. **Trading Period**: 10:30 AM - 3:00 PM IST
   - Waits for breakout above DR High (LONG)
   - Waits for breakdown below DR Low (SHORT)
   - Only trades if ALL filters pass (ADX, Volume, RSI, etc.)

3. **Entry Filters** (All Must Pass):
   - DR breakout confirmed
   - ADX > 25 (strong trend)
   - Volume > 2x average
   - RSI in valid zone
   - Hourly SMA50 trend confirmation
   - Stop loss distance > 0.5%

**If No Trades by 11:00 AM:**
- This is NORMAL if market is choppy/sideways
- Bot is waiting for high-probability setups
- Check Activity Feed for "Signal rejected" messages
- Bot will explain why each signal was rejected

---

## 🔍 TIMEZONE EXPLANATION (IMPORTANT)

**Cloud Run Server:**
- Runs in **UTC timezone** (Coordinated Universal Time)
- Logs show UTC timestamps

**Indian Stock Market:**
- Operates in **IST timezone** (India Standard Time)
- IST = UTC + 5:30 hours

**Conversion:**
- 9:15 AM IST = 3:45 AM UTC
- 3:30 PM IST = 10:00 AM UTC

**Bot's Market Hours Check** (in code):
```python
# _is_market_open() function uses pytz
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)  # Converts to IST
# Checks: 9:15 AM <= now <= 3:30 PM (IST)
```

**This is handled correctly** - bot knows it's IST market hours!

---

## 📊 TROUBLESHOOTING GUIDE

### Problem: No Trades All Day

**Check 1: Was backend healthy?**
```powershell
.\check_backend_health.ps1
```

**Check 2: Was bot actually running?**
- Dashboard shows "Bot Running" badge
- Activity Feed has recent messages (<2 min old)

**Check 3: Market conditions**
- Was market trending or sideways?
- Check Nifty 50 movement (if Nifty flat, stocks won't break out)

**Check 4: DR established?**
- Activity Feed should show "DR High: ₹XXX, DR Low: ₹XXX" around 10:30 AM
- If no DR messages, data fetch failed

**Check 5: Filters too strict?**
- Bot has 6+ entry filters
- If market choppy, most signals get rejected
- This is GOOD - prevents bad trades

---

## 🚨 WHEN TO STOP BOT IMMEDIATELY

1. **Backend health check fails** before starting
2. **"WebSocket disconnected"** error persists >1 minute
3. **No activity feed updates** for >5 minutes during market hours
4. **Orders not executing** in Paper mode (indicates API issue)
5. **Strange errors** in browser console (F12)

---

## 📝 SUMMARY - DECEMBER 22 ISSUE

**What Happened:**
- Backend service crashed repeatedly due to Firebase credentials error
- Service couldn't start, API was down
- Bot frontend couldn't communicate with backend
- Zero trades because backend was dead

**Current Status:**
- Backend FIXED (revision 00074 with Firebase ADC)
- Health check script added
- Pre-market checklist created

**Action Items:**
1. ✅ ALWAYS run `check_backend_health.ps1` before starting bot
2. ✅ Monitor Activity Feed for first 10 minutes
3. ✅ Understand DR strategy - no trades before 10:30 AM
4. ✅ Check logs if no activity for 5+ minutes

---

## 🔗 Quick Commands

**Check backend health:**
```powershell
.\check_backend_health.ps1
```

**Check IST time:**
```powershell
[System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'India Standard Time')
```

**Check recent logs:**
```powershell
gcloud logging read "resource.labels.service_name=trading-bot-service" --limit 10 --project tbsignalstream
```

**Check current revision:**
```powershell
gcloud run services describe trading-bot-service --region asia-south1 --format="value(status.latestReadyRevisionName)" --project tbsignalstream
```

**Expected**: `trading-bot-service-00074-fzb` (or newer)

---

## ✅ TODAY (Next Trading Day)

**9:00 AM IST:**
1. Run health check script
2. Open dashboard
3. Check IST time

**9:15 AM IST:**
1. Start bot
2. Monitor activity feed
3. Verify WebSocket connected

**10:30 AM IST:**
1. Check if DR established
2. Look for breakout signals
3. Monitor rejected signals

**3:00 PM IST:**
1. Review day's activity
2. Check if any positions open
3. Let bot close positions at 3:15 PM

---

**Remember**: The bot is CONSERVATIVE by design. No trades is better than bad trades!
