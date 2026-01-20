# 🚀 QUICK START GUIDE - Get Bot Trading Today

## The Problem

**Bot hasn't been properly started.** All code is working, but bot needs to be initialized through the frontend dashboard.

---

## The Solution (5 Steps - 15 Minutes)

### Step 1: Deploy to Cloud Run (5 min)

```bash
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"

# Deploy backend service
cd trading_bot_service
gcloud run deploy trading-bot-service \
  --source . \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --project tbsignalstream \
  --timeout=3600 \
  --memory=2Gi \
  --cpu=2
```

**Output**: You'll get a service URL like:
```
Service URL: https://trading-bot-service-xxxxx-asia-south1.run.app
```

**Save this URL!**

### Step 2: Update Configuration (1 min)

Edit `cloud_run_config.json`:
```json
{
  "service_url": "https://trading-bot-service-xxxxx-asia-south1.run.app"
}
```

### Step 3: Set Angel One Credentials (2 min)

```bash
gcloud run services update trading-bot-service \
  --region asia-south1 \
  --project tbsignalstream \
  --set-env-vars="ANGEL_API_KEY=YOUR_KEY,ANGEL_CLIENT_CODE=YOUR_CODE,ANGEL_PASSWORD=YOUR_PASSWORD,ANGEL_TOTP_SECRET=YOUR_SECRET"
```

**Replace with your actual credentials!**

### Step 4: Test Backend (1 min)

```bash
# Test health endpoint
curl https://trading-bot-service-xxxxx-asia-south1.run.app/health

# Should return:
# {"status":"healthy","timestamp":"2026-01-21..."}
```

### Step 5: Start Bot via API (2 min)

Create a test file `start_bot_test.sh`:

```bash
#!/bin/bash

# Replace with your service URL
SERVICE_URL="https://trading-bot-service-xxxxx-asia-south1.run.app"

# Replace with your Firebase auth token (get from frontend login)
AUTH_TOKEN="YOUR_FIREBASE_AUTH_TOKEN"

# Start bot
curl -X POST "${SERVICE_URL}/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d '{
    "symbols": "NIFTY50",
    "interval": "5minute",
    "mode": "paper",
    "strategy": "alpha-ensemble"
  }'
```

Run it:
```bash
bash start_bot_test.sh
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Trading bot started for 50 symbols (Mode: paper, Strategy: alpha-ensemble)",
  "symbols": "NIFTY50",
  "interval": "5minute",
  "mode": "paper",
  "strategy": "alpha-ensemble"
}
```

---

## Verify It's Working

### Check 1: Firestore (30 seconds)

```bash
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
python firestore_diagnostic.py
```

**You should now see:**
- ✅ `bot_config` document created
- ✅ `activity_feed` showing "BOT_STARTED"
- ✅ `bot_status` showing "running"

### Check 2: Cloud Run Logs (30 seconds)

```bash
gcloud logging tail "resource.type=cloud_run_revision" \
  --project tbsignalstream \
  --limit 20
```

**You should see:**
```
🔴 REAL-TIME MODE ACTIVE
Fetching symbol tokens...
✅ Fetched tokens for 50 symbols
🔧 Initializing trading managers...
🔌 Initializing WebSocket connection...
✅ WebSocket initialized and connected
📊 Bootstrapping historical candle data...
✅ Historical candles loaded
🚀 Real-time trading bot started successfully!
```

### Check 3: Activity Feed (Every 5 min)

Re-run firestore diagnostic:
```bash
python firestore_diagnostic.py
```

**You should see increasing activity:**
```
BOT_STARTED: Real-time bot initialized
WEBSOCKET_CONNECTED: Connected to Angel One
SYMBOLS_SUBSCRIBED: 50 symbols
SYMBOL_SCANNED: RELIANCE (1/50)
SYMBOL_SCANNED: TCS (2/50)
...
SIGNAL_DETECTED: INFY - Bullish pattern
SCREENING_STARTED: INFY
```

---

## If Bot Doesn't Start

### Issue: "Angel One credentials not found"

**Solution**: Bot needs credentials in Firestore, not just environment variables.

Create a script `save_credentials_firestore.py`:

```python
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("../firestore-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Your Angel One credentials
credentials_data = {
    'api_key': 'YOUR_API_KEY',
    'client_code': 'YOUR_CLIENT_CODE',
    'jwt_token': 'YOUR_JWT_TOKEN',  # Get from Angel One login
    'feed_token': 'YOUR_FEED_TOKEN',  # Get from Angel One login
    'refresh_token': 'YOUR_REFRESH_TOKEN',
    'totp_secret': 'YOUR_TOTP_SECRET'
}

# Save to Firestore (replace 'your_user_id' with actual user ID)
user_id = 'your_user_id'  # From Firebase Auth
db.collection('angel_one_credentials').document(user_id).set(credentials_data)

print(f"✅ Credentials saved for user: {user_id}")
```

