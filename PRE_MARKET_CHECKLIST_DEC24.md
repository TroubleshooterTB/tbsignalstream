# PRE-MARKET CHECKLIST - December 24, 2025
## Market Opens: 9:15 AM IST (7.5 hours from now)

---

## ✅ COMPLETED (Backend Infrastructure)

### System Health
- [x] Frontend accessible (HTTP 200)
- [x] Backend service running (revision 00103)
- [x] Firebase/Firestore operational
- [x] Angel One credentials loaded (all 5 SET)
- [x] Health endpoint responding correctly
- [x] No crash loops or errors in logs
- [x] Service stable for 15+ minutes

### Critical Bugs Fixed
- [x] Firebase initialization (ADC working)
- [x] Credentials loading (all variants supported)
- [x] Environment variables cleaned up
- [x] Diagnostic endpoints working

---

## ⏳ PENDING (User Actions Required)

### Phase 1: Dashboard Testing (NEXT - Do Now!)
- [ ] **User logs into dashboard**
  - URL: https://studio--tbsignalstream.us-central1.hosted.app
  - Verify login works
  - Check Firebase authentication
  
- [ ] **Navigate to bot controls**
  - Find "Start Bot" button
  - Check settings panel (universe, interval, mode, strategy)
  - Verify UI is responsive

- [ ] **Connect Angel One account (if needed)**
  - Check if user credentials exist in Firestore
  - If not, complete Angel One connection flow
  - Verify JWT and feed tokens are stored

### Phase 2: Bot Start Test (After Phase 1)
- [ ] **Start bot in PAPER TRADING mode**
  - Select: NIFTY50 universe
  - Interval: 5minute
  - Mode: PAPER (NOT live!)
  - Strategy: alpha-ensemble
  - Click "Start Bot"

- [ ] **Verify bot started successfully**
  - Check if UI shows "Bot Running"
  - Look for green indicator or status change
  - Check for any error messages

- [ ] **Inspect Firestore data**
  - Open Firebase Console → Firestore
  - Navigate to `bot_instances` collection
  - Verify document created with user_id
  - Check fields: status, symbols, timestamp

### Phase 3: Activity Feed Verification (After Phase 2)
- [ ] **Check activity feed in dashboard**
  - Should show real-time updates
  - Look for: "Bot started" message
  - Wait 30 seconds - should see "Scanning symbols" logs

- [ ] **Verify Firestore activity logging**
  - Open `bot_activity` collection
  - Should have recent documents
  - Check timestamps are current (not hours old)

- [ ] **Check Cloud Run logs**
  - Run command:
    ```powershell
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service" --limit=20 --format="value(textPayload)" --project=tbsignalstream
    ```
  - Look for: "Starting bot for user..." 
  - Look for: WebSocket connection messages
  - No errors about credentials or Firebase

### Phase 4: Bot Stop Test (After Phase 3)
- [ ] **Stop bot from dashboard**
  - Click "Stop Bot" button
  - Verify UI updates to "Bot Stopped"
  
- [ ] **Verify bot stopped cleanly**
  - Check Firestore bot_instances (status should update)
  - Check activity feed for "Bot stopped" message
  - No error messages in logs

### Phase 5: WebSocket Testing (During Market Hours or Pre-Market)
- [ ] **Start bot at 8:45 AM (pre-market)**
  - This allows testing during live trading hours
  - Pre-market activity: 8:00 AM - 9:15 AM
  
- [ ] **Verify WebSocket connection**
  - Check logs for: "WebSocket connected"
  - Look for: Market data streaming messages
  - Activity feed should show symbol scans

- [ ] **Monitor for 15-30 minutes**
  - Bot should remain running (no crashes)
  - Activity feed should update regularly
  - No error messages about disconnections

### Phase 6: Final Pre-Market Check (9:00 AM - 9:15 AM)
- [ ] **Verify bot is still running**
  - Check dashboard shows "Running"
  - Activity feed has recent updates (< 1 min old)
  
- [ ] **Check system resources**
  - Cloud Run metrics (CPU < 80%, Memory < 80%)
  - No excessive errors in logs
  
- [ ] **Confirm paper trading mode**
  - CRITICAL: Verify bot is NOT in live trading mode
  - Check dashboard settings
  - Verify no real money at risk

