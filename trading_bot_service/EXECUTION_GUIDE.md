# 🚀 Alpha-Ensemble Screener - Execution Guide

## Step-by-Step Workflow

### Phase 1: Setup & Symbol Fetching (One-Time)

#### 1.1 Fetch Nifty 200 Symbols & Tokens
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup\trading_bot_service"
python fetch_nifty200_symbols.py
```

**What it does:**
- Connects to Angel One API
- Searches all 200 Nifty stocks
- Fetches current tokens
- Maps stocks to sectors
- Saves to `nifty200_constituents.json`

**Time:** ~2-3 minutes

**Inputs:**
```
Client Code: [Your Angel One client ID]
Password/MPIN: 1012
TOTP Code: [From authenticator app]
API Key: [Your API key]
```

**Output:**
```json
[
  {
    "symbol": "RELIANCE-EQ",
    "token": "2885",
    "name": "Reliance Industries Limited",
    "sector": "ENERGY",
    "rank": 1
  },
  ...200 stocks
]
```

---

### Phase 2: Quick Validation Test

#### 2.1 Test Screening Logic (Single Day)
```powershell
python quick_test_screener.py
```

**What it does:**
- Tests screening on 1 day
- Shows top 25 candidates
- Validates all 4 filters work
- Quick sanity check

**Time:** ~30 seconds

**Inputs:**
- Same credentials
- Test date (e.g., `2024-12-18`)

**Expected Output:**
```
TOP 25 CANDIDATES SELECTED (from 47 qualified)

Rank   Symbol              Score    Move%    ADX    Vol Mult  ATR%
-------------------------------------------------------------------
1      LTIM-EQ            45.23    +1.20%   32.4    6.6x     0.22%
2      BHARTIARTL-EQ      43.87    +0.80%   36.4    3.0x     0.13%
3      INFY-EQ            41.56    +0.60%   30.9    2.8x     0.13%
...
```

---

### Phase 3: Full Backtesting

#### 3.1 Single-Day Backtest (Fast)
```powershell
python test_alpha_screener.py
```

**Inputs:**
- Credentials
- Start Date: `2024-12-18`
- End Date: `2024-12-18`

**Time:** ~5-10 minutes

**What it does:**
- Screens Nifty 200 at 10:30 AM
- Selects top 25
- Runs Alpha-Ensemble strategy
- Shows all trades

**Expected Output:**
```
FINAL PERFORMANCE SUMMARY
════════════════════════════════════════════════════════════════

💰 CAPITAL PERFORMANCE:
   Initial Capital:  ₹100,000.00
   Final Capital:    ₹102,450.00
   Total Return:     2.45%
   Max Drawdown:     0.8%

📈 TRADE STATISTICS:
   Total Trades:     3
   Winning Trades:   2
   Losing Trades:    1
   Win Rate:         66.67%

🎯 PERFORMANCE METRICS:
   Profit Factor:    4.25
   Expectancy (Φ):   ₹816.67
   Avg Win:          ₹2,125.00
   Avg Loss:         ₹500.00
   Sharpe Ratio:     2.8

VALIDATION TARGETS:
════════════════════════════════════════════════════════════════
   Win Rate > 40%?       66.67% ✅ YES
   Profit Factor > 1.0?  4.25 ✅ YES
   Positive Expectancy?  ₹816.67 ✅ YES
   Positive Return?      2.45% ✅ YES
```

#### 3.2 Multi-Day Backtest (1 Week)
```powershell
python test_alpha_screener.py
```

**Inputs:**
- Start Date: `2024-12-09`
- End Date: `2024-12-15`

**Time:** ~20-30 minutes (depends on JWT refresh)

**Note:** Will prompt for TOTP if JWT expires during run

#### 3.3 Multi-Month Backtest (1 Month)
```powershell
python test_alpha_screener.py
```

**Inputs:**
- Start Date: `2024-11-18`
- End Date: `2024-12-18`

**Time:** ~60-90 minutes

**Target Metrics:**
- Trades: 25-30
- Win Rate: 40-45%
- Return: >10%
- Profit Factor: >2.5

---

### Phase 4: Performance Comparison

#### 4.1 Compare Fixed 50 vs Dynamic 25

**Fixed 50 Strategy (Already Completed):**
```
Period      Trades   Win Rate   Return      Profit Factor
─────────────────────────────────────────────────────────
1 Year      92       42.39%     +2,072%     3.75
```

**Dynamic Screener (Run for comparison):**
```powershell
python test_alpha_screener.py
# Use 1-year date range
```

**Compare:**
- Trade frequency (92 vs expected 100+)
- Win rate consistency (42.39% vs target 40-45%)
- Return magnitude
- Drawdown profile

---

## 🎯 Key Decision Points

### After Phase 1 (Symbol Fetching):
✅ **Success:** `nifty200_constituents.json` created with 200 stocks  
❌ **Failure:** Some symbols not found → Run again or use Nifty 50 subset

### After Phase 2 (Quick Test):
✅ **Success:** Top 25 selected, all filters working  
❌ **Failure:** No candidates → Check test date has market data

### After Phase 3.1 (Single Day):
✅ **Success:** Trades executed, metrics positive  
❌ **Failure:** No trades → Market was NEUTRAL or no retest signals

### After Phase 3.3 (1 Month):
**If Win Rate >40% AND Profit Factor >2.5:**
→ Proceed to live paper trading

**If Win Rate <40% OR Profit Factor <2.0:**
→ Review filter parameters or extend backtest period

---

## 📊 Expected Timeline

```
Day 1 (Setup):
├─ 10 min: Fetch Nifty 200 symbols
├─ 5 min:  Quick test single day
└─ 30 min: 1-week backtest

