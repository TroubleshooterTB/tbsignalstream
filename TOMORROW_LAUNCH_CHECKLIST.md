# 🚀 DECEMBER 12, 2025 - LAUNCH CHECKLIST

## ⏰ Pre-Market Checklist (9:00 - 9:14 AM)

### Account Verification (5 mins)
- [ ] Log in to Angel One account
- [ ] Verify account is active (not blocked/frozen)
- [ ] Check available margin (₹50,000+ recommended)
- [ ] Verify no pending dues or charges

### Dashboard Setup (2 mins)
- [ ] Open browser
- [ ] Navigate to: https://studio--tbsignalstream.us-central1.hosted.app
- [ ] Verify dashboard loads correctly
- [ ] Check "Bot Status: Stopped 🔴"

### System Verification (2 mins)
- [ ] Check stable internet connection
- [ ] Verify current time is 9:00-9:14 AM
- [ ] Keep phone nearby for emergency stop
- [ ] Have Cloud Run logs ready (optional): https://console.cloud.google.com/run

---

## 🟢 At 9:15 AM SHARP - START BOT

### Step 1: Start Bot (30 seconds)
```
1. Click "Start Bot" button on dashboard
2. Wait for confirmation message
3. Check "Bot Status: Running 🟢"
4. Verify timestamp shows current time
```

### Step 2: Monitor Initialization (1-2 minutes)
**Watch for these log messages:**
```
✅ "Bot started successfully"
✅ "Fetching previous trading session data"
✅ "Loaded 375 historical candles for SBIN"
✅ "Loaded 375 historical candles for RELIANCE"
✅ (Repeat for all 50 stocks)
✅ "WebSocket connection established"
✅ "Subscribed to 50 tokens"
✅ "Pattern scanning started (1s interval)"
```

**CRITICAL: Verify this message appears:**
```
✅ "Loaded 375 historical candles"
```
If you see "Loaded 20 candles" or "Loaded 0 candles" → PROBLEM!

### Step 3: Wait for First Signal (3-5 minutes)
**Expected timeline:**
```
9:15:00 - Bot starts
9:15:05 - Historical data loaded (375 candles)
9:15:06 - Indicators calculated
9:15:07 - Pattern scan begins (every 1 second)
9:16:00 - First pattern detected (if any)
9:16:01 - Advanced screening validates
9:16:02 - Signal appears (if passes 95% + 3:1 criteria)
```

---

## 📊 What to Expect Today

### Scenario A: 1-3 Signals Generated ✅
**This is IDEAL!**
- Means strict criteria (95% + 3:1) found exceptional setups
- High probability of success
- Bot working perfectly
- **Action:** Monitor signals, let bot trade

### Scenario B: Zero Signals Generated ✅
**This is NORMAL with strict criteria!**
- 95% confidence is VERY strict
- 3:1 R:R is VERY strict
- Better zero signals than bad signals
- Bot is working correctly - just filtering everything out
- **Action:** Don't panic, don't lower criteria, check logs to see rejected patterns

### Scenario C: Bot Crashes with Error ❌
**This is UNEXPECTED (we fixed all bugs!)**
- Check Cloud Run logs for error message
- Look for `KeyError`, `AttributeError`, `IndexError`
- Take screenshot of error
- **Action:** Stop bot, report error details

---

## 🚨 Error Recognition

### ✅ EXPECTED LOG MESSAGES (Good)
```
"Pattern detected: Bull Flag on SBIN (confidence: 92%)"
  → Pattern found but rejected (below 95%)

"R:R ratio 2.5:1 below minimum 3.0:1"
  → Pattern found but R:R too low

"Advanced screening failed: Level 12 - Insufficient volume"
  → Pattern found but failed screening

"No signals generated this scan"
  → No patterns met all criteria (NORMAL)
```

### ❌ UNEXPECTED ERROR MESSAGES (Bad)
```
"KeyError: 'High'"
  → Column name mismatch (should be fixed!)

"KeyError: 'Close'"
  → Column name mismatch (should be fixed!)

"AttributeError: 'DataFrame' object has no attribute 'sma_20'"
  → Indicator calculation failed

"IndexError: list index out of range"
  → Not enough candles (should have 375!)
```

