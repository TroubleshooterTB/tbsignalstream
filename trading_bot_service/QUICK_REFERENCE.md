# 🎯 ALPHA-ENSEMBLE SCREENER - QUICK REFERENCE

## ⚡ Quick Commands

### 1️⃣ First Time Setup (Run Once)
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup\trading_bot_service"
python fetch_nifty200_symbols.py
```
**Time:** 2-3 minutes | **Output:** `nifty200_constituents.json`

---

### 2️⃣ Quick Validation Test
```powershell
python quick_test_screener.py
```
**Time:** 30 seconds | **Output:** Top 25 candidates for test date

---

### 3️⃣ Full Backtest
```powershell
python test_alpha_screener.py
```
**Time:** 5 min (1 day) to 90 min (1 month)  
**Output:** Complete performance summary

---

## 📊 Key Metrics to Watch

| Metric | Target | Current Status |
|--------|--------|----------------|
| **Win Rate** | >40% | 50-stock: 42.39% ✅ |
| **Profit Factor** | >2.5 | 50-stock: 3.75 ✅ |
| **Expectancy (Φ)** | Positive | 50-stock: ₹~15k ✅ |
| **Trades/Year** | 100+ | 50-stock: 92 → Target: 100+ |
| **Max Drawdown** | <20% | To be tested |
| **Total Return** | >100%/yr | 50-stock: +2,072% ✅ |

---

## 🔄 System Flow (1 Trading Day)

```
10:30 AM
    ↓
Fetch Nifty 50 data (9:15-10:30)
    ↓
Calculate Nifty direction (BULLISH/BEARISH/NEUTRAL)
    ↓
Screen all 200 stocks:
  ✓ Sector + Nifty alignment (>0.3%)
  ✓ ATR (1-4%)
  ✓ ADX >25
  ✓ Volume >2x
    ↓
Rank by composite score
    ↓
Select TOP 25
    ↓
Monitor for retest signals (10:30-15:15)
    ↓
Execute trades with 2.5:1 R:R
    ↓
Square off at 15:15
```

---

## 🎯 4-Layer Filtering

### Layer 1: Market Regime
- Nifty/Sector alignment >0.3%
- Skip if VIX >22 (future)

### Layer 2: Screening (Top 25 from 200)
1. Market/Sector move >0.3%
2. Daily ATR: 1.0-4.0%
3. ADX(14) >25 on 15-min
4. Volume >2.0x time-adjusted average

### Layer 3: Execution Filters (5-Factor)
1. ADX >25 ✓
2. Volume >2.5x ✓
3. RSI sweet spot (55-65 LONG, 35-45 SHORT) ✓
4. EMA50 distance <2% ✓
5. ATR window 0.10-5.0% ✓

### Layer 4: Risk Management
- 2.5:1 R:R
- SL: max(1.5x ATR, retest candle), cap 0.7%
- Break-even at 1:1 R:R
- 1% risk per trade, 5x MIS leverage
- Time exit: 15:15

---

## 📁 File Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `fetch_nifty200_symbols.py` | Get tokens | Once (setup) |
| `quick_test_screener.py` | Validate screening | Before backtest |
| `test_alpha_screener.py` | Full backtest | Main testing |
| `alpha_ensemble_screener.py` | Core engine | Auto-imported |
| `README_ALPHA_SCREENER.md` | Full docs | Read for details |
| `EXECUTION_GUIDE.md` | Step-by-step | Follow workflow |
| `BUILD_SUMMARY.md` | Overview | Understand system |
| `QUICK_REFERENCE.md` | This file | Quick lookup |

---

## 🔧 Common Issues & Fixes

### ❌ "nifty200_constituents.json not found"
**Fix:** Run `python fetch_nifty200_symbols.py`

### ❌ "Invalid Token" during backtest
**Fix:** System will prompt for new TOTP - have authenticator ready

### ❌ "0 candidates found"
**Cause:** Market NEUTRAL (<0.3% move) or no stocks met criteria  
**Fix:** Try different date or relax filters

### ❌ "No retest signals"
**Cause:** Normal - not every breakout gets retest  
**Fix:** Extend backtest period

---

## 🎓 Strategy in 30 Seconds

**What:** Dynamic intraday system screening Nifty 200 daily

**How:**
1. Screen 200 stocks at 10:30 AM
2. Select top 25 by multi-factor score
3. Wait for breakout + retest entry
4. Execute with 2.5:1 R:R and break-even trailing

**Why It Works:**
- Retest entry: 13% fewer false breakouts
- 2.5:1 R:R: Only needs 40% WR (achievable)
- Dynamic selection: Captures "stocks in play"
- Mid-cap alpha: Higher volatility than Nifty 50

**Mathematical Edge:**
```
Φ (Expectancy) = (0.40 × 2.5R) - (0.60 × 1R) = +0.4R
```

---

## 🚀 Quick Start (5 Minutes)

```powershell
# Step 1: Fetch symbols (2 min)
python fetch_nifty200_symbols.py

