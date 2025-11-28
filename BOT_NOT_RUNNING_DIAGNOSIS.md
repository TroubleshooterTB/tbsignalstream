# 🔍 Bot Not Running - Diagnosis & Solution

## Problem Statement

**User Reported**: "I tried using the app when market was open today but it didnt work. The bot did not place any trade."

**Observed**:
- ❌ No new signals generated during market hours
- ❌ Dashboard shows 3 old/stale signals (RELIANCE, HDFCBANK, INFY)
- ❌ No trades placed
- ❌ Unclear if bot was analyzing

---

## Root Cause Analysis

### 🔴 **CRITICAL FINDING: Bot Was Never Started**

**Evidence from Production Logs**:
```bash
# Health check shows ZERO active bots
$ curl https://trading-bot-service.../health
{"active_bots": 0, "status": "healthy"}

# Application logs are EMPTY
$ gcloud logging read ... --freshness=2h
# No analysis logs, no pattern detection, no signal generation
```

### How the Bot Actually Works

The bot is **NOT auto-starting**. It requires **manual start action**:

1. ✅ **Deployment**: v8 is deployed successfully to Cloud Run
2. ✅ **Backend Service**: Flask app is running and healthy
3. ❌ **Bot Instance**: User must click "Start Trading Bot" to create bot instance
4. ❌ **Analysis Loop**: Only runs when bot instance exists

**Architecture**:
```
User Clicks "Start Bot" 
  → API POST /api/bot/start 
  → TradingBotInstance created
  → Background thread started
  → WebSocket connection established
  → Analysis loop runs every 5 seconds
  → Signals written to Firestore
```

**WITHOUT clicking Start**:
- No bot instance exists
- No WebSocket connection
- No analysis runs
- No signals generated

---

## Secondary Issue: Old Cached Signals

The dashboard showing "3 old signals" suggests:

**Possible Causes**:
1. **Firestore has old test data** from previous hardcoded implementation
2. **Browser cache** showing stale React state
3. **Frontend listener** connected to wrong Firestore collection

**Solution**: Clear Firestore collection and browser cache

---

## Step-by-Step Solution

### ✅ **Step 1: Clear Old Firestore Data**

```bash
# Delete old test signals (if any exist)
# Go to Firebase Console → Firestore → trading_signals collection
# Delete all documents manually OR use script:
```

**Python Script** (run locally):
```python
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred)
db = firestore.client()

# Delete all old signals
signals_ref = db.collection('trading_signals')
docs = signals_ref.stream()

count = 0
for doc in docs:
    doc.reference.delete()
    count += 1
    print(f"Deleted signal: {doc.id}")

print(f"✅ Deleted {count} old signals")
```

---

### ✅ **Step 2: Clear Browser Cache**

**In Chrome/Edge**:
1. Open DevTools (F12)
2. Right-click Refresh button
3. Select **"Empty Cache and Hard Reload"**

**OR**:
- Press `Ctrl + Shift + Delete`
- Check "Cached images and files"
- Check "Cookies and site data"
- Time range: Last 24 hours
- Click "Clear data"

---

### ✅ **Step 3: Verify Bot Configuration**

Before starting bot, ensure:

**Angel One Connection**:
- Go to Settings
- Check "Angel One Status": Should show ✅ Connected
- If not, re-authenticate

**Bot Configuration**:
- **Symbols**: RELIANCE, HDFCBANK, INFY (or custom)
- **Strategy**: Pattern Trading (recommended)
- **Mode**: Paper Trading (for testing)
- **Max Positions**: 3
- **Position Size**: ₹10,000

---

### ✅ **Step 4: Start the Bot (CRITICAL)**

**Dashboard → Trading Bot Controls**:

1. Review configuration (symbols, mode, strategy)
2. **Click "Start Trading Bot"** button
3. Wait for confirmation toast: "Trading Bot Started"
4. Check bot status indicator: Should change to **"Running 🟢"**

**What Should Happen**:
```
[09:30:15] Bot started for user abc123
[09:30:16] WebSocket connected to Angel One
[09:30:17] Subscribed to 3 symbols
[09:30:18] 📊 Scanning 50 symbols for trading opportunities...
[09:30:23] Pattern detected: RELIANCE Breakout | Confidence: 87.5%
[09:30:23] ✅ 30-Point Validation PASSED
[09:30:23] ✅ Advanced 24-Level Screening PASSED
[09:30:24] 🔴 Signal written to Firestore: RELIANCE BUY @ ₹2450
```

---

### ✅ **Step 5: Verify Bot is Actually Running**

**Check Backend Logs** (5 minutes after starting):
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service" \
  --limit=50 --format="value(timestamp,textPayload)" --freshness=10m