---

## 📱 Dashboard Monitoring

### Real-Time Signal Display
Watch the "Live Signals" section:
```
If signal appears:
- ✅ Symbol name (e.g., "SBIN")
- ✅ Pattern type (e.g., "Bull Flag")
- ✅ Confidence (should be ≥ 95%)
- ✅ Entry price
- ✅ Stop loss
- ✅ Target (should be 3X stop loss distance)
- ✅ R:R ratio (should be ≥ 3.0)
```

### Bot Performance Stats
Monitor these metrics:
- **Active Positions:** 0-5 (max limit is 5)
- **Win Rate:** Not measurable on Day 1
- **Total P&L:** Will update after trades close
- **Signals Generated:** 0-3 expected today

---

## 🛑 When to STOP Bot

### Mandatory Stop Conditions
```
❌ Any crash or error in logs
❌ Bot placing trades with confidence < 95%
❌ Bot placing trades with R:R < 3.0
❌ More than 5 positions open simultaneously
❌ Unusual behavior (rapid order placement)
```

### Optional Stop Conditions
```
⚠️ Internet becomes unstable
⚠️ You need to leave computer unattended
⚠️ Want to analyze signals before allowing trades
```

### How to Stop
```
1. Click "Stop Bot" button on dashboard
2. Wait for "Bot Status: Stopped 🔴"
3. Verify all positions are closed (or manually close)
4. Check final P&L
```

---

## 📞 Troubleshooting Quick Reference

### Problem: Bot Won't Start
```
Symptoms: Click "Start Bot" but status stays "Stopped"

Possible Causes:
1. Cloud Run service down
2. API credentials expired
3. Network connectivity issue

Actions:
1. Refresh dashboard
2. Check internet connection
3. Try starting again
4. Check Cloud Run logs
```

### Problem: Zero Historical Candles
```
Symptoms: Log shows "Loaded 0 historical candles"

Possible Causes:
1. Angel One API not responding
2. Market holiday (no previous session)
3. Incorrect date calculation

Actions:
1. Check if yesterday was market holiday
2. Verify Angel One API credentials
3. Bot can still work - will take 50 mins to build candles
```

### Problem: Signals Not Appearing in Dashboard
```
Symptoms: Logs show signals but dashboard empty

Possible Causes:
1. Firestore connection issue
2. Dashboard not refreshing
3. Frontend bug

Actions:
1. Refresh dashboard
2. Check browser console for errors
3. Verify Firestore database has signals
4. Check backend API is responding
```

### Problem: Bot Crashes During Trading
```
Symptoms: "Bot Status: Stopped 🔴" unexpectedly

Possible Causes:
1. Unhandled exception in code
2. Cloud Run timeout (unlikely - we have 3600s)
3. Memory limit exceeded (unlikely - we have 2Gi)

Actions:
1. Check Cloud Run logs immediately
2. Look for stack trace
3. Note exact error message
4. Report for debugging
```

---

## 📊 End-of-Day Review (3:30 PM)

### Data to Collect
```
1. Total signals generated: _____
2. Signals that became trades: _____
3. Total P&L: ₹_____
4. Win rate: ____%
5. Any errors encountered: _____
```

### Questions to Answer
```
1. Did bot run full session without crashes? YES / NO
2. Did historical data load correctly? YES / NO
3. Were any signals below 95% confidence? YES / NO
4. Were any signals below 3:1 R:R? YES / NO
5. Should we adjust criteria for tomorrow? YES / NO
```

### Files to Update
```
- DEPLOYMENT_STATUS.md (add today's results)
- LIVE_TRADING_READINESS.md (update with learnings)
- Create: TRADING_LOG_DEC12.md (detailed session notes)
```

---

## 🎯 Success Definition for Today

