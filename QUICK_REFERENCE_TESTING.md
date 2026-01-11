# QUICK REFERENCE - Manual Testing
**Print this for your desk on Monday**

---

## 🌙 TONIGHT (15 min)
1. Open dashboard URL
2. Press F12 → Check Console (no red errors)
3. Click all navigation links
4. Test all dropdowns (Universe, Strategy)
5. Test input fields (Capital, Max Positions)
6. Toggle Paper Trading ON/OFF
7. Take 3 screenshots

**Goal:** Verify UI works before Monday

---

## 🌅 MONDAY 8:30 AM (20 min)
1. Open dashboard fresh (incognito mode)
2. F12 → Console tab open
3. Configure:
   - Universe: **NIFTY50**
   - Strategy: **Alpha-Ensemble**
   - Capital: **100000**
   - Max Positions: **3**
   - Risk: **1.5**
   - Paper Trading: **ON** ⚠️
4. Click "Start Bot"
5. Watch Activity Feed for:
   - "🚀 Bot STARTED"
   - "📊 Using NIFTY 50 universe: 50 symbols"
   - "🔍 Scan Cycle #1"

**Goal:** Bot starts and begins scanning

---

## 📈 MARKET HOURS 9:15-10:00 AM (45 min)
1. Monitor scan cycles (should see 5-15 in 15 min)
2. Watch for pattern detections
3. Check Console (no red errors)
4. Test universe change (NIFTY50 → NIFTY100)
5. Verify logs show "100 symbols"
6. Check System Health (stays green)
7. Take screenshots every 15 minutes

**Goal:** Bot runs smoothly for 45+ minutes

---

## ✅ SUCCESS = YES to all:
- [ ] Dashboard loads
- [ ] Bot starts
- [ ] Activity feed populates
- [ ] Scan cycles appear
- [ ] No critical errors
- [ ] Universe selection works
- [ ] System health green
- [ ] Runs for 45+ minutes

**If 6+ YES:** ✅ Good to go!  
**If <6 YES:** ⚠️ Don't trade live yet

---

## 🚨 STOP IMMEDIATELY IF:
- ❌ Console full of red errors
- ❌ Bot crashes repeatedly  
- ❌ Activity feed never populates
- ❌ Scan cycles stop after few minutes
- ❌ Dashboard freezes/crashes

---

## 📸 EVIDENCE TO COLLECT:
1. Dashboard screenshot (tonight)
2. Console screenshot (tonight)
3. Bot running screenshot (morning)
4. Activity feed screenshot (with entries)
5. Cloud Run logs screenshot
6. Final status screenshot (10 AM)

---

## 📞 QUICK CHECKS:

**Dashboard URL:**
https://studio--tbsignalstream.us-central1.hosted.app

**Backend Health:**
https://trading-bot-service-818546654122.asia-south1.run.app/health

**Cloud Run Logs:**
https://console.cloud.google.com/run → trading-bot-service → LOGS

**Firestore:**
https://console.firebase.google.com/project/tbsignalstream/firestore

---

## ⏰ TIMELINE:

| Time | Action | Duration |
|------|--------|----------|
| Tonight | UI Testing | 15 min |
| 8:30 AM | Bot Setup | 10 min |
| 8:40 AM | Start Bot | 5 min |
| 8:45 AM | Watch Initialization | 10 min |
| 9:00 AM | Monitor Pre-Market | 15 min |
| 9:15 AM | Monitor Scanning | 15 min |
| 9:30 AM | Test Universe Change | 10 min |
| 9:45 AM | Final Verification | 15 min |
| 10:00 AM | Collect Evidence | 10 min |

**Total:** ~1 hour 40 min (spread across tonight + Monday morning)

---

## 🎯 EXPECTED RESULTS:

**Activity Feed should show:**
```
🚀 Bot STARTED at 8:40:15
📊 Using NIFTY 50 universe: 50 symbols
🔍 Initializing strategies...
✅ Strategy initialized: Alpha-Ensemble
🔍 Scan Cycle #1 started
📊 Scanning 50 symbols...
🔍 Scan Cycle #2 started
📊 Scanning 50 symbols...
🎯 Pattern detected on RELIANCE-EQ
✅ Signal generated: RELIANCE-EQ @ ₹2450
```

**Console should show:**
- Gray/blue informational logs ✅
- No red error messages ✅
- Successful Firestore connections ✅

**System Health should show:**
- Backend: ✅ Healthy
- WebSocket: ✅ Connected  
- Firestore: ✅ Connected

---

## 💡 REMEMBER:

1. **Paper Trading MUST be ON** ⚠️
2. Start with NIFTY50 (50 stocks)
3. Give bot 2-3 minutes to initialize
4. No patterns detected is OK (market dependent)
5. Take screenshots as evidence
6. Monitor for 45+ minutes minimum
7. Stop if critical errors appear

---

**Good luck! 🚀**

**You've tested 70% already.**  
**This checklist covers the final 30%.**  
**You're well-prepared!**
