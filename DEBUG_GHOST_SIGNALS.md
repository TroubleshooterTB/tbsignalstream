# 🔍 Ghost Signals Debug Guide

## Current Time
**December 3, 2025 - 11:45 PM IST**

## The Mystery
Three signals appear every day:
- **INFY** - ₹1578.70 - 98% - Breakout - "News catalyst and high volume"
- **HDFCBANK** - ₹1000.50 - 92% - Momentum - "Strong relative strength vs NIFTY"
- **RELIANCE** - ₹1538.80 - 95% - Breakout - "Volume spike, opening range breakout"

## Verified Facts
✅ Firestore `trading_signals` collection is **COMPLETELY EMPTY** (verified multiple times)
✅ Source code has **NO hardcoded values** for these prices
✅ localStorage/sessionStorage **cleared on mount**
✅ No service worker caching
✅ Browser console shows 404 errors for `/analysis/*` pages, **proving signals ARE rendering**

## What We Changed (Not Yet Deployed)
1. ✅ Removed broken `/analysis/{ticker}` links (caused 404s)
2. ✅ Added comprehensive logging to trace signal sources
3. ✅ Added "Clear All Signals" button
4. ✅ Added 5-minute age filter (blocks old signals)

## Debug Steps - DO THIS NOW

### Step 1: Open Browser Developer Tools
```
Press F12 in your browser
Go to Console tab
```

### Step 2: Clear EVERYTHING
```
In Console, run:
localStorage.clear()
sessionStorage.clear()
indexedDB.deleteDatabase('firebaseLocalStorageDb')
```

Then **hard refresh**: `Ctrl + Shift + R`

### Step 3: Watch Console Logs
You should see these logs when page loads:

```
[Dashboard] 📊 Firestore snapshot received: 0 total docs, 0 changes
```

**IF YOU SEE SIGNALS**, look for logs like:
```
[Dashboard] 🔍 Raw signal data: { symbol: "INFY", ... }
[Dashboard] ⏰ Signal age check: 720.5 minutes old (limit: 5 min)
[Dashboard] ❌ REJECTING OLD SIGNAL: INFY from 2025-12-02...
```

### Step 4: Check IndexedDB
In DevTools:
1. Go to **Application** tab
2. Click **IndexedDB** in left sidebar
3. Expand **firebaseLocalStorageDb** (if exists)
4. Look for any data containing "INFY", "HDFCBANK", "RELIANCE"

### Step 5: Check Network Tab
1. Go to **Network** tab
2. Refresh page
3. Filter for "firestore"
4. Check if any request returns signal data

## Expected Behavior After Fix

### When Market is CLOSED (like now, 11:45 PM):
```
✅ Dashboard loads
✅ Console shows: "Firestore snapshot received: 0 total docs"
✅ NO signals displayed
✅ NO 404 errors for /analysis pages
```

### When Market OPENS (tomorrow 9:15 AM) and Bot Running:
```
✅ Bot generates signals → writes to Firestore
✅ Console shows: "Raw signal data: {...}"
✅ Console shows: "Signal age check: 0.02 minutes old"
✅ Console shows: "✅ ACCEPTING FRESH SIGNAL"
✅ Signals appear in dashboard
```

## If Ghost Signals STILL Appear

### Check 1: Component State
In React DevTools:
1. Find `LiveAlertsDashboard` component
2. Check `alerts` state
3. See what's in the array

### Check 2: Next.js Build Cache
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
Remove-Item -Recurse -Force .next
npm run build
firebase deploy --only hosting
```

### Check 3: Browser Profile
Try in **Incognito/Private window**:
```
Ctrl + Shift + N (Chrome)
Ctrl + Shift + P (Firefox)
```

If signals DON'T appear in incognito → it's cached in your browser profile

## Firestore Verification Command
```powershell
# Run this to verify Firestore is empty
$TOKEN = gcloud auth print-access-token
$RESPONSE = Invoke-RestMethod -Uri "https://firestore.googleapis.com/v1/projects/tbsignalstream/databases/(default)/documents:runQuery" -Method Post -Headers @{Authorization="Bearer $TOKEN"; "Content-Type"="application/json"} -Body '{"structuredQuery":{"from":[{"collectionId":"trading_signals"}],"limit":50}}'
$RESPONSE | ConvertTo-Json -Depth 10
```

Expected: Only 1 result (empty response object), no actual documents

## Deploy Fixed Code
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"

# Build frontend
npm run build

# Deploy
firebase deploy --only hosting

# Wait 2 minutes for deployment
Start-Sleep -Seconds 120

# Open in browser with hard refresh
Start-Process "https://tbsignalstream.web.app"
# Then press Ctrl+Shift+R
```

## Manual Signal Cleanup (If Needed)
```powershell
# If you find signals in Firestore, run:
python clear_ghost_signals.py
```

## Report Back With
1. **Console logs** - Screenshot showing Firestore snapshot and any signal logs
2. **IndexedDB contents** - What you find in firebaseLocalStorageDb
3. **Network requests** - Any Firestore requests returning data
4. **Incognito test** - Do signals appear in private window?

---

**Next Steps**: Deploy this fix and test with the steps above. The comprehensive logging will tell us EXACTLY where these ghost signals are coming from.
