# Live Trading & Backtesting Diagnosis - Dec 27, 2025

## 🚨 Critical Issues Identified

### 1. Backend Crash-Looping (FIXED)
**Problem**: Old worker instances crashing with `File /app/firestore-key.json was not found`

**Root Cause**: Old worker instances not getting shut down properly

**Fix Applied**:
- Deployed revision **00106** with `--min-instances=1`
- All fresh workers now using Application Default Credentials (ADC)
- Health endpoint confirmed working: ✅ Healthy

### 2. Live Trading Not Placing Trades

**Likely Causes**:
1. **Market Closed** - Bot won't generate signals when market is closed (9:15 AM - 3:30 PM IST)
2. **No Valid Patterns** - Alpha-Ensemble is highly selective, may not find opportunities
3. **Paper Mode Config** - Verify bot is configured correctly

**Diagnosis Steps**:

#### Check 1: Is Market Open?
```bash
# Indian market hours: 9:15 AM - 3:30 PM IST (Monday-Friday)
# If outside these hours, NO TRADES is NORMAL
```

#### Check 2: Is Bot Actually Running?
```bash
curl https://trading-bot-service-818546654122.asia-south1.run.app/health
# Should show: "active_bots": 1
```

#### Check 3: Check Backend Logs for Scan Activity
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service AND textPayload=~'Scanning'" --limit=20 --freshness=30m --project=tbsignalstream
```

**What to look for**:
- "📊 Scanning X symbols for pattern opportunities..."
- "✅ Pattern detected: [symbol]"
- "❌ No valid patterns found"

If you see **NO scan logs**, bot isn't running properly.  
If you see **"No valid patterns"**, bot is working but market conditions don't meet criteria.

#### Check 4: Verify Bot Activity in Firestore
```powershell
# Check bot_activity collection
python check_firestore_signals.py
```

### 3. Backtesting Not Working

**Possible Issues**:
1. Frontend not calling the backend endpoint correctly
2. Backend timeout (30s default for large backtests)
3. Missing credentials in backtest request

**Diagnosis Steps**:

#### Test Backtest Endpoint Directly
```powershell
# Get your Firebase auth token first
$idToken = "YOUR_FIREBASE_ID_TOKEN"

$backendUrl = "https://trading-bot-service-818546654122.asia-south1.run.app"

$body = @{
    strategy = "alpha-ensemble"
    start_date = "2025-12-20"
    end_date = "2025-12-27"
    symbols = "NIFTY50"
    capital = 100000
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$backendUrl/backtest" -Method POST -Body $body -ContentType "application/json" -Headers @{
    "Authorization" = "Bearer $idToken"
}

$response | ConvertTo-Json -Depth 10
```

#### Check Backend Logs for Backtest Errors
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service AND textPayload=~'backtest'" --limit=20 --freshness=1h --project=tbsignalstream
```

### 4. Activity Feed Empty (RESOLVED - By Design)

**Explanation**: Activity feed ONLY logs during SCAN CYCLES when bot is actively analyzing patterns.

**When logs appear**:
- ✅ During market hours (9:15 AM - 3:30 PM IST)
- ✅ Every 1-2 minutes during scanning
- ✅ When patterns detected

**When logs DON'T appear**:
- ❌ Market closed
- ❌ Bot just started (takes 1-2 min for first scan)
- ❌ Bot crashed (check backend errors)

## 🔧 Immediate Actions Required

### Action 1: Verify Bot Configuration

1. **Go to Dashboard**
2. **Check Bot Settings**:
   - Symbol Universe: NIFTY100 or NIFTY50 (start small)
   - Mode: Paper Trading (recommended for testing)
   - Strategy: Alpha-Ensemble
   - Max Positions: 5 (default)

3. **Start Bot**
4. **Wait 2-3 minutes** for initialization

### Action 2: Monitor Backend Health

