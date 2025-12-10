# ✅ TOMORROW MORNING CHECKLIST - PRINT THIS!

**Date**: December 10, 2025  
**Market Open**: 9:15 AM IST

---

## □ 9:00 AM - SETUP

- [ ] Open PowerShell terminal
- [ ] Navigate to project folder
- [ ] Open browser to: `https://studio--tbsignalstream.us-central1.hosted.app`
- [ ] Press **Ctrl + Shift + R** (hard refresh)
- [ ] Press **F12** (DevTools)
- [ ] Verify bot settings:
  - [ ] Mode: _____________ (Paper/Live/Simulation)
  - [ ] Portfolio: ₹100,000
  - [ ] Symbols: 49

---

## □ 9:15 AM - START BOT

- [ ] Click **"Start Trading Bot"** button
- [ ] Run monitoring command in terminal (see Quick Start guide)
- [ ] Watch dashboard for toast message

---

## □ 9:15-9:30 AM - WATCH STARTUP

### Expected Timeline:

| Time | Event | Status |
|------|-------|--------|
| 9:15:00 | Token fetching starts | ☐ |
| 9:16:00 | Tokens fetched (48/49) | ☐ |
| 9:18:00 | Managers initialized | ☐ |
| 9:18:10 | WebSocket connected | ☐ |
| 9:18:15 | Subscribed to 48 symbols | ☐ |
| 9:18:18 | Price data arriving | ☐ |
| 9:25:00 | Bootstrap complete | ☐ |
| 9:25:05 | **PRE-TRADE VERIFICATION** | ☐ |

---

## □ CRITICAL CHECK: PRE-TRADE VERIFICATION

### Must See ALL 4 Green Checkmarks:

- [ ] ✅ websocket_connected: True
- [ ] ✅ has_prices: True
- [ ] ✅ has_candles: True
- [ ] ✅ has_tokens: True

### Success Message:
```
✅ ALL CHECKS PASSED - Bot ready to trade!
🚀 Real-time trading bot started successfully!
```

- [ ] **I saw the success message** ✅ → PROCEED TO MONITORING
- [ ] **I did NOT see it** ❌ → STOP BOT, CONTACT DEVELOPER

---

## □ 9:30 AM - VERIFY HEALTHY

- [ ] Run health check command
- [ ] Status = "healthy"
- [ ] Dashboard shows "Running"
- [ ] Prices updating in real-time

---

## □ ONGOING - MONITOR

### Every 15 minutes:
- [ ] 9:45 AM - Health check
- [ ] 10:00 AM - Health check
- [ ] 10:15 AM - Health check
- [ ] 10:30 AM - Health check
- [ ] 10:45 AM - Health check
- [ ] 11:00 AM - Health check

### Every 30 minutes:
- [ ] 9:45 AM - Check for signals
- [ ] 10:15 AM - Check for signals
- [ ] 10:45 AM - Check for signals
- [ ] 11:15 AM - Check for signals

---

## □ 3:15 PM - EOD AUTO-CLOSE

- [ ] Bot closes all positions automatically
- [ ] Verify in logs: "EOD AUTO-CLOSE"
- [ ] All positions closed by 3:20 PM

---

## □ 3:30 PM+ - POST-MARKET

- [ ] Review trade logs
- [ ] Stop bot (if desired)
- [ ] Document any issues

---

## 🚨 IF ANYTHING GOES WRONG

- [ ] Click "Stop Trading Bot"
- [ ] Take screenshot
- [ ] Copy error logs
- [ ] Note timestamp
- [ ] Contact developer

---

## 📞 EMERGENCY STOP

**Firestore**: `bot_configs/{user_id}` → Set `emergency_stop = true`

---

## ✅ SUCCESS CRITERIA

**Bot is working if**:
- Startup completes in <15 min
- All 4 pre-trade checks pass
- Health returns "healthy"
- Dashboard shows real-time data
- Strategy analysis running

**Bot is NOT working if**:
- Startup hangs >15 min
- Any pre-trade check fails
- Health returns "degraded"
- No price updates after 5 min
- Errors in logs

---

**PRINT THIS AND KEEP NEXT TO COMPUTER!**

**Quick Start Guide**: See `TOMORROW_MORNING_QUICK_START.md`  
**Full Audit**: See `PRODUCTION_READY_AUDIT_DEC_9_2025.md`

---

**Good Luck! 🚀**
