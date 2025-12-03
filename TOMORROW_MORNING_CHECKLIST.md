# ✅ Tomorrow Morning Checklist (Dec 4, 2025 - 9:15 AM IST)

## 🎯 What to Expect

The bot will now:
1. **Load 200+ historical candles** at startup (~25 seconds)
2. **Generate signals immediately** from 9:15 AM onwards
3. **Write signals to Firestore** with current timestamps
4. **Display in your dashboard** within seconds

---

## 📋 Step-by-Step Testing

### Before Market Opens (9:00-9:14 AM)

1. **Open your dashboard:** https://tbsignalstream.web.app

2. **Open Browser DevTools:**
   - Press `F12`
   - Go to **Console** tab
   - Clear console logs

3. **Clear any cached data:**
   ```javascript
   localStorage.clear()
   sessionStorage.clear()
   indexedDB.deleteDatabase('firebaseLocalStorageDb')
   ```

4. **Hard refresh the page:**
   - Press `Ctrl + Shift + R`

5. **Verify you're logged in:**
   - Should see "Angel One Connected - AABL713311"
   - If not, click "Connect Angel One"

---

### At 9:15 AM (Market Open)

1. **Start the bot:**
   - Click "Start Trading Bot" button
   - Should turn to "Stop" button with green "Running" badge

2. **Watch Cloud Run logs in new terminal:**
   ```powershell
   # Open PowerShell and run:
   gcloud logging tail "resource.type=cloud_run_revision 
     AND resource.labels.service_name=trading-bot-service" 
     --format="value(timestamp,textPayload)"
   ```

3. **What you should see in logs within 60 seconds:**
   ```
   📊 [CRITICAL] Bootstrapping historical candle data...
   Fetching historical data for RELIANCE (ONE_MINUTE)
   ✅ RELIANCE: Loaded 243 historical candles
   ✅ TCS: Loaded 237 historical candles
   ✅ HDFCBANK: Loaded 251 historical candles
   ... (49 symbols)
   📈 Historical data bootstrap complete: 49 success, 0 failed
   🎯 Bot ready for immediate signal generation!
   🚀 Real-time trading bot started successfully!
   ```

4. **If you see errors like:**
   ```
   ❌ RELIANCE: Failed to fetch historical data: 401 Unauthorized
   ```
   **This means:** Angel One credentials expired
   **Fix:** Click "Connect Angel One" button to refresh tokens

---

### Within 5-10 Minutes (9:15-9:25 AM)

1. **Watch for signal generation in logs:**
   ```
   🔍 [DEBUG] Scanning 49 symbols for trading opportunities...
   📊 [DEBUG] Candle data available for 49 symbols
   ✅ RELIANCE: Pattern detected | Confidence: 87.3% | R:R = 1:2.5
   💾 [DEBUG] Attempting to write RELIANCE signal to Firestore...
   ✅ [DEBUG] Signal written to Firestore! Doc ID: abc123xyz
   🎯 SIGNAL GENERATED: RELIANCE @ ₹1245.50 - Check dashboard NOW!
   ```

2. **Check browser console (F12):**
   ```
   [Dashboard] 📊 Firestore snapshot received: 1 total docs, 1 changes
   [Dashboard] 🔍 Raw signal data: {symbol: "RELIANCE", price: 1245.5, ...}
   [Dashboard] ⏰ Signal age check: 0.08 minutes old (limit: 5 min)
   [Dashboard] ✅ ACCEPTING FRESH SIGNAL
   ```

3. **Signal should appear in dashboard table:**
   - **Symbol:** RELIANCE (or other Nifty 50 stock)
   - **Price:** Current market price
   - **Type:** BUY or SELL
   - **Signal:** Breakout/Momentum/etc
   - **Confidence:** 85-95%
   - **Time:** Current session time (e.g., "9:18 AM")

---

## 🚨 Troubleshooting

### Problem: No logs appear after bot start

**Check:**
```powershell
gcloud run services describe trading-bot-service --region=asia-south1 --format="value(status.url)"
```

**Should return:** `https://trading-bot-service-818546654122.asia-south1.run.app`

**Then check status:**
```powershell
Invoke-RestMethod -Uri "https://trading-bot-service-818546654122.asia-south1.run.app/status"
```

---