Run it:
```bash
python save_credentials_firestore.py
```

### Issue: "Failed to start bot"

Check Cloud Run logs for detailed error:
```bash
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=20 \
  --project tbsignalstream \
  --format=json
```

### Issue: "No signals after 1 hour"

**Possible causes:**
1. Market is closed (check time: must be 9:15 AM - 3:30 PM IST)
2. Liquidity filter blocking (12:00 PM - 2:30 PM blocked)
3. All signals filtered by screening
4. Symbols have no patterns matching criteria

**Check activity feed** - should show "SYMBOL_SCANNED" every 5 seconds for all 50 symbols.

---

## Expected Timeline (First Hour)

| Time | What Should Happen |
|------|-------------------|
| 09:15:00 | Bot starts, connects WebSocket |
| 09:15:10 | Historical data bootstrapped |
| 09:15:15 | Symbols subscribed, prices flowing |
| 09:15:20 | First scan cycle (50 symbols) |
| 09:15:40 | Scan complete |
| 09:15:45 | First signal detected (if market conditions match) |
| 09:16:00 | Position monitoring active |
| 09:20:20 | Second scan cycle starts |
| 10:00:00 | Should have 5-10 signals by now |
| 12:00:00 | Entry blocking starts (liquidity filter) |
| 14:30:00 | Entry blocking ends |
| 15:15:00 | EOD auto-close warning |
| 15:20:00 | All positions auto-closed |

---

## Paper Trading Test (Day 1)

### Goals
- ✅ Bot runs without crashing
- ✅ Signals generated (2-5 per hour expected)
- ✅ Orders placed (paper mode - no real money)
- ✅ Positions tracked correctly
- ✅ Stop losses work
- ✅ EOD auto-close works

### Monitoring
Check every hour:
```bash
python firestore_diagnostic.py
```

Look for:
- **Activity count increasing** (should be 100+ entries after 1 hour)
- **Signals appearing** (2-5 per hour)
- **Orders being created** (1-3 per hour)
- **Positions opening and closing**

### Success Criteria
After 1 day of paper trading:
- [ ] Bot ran for full market hours (6+ hours)
- [ ] Generated 15+ signals
- [ ] Placed 5+ paper orders
- [ ] No crashes or errors in logs
- [ ] Activity feed shows complete timeline
- [ ] Performance matches backtest (roughly)

---

## Go Live (Day 2)

**Only if paper trading successful!**

Stop bot:
```bash
curl -X POST "${SERVICE_URL}/stop" \
  -H "Authorization: Bearer ${AUTH_TOKEN}"
```

Restart in LIVE mode:
```bash
curl -X POST "${SERVICE_URL}/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d '{
    "symbols": "NIFTY50",
    "interval": "5minute",
    "mode": "live",
    "strategy": "alpha-ensemble"
  }'
```

**Start with limited capital!**
- Max 2-3 positions
- Small position sizes
- Monitor closely for first week

---

## Emergency Stop

If anything goes wrong:

```bash
# Stop bot immediately
curl -X POST "${SERVICE_URL}/stop" \
  -H "Authorization: Bearer ${AUTH_TOKEN}"

# Or set emergency stop flag in Firestore
# (bot checks this every 5 seconds)
python -c "
import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate('../firestore-key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
db.collection('bot_configs').document('YOUR_USER_ID').update({
    'emergency_stop': True
})
print('Emergency stop activated!')
"
```

---

## Troubleshooting Commands

```bash
# Check if bot is running
curl "${SERVICE_URL}/status"

# View real-time logs
gcloud logging tail "resource.type=cloud_run_revision" --project tbsignalstream

# Check Firestore data
python firestore_diagnostic.py

# Check code structure
python critical_diagnostic.py

# Test all features
python quick_test.py

# Restart Cloud Run service
gcloud run services update trading-bot-service --region asia-south1 --project tbsignalstream
```

---

## Success Checklist

### Backend
- [ ] Cloud Run service deployed
- [ ] Service URL in cloud_run_config.json
- [ ] Health endpoint responding
- [ ] Credentials configured

### Firestore
- [ ] bot_config document exists
- [ ] bot_status shows "running"
- [ ] activity_feed populating
- [ ] angel_one_credentials saved

### Bot Engine
- [ ] WebSocket connected
- [ ] Historical data loaded
- [ ] Symbols subscribed
- [ ] Scan cycles executing
- [ ] Signals being generated

### Paper Trading
- [ ] Orders created
- [ ] Positions tracked
- [ ] Stop losses monitored
- [ ] EOD close working

### Ready for Live
- [ ] 1 full day of successful paper trading
- [ ] Performance matches expectations
- [ ] No errors or crashes
- [ ] Activity feed shows complete workflow

---

**Last Updated**: January 21, 2026  
**Status**: Ready to deploy and test  

**Next Step**: Run Step 1 (Deploy to Cloud Run) NOW!