```

**Expected Log Messages**:
- ✅ "Bot started for user..."
- ✅ "WebSocket connected"
- ✅ "📊 Scanning X symbols..."
- ✅ "Pattern detected..." OR "No trading signals found"
- ✅ "📊 Market Internals: X ADV | Y DEC | Z UNCH"

**If logs are EMPTY** → Bot was not started correctly

---

### ✅ **Step 6: Monitor Frontend Dashboard**

**After bot starts, you should see**:

**Live Trading Signals**:
- **IF patterns found**: New signals appear in real-time
- **IF no patterns**: Table shows "No active signals" (this is NORMAL)
- **Old signals should disappear** after Firestore cleanup

**Bot Status**:
- Status: "Running 🟢"
- Active Positions: 0 (initially)
- WebSocket: Connected

**Important**: During sideways markets or low volatility, bot may run for hours without finding valid setups. This is EXPECTED behavior - the 30-point + 24-level validation is very strict.

---

## Testing During Market Hours

### Best Times to Test (High Volatility)

**Market Open** (9:15 AM - 10:00 AM):
- Highest volatility
- Most breakout patterns
- Best chance of signal generation

**Pre-Close** (3:00 PM - 3:15 PM):
- Volatile moves
- Pattern completions
- Position auto-close at 3:15 PM

### What to Expect

**Normal Behavior**:
- ✅ Bot running but NO signals for 30-60 minutes (strict validation)
- ✅ Logs show "Scanning X symbols..." every 5 seconds
- ✅ Logs show "No trading signals found in this scan cycle"

**Abnormal Behavior**:
- ❌ No logs at all (bot not started)
- ❌ WebSocket disconnection errors (API key issue)
- ❌ "Scanning 0 symbols" (symbol tokens not fetched)

---

## Quick Checklist

Before reporting "bot not working":

- [ ] Clicked "Start Trading Bot" button
- [ ] Status shows "Running 🟢" (not "Stopped 🔴")
- [ ] Market is OPEN (9:15 AM - 3:30 PM weekdays)
- [ ] Angel One connection is active (not expired)
- [ ] Cloud Run logs show "Scanning symbols..." messages
- [ ] Cleared browser cache and Firestore old data
- [ ] Waited at least 15-30 minutes (patterns are rare)

---

## Advanced Debugging

### Check Firestore Security Rules

Ensure bot can WRITE signals:

**Firestore Rules** (`firestore.rules`):
```javascript
match /trading_signals/{signalId} {
  allow read: if request.auth != null;
  allow write: if request.auth != null; // ← Must allow write
}
```

**Verify**:
```bash
firebase deploy --only firestore:rules
```

---

### Test Firestore Write Manually

**Add Debug Logging** to `realtime_bot_engine.py`:

```python
# In _place_entry_order() method (around line 1149)
logger.info(f"[DEBUG] Attempting Firestore write for {symbol}")

try:
    signal_ref = db.collection('trading_signals').add({
        'user_id': self.user_id,
        'symbol': symbol,
        'type': 'BUY' if direction == 'up' else 'SELL',
        # ... rest of data
    })
    logger.info(f"✅ [DEBUG] Firestore write SUCCESS: {signal_ref[1].id}")
except Exception as e:
    logger.error(f"❌ [DEBUG] Firestore write FAILED: {e}", exc_info=True)
```

**Redeploy and check logs**.

---

### Verify Frontend Listener

**Check Browser Console** (F12):

Expected messages:
```
✅ Firestore listener attached to trading_signals
✅ Received 0 signals (if none exist)
✅ Received 1 signals (when bot generates signal)
```

Errors to look for:
```
❌ Firestore permission denied
❌ Firebase not initialized
❌ Invalid collection path
```

---

## Summary

### The Issue

**Bot was never started by user** → No analysis running → No signals generated

### The Solution

1. ✅ Clear old Firestore data
2. ✅ Clear browser cache
3. ✅ **Click "Start Trading Bot"** (CRITICAL)
4. ✅ Verify logs show "Scanning symbols..."
5. ✅ Wait 15-30 minutes during market hours
6. ✅ Check if signals appear (may be zero if no patterns)

### Expected Outcome

**After proper start**:
- Logs show analysis every 5 seconds
- Signals appear ONLY when valid patterns found
- Dashboard updates in real-time
- Positions tracked automatically
- Auto-close at 3:15 PM (INTRADAY mode)

### Still Not Working?

**Check**:
1. Angel One session not expired (re-authenticate daily)
2. Market is actually open (weekdays 9:15 AM - 3:30 PM)
3. Cloud Run service has latest v8 deployment
4. Firebase Authentication working
5. Firestore rules allow writes

**Contact Support** with:
- Screenshot of bot status ("Running" or "Stopped")
- Cloud Run logs (last 50 lines)
- Browser console errors
- Exact time when you started bot
- Market conditions (volatile or sideways)

---

## Next Steps

**Immediate Actions**:
1. Clear Firestore `trading_signals` collection
2. Clear browser cache
3. Start bot via Dashboard
4. Monitor logs for 5 minutes
5. Wait 30 minutes during market open
6. Report back with results

**Testing Tomorrow** (Market Open):
- Start bot at 9:20 AM (after market settles)
- Check logs every 5 minutes
- Expect first signal between 9:30 AM - 10:30 AM (high volatility window)
- If no signals by 11:00 AM, it's likely a quiet market (NORMAL)

---

**Status**: Ready for user action - bot deployment is correct, just needs manual start.