### Problem: Logs show "401 Unauthorized" for historical data

**Cause:** Angel One tokens expired

**Fix:**
1. Go to dashboard
2. Click "Connect Angel One" button
3. Complete login flow
4. Restart bot

---

### Problem: Logs show "insufficient candle data"

**Before fix:** This was expected (needed 200 minutes)  
**After fix:** This should NOT appear (historical data loaded at startup)

**If you still see it:**
1. Check logs for "Bootstrapping historical candle data" message
2. If missing → Historical bootstrap failed
3. Check error messages above it
4. Likely cause: API rate limit or auth issue

---

### Problem: Signals appear but have OLD timestamps

**Example:** Signal shows "11:38 PM" when current time is 9:20 AM

**Cause:** Browser cache (ghost signals)

**Fix:**
1. Click "Clear All Signals" button in dashboard
2. Hard refresh (`Ctrl + Shift + R`)
3. Clear browser cache:
   ```javascript
   localStorage.clear()
   sessionStorage.clear()
   indexedDB.deleteDatabase('firebaseLocalStorageDb')
   ```

---

### Problem: Dashboard shows "Loading..." forever

**Check Firestore directly:**
```powershell
$TOKEN = gcloud auth print-access-token
Invoke-RestMethod -Uri "https://firestore.googleapis.com/v1/projects/tbsignalstream/databases/(default)/documents/trading_signals" `
  -Headers @{Authorization="Bearer $TOKEN"} | ConvertTo-Json -Depth 5
```

**If empty:** Bot hasn't generated signals yet (wait 5-10 more minutes)  
**If has data:** Frontend issue - check browser console for errors

---

## 📊 Success Metrics

After 30 minutes of trading (9:15-9:45 AM), you should have:

- ✅ **Cloud Run logs:** "Historical data bootstrap complete"
- ✅ **Cloud Run logs:** At least 1-3 "SIGNAL GENERATED" messages
- ✅ **Firestore:** 1-3 documents in `trading_signals` collection
- ✅ **Dashboard:** 1-3 signals displayed with current timestamps
- ✅ **Browser console:** No errors, only "ACCEPTING FRESH SIGNAL" messages

---

## 🎊 What Success Looks Like

### In Cloud Run Logs:
```
📊 [CRITICAL] Bootstrapping historical candle data...
📈 Historical data bootstrap complete: 49 success, 0 failed
🔍 [DEBUG] Scanning 49 symbols for trading opportunities...
✅ TCS: Pattern detected | Confidence: 91.2% | R:R = 1:2.8
🎯 SIGNAL GENERATED: TCS @ ₹3456.75 - Check dashboard NOW!
```

### In Browser Console:
```
[Dashboard] 📊 Firestore snapshot received: 1 total docs, 1 changes
[Dashboard] ⏰ Signal age check: 0.12 minutes old (limit: 5 min)
[Dashboard] ✅ ACCEPTING FRESH SIGNAL: TCS
```

### In Dashboard UI:
| Symbol | Type | Signal | Price | Confidence | Time |
|--------|------|--------|-------|------------|------|
| TCS | BUY | Breakout | ₹3456.75 | 91% | 9:18 AM |

---

## 📝 What to Report Back

Please share:

1. **Screenshot of Cloud Run logs** showing bootstrap completion
2. **Screenshot of dashboard** with first signal
3. **Screenshot of browser console** showing signal acceptance
4. **Time it took** from bot start to first signal

This will confirm the fix is working as expected!

---

## 🔧 Emergency Commands

### Stop bot if issues:
```powershell
# In browser: Click "Stop Trading Bot" button
# OR manually via API:
Invoke-RestMethod -Uri "https://trading-bot-service-818546654122.asia-south1.run.app/stop" `
  -Method Post -Headers @{Authorization="Bearer $(gcloud auth print-identity-token)"}
```

### Clear all Firestore signals:
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
python clear_ghost_signals.py
```

### Check bot status:
```powershell
# From dashboard: Look at "Bot Status" badge
# OR via logs:
gcloud logging read 'resource.type=cloud_run_revision 
  AND resource.labels.service_name=trading-bot-service' 
  --limit=10 --format="value(timestamp,textPayload)"
```

---

**Ready for tomorrow! The bot is now capable of generating signals from the very first minute of market open.** 🚀
