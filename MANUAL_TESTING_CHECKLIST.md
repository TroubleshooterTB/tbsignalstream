# MANUAL TESTING CHECKLIST - STEP BY STEP
**For:** Monday, January 12, 2026  
**Time Required:** 45-60 minutes  
**Status:** Print this and tick off each item as you test

---

## 🌙 TONIGHT (Before Sleep) - 15 Minutes

### Test 1: Dashboard Loads
- [ ] **Action:** Open https://studio--tbsignalstream.us-central1.hosted.app
- [ ] **Expected:** Page loads within 3 seconds
- [ ] **Expected:** You see the dashboard with sidebar navigation
- [ ] **Expected:** No blank white screen
- [ ] **How to verify:** Page shows "TBSignalStream" or similar branding

**If it fails:** Clear browser cache (Ctrl+Shift+Delete), try again

---

### Test 2: Browser Console Check
- [ ] **Action:** Press F12 on keyboard
- [ ] **Action:** Click "Console" tab
- [ ] **Expected:** No red error messages
- [ ] **Expected:** May see some gray/blue logs (normal)
- [ ] **How to verify:** Look for errors with ❌ or red text

**If you see errors:**
- Take screenshot
- Note the error message
- Try refreshing page (Ctrl+F5)

---

### Test 3: System Health Monitor
- [ ] **Action:** Look at top-right corner of dashboard
- [ ] **Expected:** See a "System Health" badge or indicator
- [ ] **Expected:** Shows "Healthy" in green
- [ ] **How to verify:** Badge color is green, not red or yellow

**If shows error:**
- Click on it to see details
- Check backend, WebSocket, Firestore status

---

### Test 4: Navigation Test
- [ ] **Action:** Click "Dashboard" in sidebar (left side)
- [ ] **Expected:** Stays on home page / no error
- [ ] **Action:** Click "Performance"
- [ ] **Expected:** Page changes to performance view
- [ ] **Action:** Click "Settings"
- [ ] **Expected:** Page changes to settings view
- [ ] **Action:** Click "Dashboard" again to return

**If navigation fails:** Note which link doesn't work

---

### Test 5: Bot Controls Visible
- [ ] **Action:** Go to Dashboard page
- [ ] **Expected:** See a card titled "Live Trading Bot" or "Trading Bot Controls"
- [ ] **Expected:** See dropdown menus for Universe and Strategy
- [ ] **Expected:** See "Start Bot" button (green)
- [ ] **Expected:** See "Stop Bot" button (gray/disabled)

**If not visible:** Try scrolling down the page

---

### Test 6: Universe Dropdown Test
- [ ] **Action:** Click on "Symbol Universe" dropdown
- [ ] **Expected:** Dropdown opens with 3 options
- [ ] **Expected:** Options are: "Nifty 50", "Nifty 100", "Nifty 200"
- [ ] **Action:** Click "Nifty 50 (Recommended)"
- [ ] **Expected:** Dropdown closes, shows selected value
- [ ] **Action:** Click dropdown again, select "Nifty 100"
- [ ] **Expected:** Selection changes to Nifty 100
- [ ] **Action:** Select "Nifty 200"
- [ ] **Expected:** Selection changes to Nifty 200
- [ ] **Action:** Select back to "Nifty 50"

**If dropdown doesn't work:** Try clicking directly on the text

---

### Test 7: Strategy Dropdown Test
- [ ] **Action:** Click on "Trading Strategy" dropdown
- [ ] **Expected:** Dropdown opens with multiple strategies
- [ ] **Expected:** First option is "⭐ Alpha-Ensemble"
- [ ] **Action:** Select "Alpha-Ensemble"
- [ ] **Expected:** Dropdown closes, shows selection
- [ ] **Expected:** See description text below: "⭐ VALIDATED: Multi-timeframe momentum..."

**If dropdown doesn't work:** Note it down, try other dropdowns

---

### Test 8: Input Fields Test
- [ ] **Action:** Find "Capital (₹)" input field
- [ ] **Action:** Click in the field
- [ ] **Action:** Type: 100000
- [ ] **Expected:** Field accepts the number
- [ ] **Expected:** Shows formatted: ₹1,00,000 or 100000
- [ ] **Action:** Find "Max Positions" field
- [ ] **Action:** Type: 3
- [ ] **Expected:** Field accepts the number
- [ ] **Action:** Find "Risk Per Trade (%)" field
- [ ] **Action:** Type: 1.5
- [ ] **Expected:** Field accepts the decimal

**If fields don't accept input:** Check if they're disabled (grayed out)

---