---

## 🚨 TROUBLESHOOTING GUIDE

### Issue: Bot Won't Start
**Symptoms**: Click "Start Bot" but nothing happens or error message

**Check**:
1. Is user logged in? (Check browser console for auth errors)
2. Are Angel One credentials connected?
   - Go to Firestore → angel_one_credentials → [user_id]
   - Should have: jwt_token, feed_token, client_code
3. Check browser Network tab for API errors
4. Try: Log out and log back in

### Issue: Activity Feed Not Updating
**Symptoms**: Bot shows "Running" but activity feed is empty or stale

**Check**:
1. Open Firestore → bot_activity collection directly
   - Are documents being created?
   - Are timestamps current?
2. Check Cloud Run logs for errors
3. Verify Firestore rules allow reads
4. Try: Refresh browser page

### Issue: Bot Crashes or Stops Unexpectedly
**Symptoms**: Bot status changes from "Running" to "Stopped" without user action

**Check**:
1. Cloud Run logs for error messages:
   ```powershell
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service AND severity=ERROR" --limit=10 --project=tbsignalstream
   ```
2. Look for: Memory errors, timeout errors, API errors
3. Check: Firestore rules haven't blocked writes
4. Verify: Angel One tokens haven't expired

### Issue: WebSocket Not Connecting
**Symptoms**: Logs show "Failed to connect WebSocket" or similar

**Check**:
1. Market hours (WebSocket only works 9:00 AM - 3:30 PM)
2. Angel One feed_token is valid (expires daily)
3. Network connectivity from Cloud Run
4. Check: No IP blocks or rate limits from Angel One

---

## 📊 MONITORING COMMANDS

### Check Service Health
```powershell
curl https://trading-bot-service-818546654122.asia-south1.run.app/health
```
Expected: `{"status":"healthy","active_bots":0}` (or 1 when bot running)

### Check Credentials
```powershell
curl https://trading-bot-service-818546654122.asia-south1.run.app/check-credentials
```
Expected: All credentials show "SET", status "OK"

### View Recent Logs
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service" --limit=20 --format="table(timestamp,textPayload)" --project=tbsignalstream
```

### Check Cloud Run Metrics
```powershell
gcloud run services describe trading-bot-service --region=asia-south1 --format="value(status.url,status.latestReadyRevisionName)" --project=tbsignalstream
```

### Query Firestore (Bot Instances)
```powershell
gcloud firestore documents list --collection-id=bot_instances --project=tbsignalstream
```

---

## ⏰ TIMELINE

| Time | Action | Status |
|------|--------|--------|
| 1:45 AM | Backend audit complete | ✅ DONE |
| 2:00 AM | User testing (Phases 1-4) | ⏳ PENDING |
| 8:00 AM | Pre-market opens | ⏰ SCHEDULED |
| 8:45 AM | Start bot for pre-market test | ⏰ SCHEDULED |
| 9:00 AM | Final checks | ⏰ SCHEDULED |
| 9:15 AM | Market opens | ⏰ SCHEDULED |

---

## ✅ SUCCESS CRITERIA

Before declaring system "READY FOR TRADING":
1. ✅ User can log in successfully
2. ✅ User can start bot from dashboard
3. ✅ Bot appears as "Running" in UI
4. ✅ Activity feed shows real-time updates
5. ✅ Bot can be stopped cleanly from dashboard
6. ✅ WebSocket connects during market hours
7. ✅ No errors in Cloud Run logs
8. ✅ Bot stays running for 15+ minutes without crashes
9. ✅ Firestore data updates correctly
10. ✅ System resources within normal limits

---

## 🎯 FINAL GO/NO-GO DECISION

### GO if:
- All Phase 1-4 tests pass
- Bot runs stable for 15+ minutes
- Activity feed shows real-time updates
- No critical errors in logs
- User feels confident

### NO-GO if:
- Bot won't start or crashes repeatedly
- Activity feed not updating
- Critical errors in logs
- WebSocket won't connect
- User sees any concerning behavior

---

**Checklist Created**: December 24, 2025, 1:50 AM IST
**Market Opens In**: 7 hours 25 minutes
**Next Action**: USER MUST TEST DASHBOARD NOW
