# 🚀 QUICK START GUIDE - Monday Dec 15, 2025

## ✅ STRATEGY VALIDATED - v3.2 Results
- **43 trades** | **53.49% WR** | **₹24,095 profit (24.10%)**
- **Profit Factor:** 2.34 | **Expectancy:** ₹560/trade
- **Status:** ✅ **READY FOR LIVE TRADING**

---

## 📋 MORNING CHECKLIST (8:30-9:00 AM)

### 1. System Setup (5 minutes)
```powershell
# Open PowerShell
cd "d:\Tushar 2.0\tbsignalstream_backup"
.venv\Scripts\Activate.ps1
cd trading_bot_service
```

### 2. Final Validation (2 minutes)
```powershell
# Verify v3.2 configuration
python run_backtest_defining_order.py
# Should show: 43 trades, 53.49% WR, 24.10% returns
```

### 3. Launch Live Bot (9:00 AM)
```powershell
# START IN PAPER MODE FIRST!
python live_bot_v32.py
```

**When prompted:**
- API Key: `jgosiGzs`
- Client Code: `AABL713311`
- Trading Password: `1012`
- TOTP: `[6-digit code from authenticator]`
- **Trading Mode: 1 (PAPER)** ← Start here!

---

## 🎯 PAPER TRADING PHASE (9:15-11:00 AM)

**Watch for 2-3 paper trades to validate:**
- ✅ Signals generated in approved hours (14:00-15:05 best)
- ✅ No trades in toxic hours (10:00, 11:00, 12:00, 13:00)
- ✅ Blacklist working (no SBIN, POWERGRID, SHRIRAMFIN, JSWSTEEL)
- ✅ SL/TP levels reasonable

**If 2-3 paper trades look good:**
1. Stop bot (Ctrl+C)
2. Restart with Mode: 2 (LIVE)
3. Monitor closely

---

## 📊 EXPECTED DAY 1 PERFORMANCE

**Based on v3.2 backtest (10 days, 43 trades):**
- **Expected Trades Today:** 3-5
- **Expected Win Rate:** 50-55%
- **Expected P&L:** ₹2,000-2,500 (2-2.5%)

**Hourly Breakdown:**
| Hour | Activity |
|------|----------|
| 9:15-10:00 | Monitor only (10AM blocked) |
| 10:00-14:00 | Low activity (11, 12, 13 blocked) |
| **14:00-15:05** | **PRIME TIME** (most signals) |
| 15:05-15:30 | No new entries (late hour) |

---

## 🚨 RISK CONTROLS

### Auto-Stop Conditions
- **Daily Loss:** Stop if -₹5,000 (--5%)
- **Consecutive Losses:** Pause after 3 in a row
- **Win Rate:** Alert if <30% for the day

### Position Limits
- **Max Concurrent:** 5 positions
- **Max per Trade:** ₹10,000 (10% capital)
- **Max Trades/Day:** 8 (2x average)

---

## 🔧 TROUBLESHOOTING

### "No signals generated"
**Normal if:**
- Before 14:00 (peak hours are 14:00-15:05)
- Low market volatility
- All breakouts rejected by filters

**Action:** Wait for 14:00-15:00 window

### "All positions hitting SL"
**Check:**
- Are you trading in toxic hours? (10-13 should be blocked)
- Is market trending or choppy?
- Are rejected signals showing quality issues?

**Action:** Switch back to PAPER mode and review

### "Bot crashed/stopped"
**Action:**
```powershell
# Restart bot
python live_bot_v32.py
# Positions will be lost - manual intervention needed
```

---

## 📞 EMERGENCY CONTACTS

**Angel One Support:** 1800-123-xxxx  
**Bot Logs:** `live_trading_YYYYMMDD.log`  
**Trade History:** `live_trades_YYYYMMDD_HHMMSS.csv`

---

## ✅ GO/NO-GO DECISION

**BEFORE switching to LIVE mode, verify:**
- [ ] 2-3 successful paper trades
- [ ] No trades in toxic hours (10-13)
- [ ] Blacklist working (4 symbols skipped)
- [ ] SL/TP levels make sense
- [ ] Bot responding correctly to market
- [ ] Logs show proper filter logic

**If ALL checked → GO LIVE!**

---

## 🎉 SUCCESS METRICS

**End of Day 1 Targets:**
- [ ] 3-5 trades executed
- [ ] 45-55% win rate
- [ ] ₹1,500-3,000 profit
- [ ] No rule violations

**If Day 1 successful:**
✅ Continue with confidence on Day 2  
📈 Target: 50%+ WR, 2%+ daily returns  
🚀 Scale up after Week 1 if consistent

---

**DEPLOYMENT TIME:** Monday Dec 15, 2025, 9:00 AM IST  
**STRATEGY:** v3.2 - The Defining Order (Ironclad)  
**MODE:** Start PAPER → Switch to LIVE after validation  
**STATUS:** 🚀 **READY TO DEPLOY!**