### Test 9: Paper Trading Toggle
- [ ] **Action:** Find "Paper Trading" switch/toggle
- [ ] **Action:** Click the toggle
- [ ] **Expected:** Toggle switches ON (usually blue or green)
- [ ] **Expected:** May see badge appear saying "Paper Trading Mode"
- [ ] **Action:** Click toggle again
- [ ] **Expected:** Toggle switches OFF

**If toggle doesn't work:** Try clicking the label text next to it

---

### Test 10: Activity Feed Exists
- [ ] **Action:** Scroll down to find "Bot Activity Feed" card
- [ ] **Expected:** See a card/panel with title "Bot Activity Feed" or "Activity Log"
- [ ] **Expected:** May show "Waiting for bot activity..." or similar message
- [ ] **Expected:** May be empty (that's OK for now)

**If not visible:** It might be on a different tab or section

---

### Test 11: Network Tab Check
- [ ] **Action:** With F12 open, click "Network" tab
- [ ] **Action:** Refresh page (Ctrl+R)
- [ ] **Expected:** See list of files loading (HTML, CSS, JS)
- [ ] **Action:** Look for anything in red or with status 404/500
- [ ] **Expected:** Most items should be status 200 (green or black)
- [ ] **Action:** Look for call to "health" endpoint
- [ ] **Expected:** Should see: trading-bot-service...run.app/health (status 200)

**If you see 404/500 errors:** Take screenshot, note the URL

---

### Test 12: Take Screenshots
- [ ] **Action:** Take screenshot of full dashboard (Print Screen)
- [ ] **Action:** Save as "dashboard-tonight-test.png"
- [ ] **Action:** Take screenshot of Console tab (F12)
- [ ] **Action:** Save as "console-tonight-test.png"
- [ ] **Action:** Take screenshot of Network tab
- [ ] **Action:** Save as "network-tonight-test.png"

**Purpose:** Evidence that everything worked tonight

---

**TONIGHT TESTING COMPLETE ✅**

**What you've verified:**
- ✅ Dashboard loads in browser
- ✅ No console errors
- ✅ Navigation works
- ✅ All UI components visible
- ✅ Dropdowns functional
- ✅ Input fields accept data
- ✅ Network calls succeed

**Sleep well! Tomorrow's test will be easier because you know the UI works.**

---

---

## 🌅 MONDAY MORNING (Before 9:15 AM) - 20 Minutes

### Pre-Market Setup (8:30 AM - 9:00 AM)

#### Test 13: Open Dashboard Fresh
- [ ] **Action:** Open new browser tab (private/incognito recommended)
- [ ] **Action:** Go to: https://studio--tbsignalstream.us-central1.hosted.app
- [ ] **Action:** Press F12 immediately
- [ ] **Action:** Go to Console tab
- [ ] **Expected:** Dashboard loads, no errors

---

#### Test 14: Configure Bot for First Run
- [ ] **Action:** Symbol Universe → Select "Nifty 50 (Recommended)"
- [ ] **Action:** Trading Strategy → Select "⭐ Alpha-Ensemble"
- [ ] **Action:** Capital → Enter: 100000
- [ ] **Action:** Max Positions → Enter: 3
- [ ] **Action:** Risk Per Trade → Enter: 1.5
- [ ] **Action:** Paper Trading → Toggle ON (must be enabled!)
- [ ] **Expected:** All fields accept input
- [ ] **Expected:** Configuration persists (doesn't reset)

**Double-check Paper Trading is ON! (very important)**

---

#### Test 15: Pre-Start Verification
- [ ] **Action:** Verify System Health shows "Healthy" (green)
- [ ] **Action:** Verify Activity Feed shows "Waiting for bot activity..."
- [ ] **Action:** Verify Bot status badge shows "Stopped"
- [ ] **Action:** Verify "Start Bot" button is green/enabled
- [ ] **Action:** Verify "Stop Bot" button is gray/disabled
- [ ] **Expected:** Everything matches above descriptions

---

#### Test 16: Start Bot (9:00 AM)
- [ ] **Action:** Take a deep breath 😊
- [ ] **Action:** Click "Start Bot" button
- [ ] **Expected:** Button changes to loading state (spinner appears)
- [ ] **Expected:** Button becomes disabled during loading
- [ ] **Expected:** Within 5-10 seconds, status changes to "Running"
- [ ] **Expected:** "Start Bot" button becomes disabled
- [ ] **Expected:** "Stop Bot" button becomes enabled (green)

**If button does nothing:**
- Check Console tab (F12) for errors
- Check Network tab for failed API call
- Try refreshing page and clicking again

---

#### Test 17: Watch Activity Feed (Critical!)
**Start timer: Give it 30 seconds**

- [ ] **Action:** Keep eyes on "Bot Activity Feed" section
- [ ] **Expected (within 30 sec):** See entry appear: "🚀 Bot STARTED"
- [ ] **Expected:** See timestamp (should be current time)
- [ ] **Expected (within 60 sec):** See entry: "📊 Using NIFTY 50 universe: 50 symbols"
- [ ] **Expected (within 90 sec):** See entry: "🔍 Initializing strategies..."

**If activity feed stays empty after 2 minutes:**
- **CRITICAL ISSUE** - Bot might not be working
- Check Console for errors
- Check if "Running" status is actually showing
- Take screenshots of Console and Network tabs

---

#### Test 18: Watch Console During Startup
- [ ] **Action:** With F12 open, watch Console tab
- [ ] **Expected:** May see logs appearing (gray/blue text)
- [ ] **Expected:** No red errors
- [ ] **Action:** Look for any messages about "Firestore" or "WebSocket"
- [ ] **Expected:** Should see successful connection messages

**If you see red errors:** Read the message carefully, take screenshot

---

#### Test 19: Verify Cloud Run Logs (Advanced)
**Only if you want extra confidence:**

- [ ] **Action:** Open new tab
- [ ] **Action:** Go to: https://console.cloud.google.com/run
- [ ] **Action:** Click "trading-bot-service"
- [ ] **Action:** Click "LOGS" tab
- [ ] **Expected:** See recent logs from last few minutes
- [ ] **Expected:** Look for log: "📊 Using NIFTY 50 universe: 50 symbols"
- [ ] **Expected:** No ERROR level logs

---

### Test 20: Wait for First Scan Cycle (9:05 AM - 9:15 AM)

**Bot needs a few minutes to initialize. Be patient!**

- [ ] **Action:** Watch Activity Feed
- [ ] **Expected (by 9:15 AM):** See entry: "🔍 Scan Cycle #1 started"
- [ ] **Expected:** See entry: "Scanning 50 symbols..." or similar
- [ ] **Expected:** Entries appear every 1-2 minutes
- [ ] **Action:** Note the timestamp of first scan cycle
- [ ] **Action:** Calculate: Time from "Start Bot" to "First Scan"
- [ ] **Expected:** Should be under 5 minutes

**If no scan cycles by 9:20 AM:**
- Something might be wrong
- Check Console for errors
- Check Cloud Run logs
- Consider restarting bot

---

---

## 📈 MARKET HOURS (9:15 AM - 10:00 AM) - 45 Minutes

### Test 21: Monitor Scan Cycles (9:15 AM - 9:30 AM)

- [ ] **Action:** Watch Activity Feed for 15 minutes
- [ ] **Expected:** New scan cycle every 1-3 minutes
- [ ] **Expected:** See entries like: "🔍 Scan Cycle #2", "#3", "#4", etc.
- [ ] **Expected:** Timestamps are sequential (getting newer)
- [ ] **Action:** Count total scan cycles in 15 minutes
- [ ] **Expected:** Should have 5-15 scan cycles (depends on speed)

**Record your count:** _____ scan cycles in 15 minutes

---

### Test 22: Watch for Pattern Detections

- [ ] **Action:** Keep watching Activity Feed
- [ ] **Expected:** May see: "🎯 Pattern detected on SYMBOL-EQ"
- [ ] **Expected:** May see: "✅ Signal generated: SYMBOL-EQ"
- [ ] **Note:** Patterns won't appear every scan (that's normal)
- [ ] **Note:** On some days, might take 30+ minutes for first pattern

**Don't worry if no patterns yet - markets vary. Keep monitoring.**

---

### Test 23: Check Trading Signals Table

- [ ] **Action:** Scroll to find "Trading Signals" or "Live Alerts" table
- [ ] **Expected:** Table exists (may be empty)
- [ ] **Action:** If pattern was detected, check if signal appears here
- [ ] **Expected:** Signal should show: Symbol, Entry, Target, SL, Confidence
- [ ] **Action:** Verify signal details match activity feed entry

**If signal detected in feed but not in table:**
- Wait 30 seconds (may have delay)
- Refresh page (Ctrl+R)
- Check Console for errors

---

### Test 24: Test Universe Change (9:30 AM)

**Only do this if everything working so far!**

- [ ] **Action:** Click "Stop Bot" button
- [ ] **Expected:** Status changes to "Stopped"
- [ ] **Expected:** Activity Feed shows: "🛑 Bot STOPPED"
- [ ] **Action:** Change Universe dropdown to "Nifty 100"
- [ ] **Action:** Click "Start Bot" again
- [ ] **Expected:** Bot starts successfully
- [ ] **Expected:** Activity Feed shows: "📊 Using NIFTY 100 universe: 100 symbols"

**This verifies universe selection actually works!**

---

### Test 25: WebSocket Status Check

- [ ] **Action:** Look for "WebSocket" status indicator
- [ ] **Expected:** Shows "Connected" in green
- [ ] **Expected:** May show number of subscribed symbols
- [ ] **Action:** Note the subscription count
- [ ] **Expected:** Should match universe size (50 or 100)

**If shows "Disconnected":**
- Click "Connect WebSocket" button if available
- Check Console for WebSocket errors

---

### Test 26: Performance Metrics (9:45 AM)

- [ ] **Action:** Click "Performance" in sidebar
- [ ] **Expected:** Page loads showing performance stats
- [ ] **Expected:** May show: Total Trades, Win Rate, P&L (all 0 if no trades yet)
- [ ] **Action:** Note which metrics are visible
- [ ] **Action:** Return to Dashboard

---

### Test 27: Settings Page Check

- [ ] **Action:** Click "Settings" in sidebar
- [ ] **Expected:** Settings page loads
- [ ] **Expected:** May see AngelOne connection button
- [ ] **Action:** Return to Dashboard

---

### Test 28: System Health Details

- [ ] **Action:** Click "System Health" badge/section
- [ ] **Action:** Click "Show Details" if available
- [ ] **Expected:** Shows status of:
  - Backend service
  - WebSocket connection
  - Firestore database
- [ ] **Expected:** All show "Healthy" or "Connected"

---

### Test 29: Console Clean Check (9:50 AM)

- [ ] **Action:** With F12 open, look at Console tab
- [ ] **Action:** Scan for any red errors
- [ ] **Expected:** No new errors since bot started
- [ ] **Expected:** May see informational logs (that's fine)

**Count errors (if any):** _____ red errors

---

### Test 30: Network Activity Check

- [ ] **Action:** F12 → Network tab
- [ ] **Action:** Look for recent API calls
- [ ] **Expected:** See periodic calls to backend (every few minutes)
- [ ] **Expected:** Status codes are 200 (OK)
- [ ] **Action:** Look for any failed calls (red, 404, 500)

**Count failed calls:** _____ failed requests

---

### Test 31: Firestore Live Data (Advanced)

**Only if you want to verify database:**

- [ ] **Action:** Open: https://console.firebase.google.com/project/tbsignalstream/firestore
- [ ] **Action:** Click "bot_activity" collection
- [ ] **Expected:** See recent entries from today
- [ ] **Expected:** Entries have timestamps, symbols, activity_type
- [ ] **Action:** Note the most recent entry time
- [ ] **Action:** Compare with Activity Feed on dashboard
- [ ] **Expected:** Should match (within 1 minute)

---

### Test 32: Take Evidence Screenshots (10:00 AM)

- [ ] **Action:** Screenshot full dashboard
- [ ] **Action:** Save as "dashboard-running-10am.png"
- [ ] **Action:** Screenshot Activity Feed close-up
- [ ] **Action:** Save as "activity-feed-10am.png"
- [ ] **Action:** Screenshot Console tab
- [ ] **Action:** Save as "console-10am.png"
- [ ] **Action:** Screenshot Cloud Run logs
- [ ] **Action:** Save as "cloudrun-logs-10am.png"

---

### Test 33: Final Verification Checklist

Answer YES or NO to each:

- [ ] **Dashboard loads without errors:** YES / NO
- [ ] **Bot starts successfully:** YES / NO
- [ ] **Activity feed populates:** YES / NO
- [ ] **Scan cycles running:** YES / NO
- [ ] **Universe selection works:** YES / NO
- [ ] **No console errors:** YES / NO
- [ ] **System health is green:** YES / NO
- [ ] **WebSocket connected:** YES / NO
- [ ] **Navigation works:** YES / NO
- [ ] **Configuration saves:** YES / NO

**If 8+ are YES:** ✅ System is working well!  
**If 5-7 are YES:** ⚠️ System works but has issues  
**If <5 are YES:** ❌ Major problems, don't trade live

---

---

## 📊 EVIDENCE COLLECTION

### Screenshots to Take

1. ✅ Dashboard loaded (tonight)
2. ✅ Console tab clean (tonight)
3. ✅ Network tab (tonight)
4. ✅ Dashboard with bot running (morning)
5. ✅ Activity feed with entries (morning)
6. ✅ Console after 45 minutes (morning)
7. ✅ Cloud Run logs (morning)

### Information to Record

**Bot Start Time:** _______  
**First Scan Cycle:** _______  
**Total Scans in 15 min:** _______  
**Patterns Detected:** _______  
**Signals Generated:** _______  
**Console Errors:** _______  
**Failed API Calls:** _______  

---

---

## 🚨 TROUBLESHOOTING GUIDE

### Problem: Dashboard doesn't load

**Symptoms:** Blank page, infinite loading  
**Check:**
- Internet connection working?
- Try different browser
- Clear cache (Ctrl+Shift+Delete)
- Try incognito mode

**Fix:** If still fails, check App Hosting deployment status

---

### Problem: Start Bot button does nothing

**Symptoms:** Click Start Bot, nothing happens  
**Check:**
- F12 → Console for errors
- F12 → Network tab for failed API call
- Check if all fields filled (universe, strategy, capital)

**Fix:**
- Refresh page, try again
- Check backend health endpoint
- Verify CORS not blocking request

---

### Problem: Activity feed stays empty

**Symptoms:** Bot shows "Running" but feed empty  
**Check:**
- Wait 2 full minutes (backend might be initializing)
- Check Console for Firestore errors
- Check Cloud Run logs for activity

**Fix:**
- Stop and restart bot
- Check Firestore permissions
- Verify backend is writing logs

---

### Problem: No scan cycles appearing

**Symptoms:** Activity shows bot started, but no scans  
**Check:**
- Cloud Run logs - is bot actually scanning?
- Check if market is open (9:15 AM - 3:30 PM)
- Console for errors

**Fix:**
- Restart bot
- Check Cloud Run service is running
- Verify AngelOne credentials

---

### Problem: Red errors in console

**Symptoms:** Console full of red error messages  
**Check:**
- Read the error message
- Note which file/line has error
- Check if it's blocking functionality

**Fix:**
- Take screenshot
- If bot still works, might be non-critical
- If bot doesn't work, needs debugging

---

### Problem: WebSocket shows disconnected

**Symptoms:** WebSocket status is red  
**Check:**
- Click "Connect WebSocket" button
- Check Console for WebSocket errors
- Check network connectivity

**Fix:**
- Refresh page
- Restart bot
- Check firewall/proxy settings

---

---

## ✅ SUCCESS CRITERIA

**Minimum Success (Good Enough for Monday):**
- ✅ Dashboard loads
- ✅ Bot starts
- ✅ Activity feed shows entries
- ✅ At least 1 scan cycle appears
- ✅ No critical errors

**Full Success (Ideal):**
- ✅ All navigation works
- ✅ All dropdowns functional
- ✅ Bot runs for 45+ minutes
- ✅ Multiple scan cycles
- ✅ Universe selection works
- ✅ At least 1 pattern detected
- ✅ System health stays green
- ✅ No console errors

**Advanced Success (Bonus):**
- ✅ Signals appear in table
- ✅ WebSocket stays connected
- ✅ Firestore updates in real-time
- ✅ Performance page shows data
- ✅ Cloud Run logs show detailed activity

---

---

## 📝 FINAL NOTES

### What's Normal
- Some days have no patterns (market dependent)
- Scan cycles may take 30-60 seconds each
- Activity feed may have 1-2 second delay
- WebSocket may briefly disconnect and reconnect

### What's NOT Normal
- Dashboard crashes or freezes
- Bot stops after few minutes
- Console full of red errors
- Activity feed never populates
- Scan cycles stop appearing

### When to Stop Testing
- **STOP if:** Critical errors, bot crashes repeatedly, data corruption
- **CONTINUE if:** Minor UI glitches, slow performance, occasional errors
- **PROCEED CAREFULLY if:** Bot works but feels unstable

---

---

## 🎯 YOUR CONFIDENCE LEVEL

After completing all tests, rate your confidence:

**How confident are you the system will work Monday?**
- [ ] 0-30%: Major issues found, don't use
- [ ] 30-60%: Some issues, use cautiously  
- [ ] 60-80%: Minor issues, mostly working
- [ ] 80-95%: Working well, confident
- [ ] 95-100%: Everything perfect!

**Your confidence:** _____%

---

**END OF CHECKLIST**

**Total Time:** ~60 minutes  
**Tests:** 33 items  
**Evidence:** 7 screenshots + recorded data  
**Outcome:** Clear GO/NO-GO decision for Monday

**Good luck! You've got this! 🚀**