# Step 2: Test screening (30 sec)
python quick_test_screener.py
# Use date: 2024-12-18

# Step 3: Single-day backtest (5 min)
python test_alpha_screener.py
# Start: 2024-12-18
# End: 2024-12-18

# ✅ If all green → Run 1-month backtest
```

---

## 📞 Decision Tree

```
After 1-Day Backtest:
├─ Trades executed? YES → Continue
│                   NO  → Check logs (may be normal)
│
└─ After 1-Week Backtest:
   ├─ Win Rate >35%? YES → Continue
   │                 NO  → Review parameters
   │
   └─ After 1-Month Backtest:
      ├─ Win Rate >40% AND PF >2.5? YES → Paper trading
      │                              NO  → Use fixed 50-stock
      │
      └─ After Paper Trading (1 week):
         ├─ Results match backtest? YES → Go live (0.5% risk)
         └─                         NO  → Debug execution
```

---

## 🏆 Validation Checklist

**Before Going Live:**
- [ ] Win Rate >40%
- [ ] Profit Factor >2.5
- [ ] Positive Expectancy
- [ ] Max Drawdown <20%
- [ ] 100+ trades/year
- [ ] Outperforms fixed 50-stock
- [ ] Paper trading successful (1 week)

---

## 💡 Pro Tips

1. **JWT Token:** Expires in 10-15 min → Have TOTP ready for long backtests
2. **Best Test Dates:** Weekdays with high Nifty volatility (>0.5% move)
3. **Screening Success:** Expect 10-50 candidates passing initial filters
4. **Top 25 Selection:** Higher score = better quality setup
5. **No Trades Normal:** May happen if no retest signals found
6. **Compare Always:** Test same dates on fixed 50-stock for comparison

---

## 📊 Expected Results (1 Month)

```
Metric                  Conservative    Optimistic
─────────────────────────────────────────────────────
Total Trades            20-25           30-35
Win Rate                38-42%          43-47%
Total Return            +5-10%          +15-25%
Profit Factor           2.0-2.5         3.0-4.0
Max Drawdown            8-15%           5-10%
Avg Trade Duration      2-4 hours       1-3 hours
Expectancy (Φ)          ₹300-500        ₹800-1200
```

---

## 🎯 One-Liner Summary

**"Screen Nifty 200 daily at 10:30 AM → Select top 25 → Enter on retest → Manage with 2.5:1 R:R → Target 100+ trades/year at 40%+ Win Rate"**

---

**Need Details?** → [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)  
**Need Full Docs?** → [README_ALPHA_SCREENER.md](README_ALPHA_SCREENER.md)  
**Need Code?** → [test_alpha_screener.py](test_alpha_screener.py)

**START NOW:** `python fetch_nifty200_symbols.py` ⚡