```powershell
# Run this every 30 seconds for 5 minutes
for ($i=1; $i -le 10; $i++) {
    Write-Host "`n[$i/10] Checking at $(Get-Date -Format 'HH:mm:ss')..."
    curl -s https://trading-bot-service-818546654122.asia-south1.run.app/health
    Start-Sleep -Seconds 30
}
```

**Expected Output** (if working):
```json
{
  "active_bots": 1,
  "status": "healthy"
}
```

### Action 3: Check for Trading Signals in Firestore

```powershell
# Check if any signals were generated today
gcloud firestore export gs://tbsignalstream.appspot.com/firestore-backup --collection-ids=trading_signals
```

Or use Firebase Console:
https://console.firebase.google.com/project/tbsignalstream/firestore/data/trading_signals

## 🎯 Expected Behavior

### During Market Hours (9:15 AM - 3:30 PM IST):

**Healthy Bot**:
1. ✅ Backend health shows `active_bots: 1`
2. ✅ Logs show "Scanning X symbols..." every 1-2 minutes
3. ✅ Activity feed updates in real-time
4. ✅ Signals appear when patterns detected (not guaranteed every scan)

**Trades Placed**:
- **NOT guaranteed every day**
- Alpha-Ensemble is **highly selective**
- May wait days for perfect setup
- This is INTENTIONAL (quality over quantity)

### Outside Market Hours:

**Normal Behavior**:
1. ✅ Bot shows "Running" status
2. ✅ Backend health shows `active_bots: 1`
3. ❌ **NO scan logs** (market closed)
4. ❌ **NO activity feed updates** (nothing to scan)
5. ❌ **NO trades** (market closed)

## 📊 Key Metrics to Monitor

### 1. Backend Health
- **URL**: https://trading-bot-service-818546654122.asia-south1.run.app/health
- **Check**: Every 1 minute
- **Expected**: `{"active_bots": 1, "status": "healthy"}`

### 2. Activity Feed
- **Location**: Dashboard > Bot Activity Feed
- **Check**: Every 2 minutes during market hours
- **Expected**: New entries every 1-2 minutes

### 3. Trading Signals
- **Location**: Firestore > `trading_signals` collection
- **Check**: After each market day
- **Expected**: 0-5 signals per day (highly selective)

### 4. Orders
- **Location**: Firestore > `order_history` collection
- **Check**: After patterns detected
- **Expected**: Orders placed immediately after signal

## 🐛 Common Issues & Solutions

### Issue: Bot Shows "Running" But No Activity

**Diagnosis**:
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service AND severity>=ERROR" --limit=10 --freshness=10m --project=tbsignalstream
```

**Solutions**:
1. Check for errors in logs
2. Stop and restart bot
3. Check Angel One credentials validity
4. Verify market is open

### Issue: Backtesting Returns Error

**Common Errors**:
1. **"Missing credentials"** → Re-authenticate with Angel One
2. **"Timeout"** → Reduce date range or use smaller universe (NIFTY50)
3. **"Invalid date"** → Check date format (YYYY-MM-DD)

**Solution**: Test with minimal params first:
```json
{
  "strategy": "alpha-ensemble",
  "start_date": "2025-12-26",
  "end_date": "2025-12-27",
  "symbols": "NIFTY50",
  "capital": 100000
}
```

### Issue: No Trades in Live Mode

**Is This Really A Problem?**
- **NO** if market is closed
- **NO** if no patterns detected (normal)
- **YES** if bot not scanning at all

**Verify Bot is Scanning**:
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service AND textPayload=~'Scanning'" --limit=5 --freshness=5m --project=tbsignalstream
```

If you see **"Scanning..."** logs → Bot working correctly, just no opportunities  
If you see **NO logs** → Bot crashed or stuck, check errors

## 📝 Next Steps

1. **Wait for Market Open** (9:15 AM IST Monday-Friday)
2. **Start Bot 5 minutes before market opens**
3. **Monitor for first 30 minutes**:
   - Check activity feed updates
   - Check scan logs in Cloud Run
   - Check health endpoint
4. **If no activity after 30 min during market hours** → Report issue with:
   - Backend logs (last 30 min)
   - Frontend console screenshot
   - Firestore bot_activity collection screenshot

## 🚀 Deployment Status

- **Backend Revision**: 00106 ✅
- **Backend URL**: https://trading-bot-service-818546654122.asia-south1.run.app
- **Frontend URL**: https://studio--tbsignalstream.us-central1.hosted.app
- **Min Instances**: 1 (no cold starts)
- **Health**: ✅ Healthy
- **Firebase**: ✅ Using ADC
- **Angel One Credentials**: ✅ Loaded from Secret Manager

## 📞 Support Commands

### Quick Health Check
```powershell
curl https://trading-bot-service-818546654122.asia-south1.run.app/health
```

### Check Recent Errors
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service AND severity>=ERROR" --limit=5 --freshness=10m --project=tbsignalstream
```

### Check Bot Activity
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service AND textPayload=~'Bot started|Scanning|Pattern detected'" --limit=10 --freshness=30m --project=tbsignalstream
```

### Force Redeploy (if needed)
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup\trading_bot_service"
gcloud run deploy trading-bot-service --source . --region=asia-south1 --project=tbsignalstream --allow-unauthenticated --min-instances=1
```

---

**Last Updated**: December 27, 2025  
**Backend Revision**: 00106  
**Status**: ✅ System Operational
