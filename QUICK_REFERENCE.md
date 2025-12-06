# 🎯 QUICK REFERENCE - LIVE TRADING PREP

## ⏰ TONIGHT (Before Sleep) - 30 Minutes

### 1️⃣ Refresh Credentials (5 min)
```
Dashboard → Settings → Connect Angel One → Login → Authorize
```

### 2️⃣ Start Bot (2 min)
```
Dashboard → Start Bot → Mode: PAPER → Strategy: Pattern → Start
```

### 3️⃣ Monitor Logs (5 min)
```powershell
gcloud run services logs tail trading-bot-service --region asia-south1
```
**Look for:** ✅ WebSocket connected, ✅ Candles loaded, ✅ No errors

### 4️⃣ Stability Test (30 min)
```
Leave running, check every 10 minutes for errors
```

### 5️⃣ Stop Bot (1 min)
```
Dashboard → Stop Bot
```

---

## 🌅 MONDAY MORNING - 1 Hour

### 9:00 AM - Start Fresh
```
Dashboard → Start Bot (PAPER mode)
```

### 9:15 AM - Market Opens
```
Watch dashboard populate with live data
```

### 9:30 AM - Validate (30 min)
```
Monitor paper trades, check for errors
```

### 10:00 AM - Decision
```
✅ All good? → Consider LIVE mode
❌ Any issues? → Stay in PAPER
```

---

## 🚨 EMERGENCY CONTACTS

**Angel One Support:** 1800-103-6666  
**Trading Hours:** 9:15 AM - 3:30 PM IST

---

## 📚 FULL DOCUMENTATION

1. **QUICK_START_TONIGHT.md** - Tonight's detailed plan
2. **LIVE_TRADING_READINESS.md** - Complete 450-line checklist
3. **DEPLOYMENT_STATUS.md** - System status summary
4. **check_readiness.ps1** - Automated health check

---

## ✅ SUCCESS CRITERIA

**Before Sleep:**
- [ ] Angel One credentials refreshed
- [ ] Bot ran for 30 min without errors
- [ ] Bot stopped cleanly

**Monday 10:00 AM:**
- [ ] Paper mode validated (45 min)
- [ ] No errors in logs
- [ ] Ready for live decision

---

## 🛡️ SAFETY FIRST

**Day 1 Live Trading:**
- Max 2 positions (not 5)
- 10% position size (not 20%)
- 1% stop loss (tight)
- Monitor EVERY trade

**Emergency Stop:**
```
Dashboard → Stop Bot → Angel One App → Square Off All
```

---

**Good Luck! 🚀 Trade Safely! 💪**