### PRIMARY GOALS (MUST ACHIEVE)
```
✅ Bot starts without errors
✅ Historical data loads (375 candles per stock)
✅ Indicators calculate successfully
✅ Pattern scanning runs continuously
✅ No crashes or KeyError exceptions
✅ Advanced screening runs without errors
```

### SECONDARY GOALS (NICE TO HAVE)
```
⭐ Generate 1-3 high-quality signals
⭐ Execute trades successfully
⭐ Close at least 1 position profitably
```

### NOT REQUIRED TODAY
```
❌ High signal count (zero is OK with strict criteria)
❌ Positive P&L (long-term metric)
❌ Win rate > 70% (need multiple days of data)
```

---

## 💡 Important Reminders

### About Zero Signals
```
Zero signals ≠ Bug
Zero signals = Strict filtering working correctly

With 95% confidence + 3:1 R:R:
- Only EXCEPTIONAL setups will pass
- Better to skip than take mediocre trades
- Quality over quantity philosophy
```

### About Computer/Internet
```
✅ Computer CAN be turned OFF after bot starts
✅ Internet ONLY needed for:
   - Starting bot (30 seconds)
   - Checking dashboard (1 minute)
   
❌ Computer does NOT need to stay on all day
❌ Internet does NOT need to be stable all day
❌ Dashboard does NOT need to stay open

Bot runs on Google Cloud Run (serverless)
```

### About Emergency Stop
```
If you see anything unusual:
1. Click "Stop Bot" immediately
2. Screenshot the error
3. Check Cloud Run logs
4. Report the issue
5. We'll fix and redeploy for afternoon session
```

---

## 🔗 Important Links

### Dashboard
https://studio--tbsignalstream.us-central1.hosted.app

### Cloud Run Service
https://console.cloud.google.com/run/detail/asia-south1/trading-bot-service

### Cloud Run Logs
https://console.cloud.google.com/logs/query

### Firestore Database
https://console.firebase.google.com/project/tbsignalstream/firestore

### GitHub Repository
https://github.com/TroubleshooterTB/tbsignalstream

---

## 📱 Contact Plan

### If Critical Issues Occur
```
1. Take screenshot of error
2. Note exact time error occurred
3. Copy error message from logs
4. Stop bot immediately
5. Report via chat/email with:
   - Screenshot
   - Error message
   - Time of occurrence
   - What you were doing
```

### Expected Response Time
```
During market hours (9:15 AM - 3:30 PM):
- Critical errors: 5-15 minutes
- Non-critical issues: 30-60 minutes

After market hours:
- Can wait for next session
- Or fix and test in afternoon if critical
```

---

## ✅ Final Pre-Launch Checks

### 5 Minutes Before Market Open (9:10 AM)
```
[ ] Dashboard open and loaded
[ ] Bot status shows "Stopped 🔴"
[ ] Internet connection stable
[ ] Angel One account verified
[ ] Margin available confirmed
[ ] Cloud Run logs accessible (optional)
[ ] Phone nearby for emergency
[ ] Calm and focused mindset ✅
```

### At 9:15 AM
```
[ ] Click "Start Bot"
[ ] Watch for "Running 🟢"
[ ] Monitor initialization logs
[ ] Verify 375 candles loaded
[ ] Relax and let bot work
```

---

## 🎊 You're Ready!

**Remember:**
- ✅ All critical bugs fixed (revision 00042-ktl)
- ✅ Comprehensive audit completed
- ✅ 95% confidence + 3:1 R:R criteria set
- ✅ Historical data bootstrap working
- ✅ End-to-end pipeline tested
- ✅ Bot runs on cloud (computer can be OFF)

**What to expect:**
- Bot will run smoothly WITHOUT crashes
- Zero signals is NORMAL and EXPECTED
- Quality over quantity
- Trust the strict filtering

**Confidence Level: 95%+ 🚀**

---

**Good luck with tomorrow's session!**  
**May the markets be profitable! 📈💰**

---

*Checklist created: December 11, 2025, 11:00 PM IST*  
*Bot revision: 00042-ktl*  
*Status: PRODUCTION READY ✅*