Day 2 (Validation):
├─ 90 min: 1-month backtest
├─ 30 min: Analyze results
└─ 60 min: Compare vs fixed 50

Day 3 (Decision):
├─ Review all metrics
├─ Decide: Dynamic screener vs Fixed watchlist
└─ If positive → Prepare live deployment
```

---

## 🔧 Troubleshooting

### Issue: JWT Token Expires During Backtest
**Symptom:** "Invalid Token" errors mid-run  
**Solution:** System will prompt for new TOTP  
**Action:** Have authenticator app ready

### Issue: No Candidates Found
**Symptom:** "0 candidates passed screening"  
**Causes:**
1. Nifty move <0.3% (NEUTRAL market)
2. Test date is weekend/holiday
3. No stocks met all 4 criteria

**Solution:** Try different date or relax ATR/ADX filters

### Issue: No Trades Generated
**Symptom:** Screening works but 0 trades  
**Causes:**
1. No retest signals found
2. All retests failed execution filters
3. Market closed before entry

**Solution:** Review retest logs, may be normal

### Issue: Performance Worse Than Expected
**Symptom:** Win rate <40% or negative return  
**Investigation:**
1. Check slippage settings (0.05% may be too low)
2. Review rejected trades (are filters too strict?)
3. Analyze losing trades (is SL too tight?)

**Action:** Backtest longer period (3 months) before judging

---

## 📁 Files Generated

### During Execution:
```
nifty200_constituents.json   # Symbol database (200 stocks)
backtest_results_[date].csv  # Trade log (optional)
performance_summary.txt      # Metrics output (optional)
```

### Logs:
```
INFO: Screening 200 stocks...
INFO: ✅ LTIM-EQ: Score=45.23
INFO: ✅ Top 25 selected
INFO: ✅ LTIM-EQ LONG ENTRY at ₹6295.50
INFO: 🔒 Moving SL to break-even
INFO: ✅ LTIM-EQ TAKE PROFIT: +₹241,365
```

---

## 🎓 What Each File Does

| File | Purpose | When to Run |
|------|---------|-------------|
| `fetch_nifty200_symbols.py` | Get tokens | Once (or when tokens change) |
| `quick_test_screener.py` | Validate screening | Before backtest |
| `test_alpha_screener.py` | Full backtest | Main testing |
| `alpha_ensemble_screener.py` | Core engine | Don't run directly |
| `README_ALPHA_SCREENER.md` | Documentation | Read first |
| `EXECUTION_GUIDE.md` | This file | Follow steps |

---

## ✅ Success Checklist

### Before Running Backtest:
- [ ] `nifty200_constituents.json` exists
- [ ] Quick test shows 10+ candidates
- [ ] Credentials work (JWT token received)
- [ ] Test date has market data

### After 1-Week Backtest:
- [ ] At least 5 trades generated
- [ ] Win rate between 30-50%
- [ ] Profit factor >1.0
- [ ] No system errors

### After 1-Month Backtest:
- [ ] Trade frequency: 20-30 trades
- [ ] Win rate: 40-45%
- [ ] Profit factor: >2.5
- [ ] Expectancy (Φ): Positive
- [ ] Max drawdown: <20%

### Ready for Live:
- [ ] 3-month backtest: Positive metrics
- [ ] Performance beats fixed 50-stock strategy
- [ ] All validation targets met
- [ ] Risk management tested
- [ ] Paper trading plan ready

---

## 🚀 Next Actions

### If Backtest Passes (Win Rate >40%, PF >2.5):

1. **Paper Trade:**
   ```powershell
   # Create live bot with paper trading
   python live_bot_alpha_screener.py --paper-mode
   ```

2. **Monitor 1 Week:**
   - Real-time screening at 10:30 AM
   - Validate execution accuracy
   - Compare paper results vs backtest

3. **Go Live (Reduced Risk):**
   - Start with 0.5% risk per trade
   - Max 2 concurrent positions
   - Monitor for 2 weeks
   - Scale up if successful

### If Backtest Fails (Win Rate <40% or PF <2.0):

1. **Extend Period:**
   - Backtest 3 months
   - Check consistency across time

2. **Parameter Tuning:**
   - Relax ADX to 23
   - Lower volume to 2.0x
   - Adjust R:R to 2.0:1

3. **Fall Back:**
   - Use fixed 50-stock strategy (PROVEN: +2,072%)
   - Dynamic screener may not add value

---

**START HERE:** Run `fetch_nifty200_symbols.py` now!

**Questions? Review:** `README_ALPHA_SCREENER.md`
