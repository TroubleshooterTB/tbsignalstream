# Backtest Auto-Save & 65% WR Optimization - DEPLOYED ✅

**Deployed:** Dec 19, 2025, 10:21 PM
**Commit:** `7426ec8`
**Dashboard:** https://studio--tbsignalstream.us-central1.hosted.app

---

## 🎯 NEW FEATURES DEPLOYED

### 1. **Auto-Save Backtest Results** ✨
- ✅ Every backtest automatically saved to **Firestore** (`backtest_results` collection)
- ✅ **History Tab** added to Strategy Backtester
- ✅ View last 20 backtest results with full metrics
- ✅ Track performance across different configurations
- ✅ "Saved!" badge appears after successful save

### 2. **65% Win Rate Optimization Plan** 📊
- ✅ Goal: Optimize from **36% WR → 65%+ WR**
- ✅ Constraint: **1+ trade per day** (20-25 trades/month)
- ✅ 12-batch systematic testing approach
- ✅ 46 total backtest variations to run
- ✅ Results tracking template CSV generated

---

## 📋 HOW TO USE

### **View Backtest History:**
1. Go to Dashboard → Strategy Backtester
2. Click **"History"** tab (shows number of saved results)
3. View all past backtests with metrics:
   - Win Rate, Trades, P&L, Profit Factor
   - Avg Win/Loss, Date Range, Timestamp
4. Results auto-save after every backtest ✅

### **Run 65% WR Optimization:**
1. Open [optimization_results_template_20251219_222110.csv](d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup\trading_bot_service\optimization_results_template_20251219_222110.csv)
2. Start with **Aggressive Baseline:**
   - ADX: 23, RSI: 32/68, Volume: 1.8x
   - R:R: 3.0, Timeframes: 3TF (5min+15min+hourly)
   - Universe: Nifty 100, Hours: 9:45-15:00
3. Run backtest on dashboard (Nov 1 - Dec 18, 2025)
4. Results auto-save to Firestore + visible in History tab
5. Record in CSV template
6. Continue with 12 batches (45 more variations)

---

## 🎯 OPTIMIZATION PLAN

### **Aggressive Baseline Parameters:**
```python
{
    "ema_period": 200,
    "adx_threshold": 23,          # Stricter than 20
    "rsi_oversold": 32,           # Tighter than 30
    "rsi_overbought": 68,         # Tighter than 70
    "volume_multiplier": 1.8,     # Higher than 1.5x
    "risk_reward": 3.0,           # Higher than 2.5
    "stop_loss_atr": 1.8,         # Wider than 1.5
    "position_size": 2,           # Conservative
    "max_positions": 3,           # Focused
    "timeframe_alignment": "3TF", # 5min + 15min + hourly
    "nifty_alignment": "same",    # Same direction
    "trading_hours": "09:45-15:00",
    "universe": "NIFTY100"        # 100 stocks
}
```

### **12 Batches to Test:**
1. Current Baseline (for comparison)
2. EMA Period (100, 150, 200, 250)
3. ADX Threshold (20, 23, 25, 27)
4. RSI Range (30/70, 32/68, 35/65, 38/62)
5. Volume Filter (1.5x, 1.8x, 2.0x, 2.5x)
6. Risk:Reward (2.5, 3.0, 3.5, 4.0)
7. Stop Loss Width (1.5, 1.8, 2.0, 2.5 ATR)
8. Position Sizing (1%, 2%, 3%, 5%)
9. Max Positions (2, 3, 5, 7)
10. Timeframe Alignment (1TF, 2TF, 3TF, 4TF)
11. Symbol Universe (NIFTY200, 100, 50, 20)
12. Trading Hours (Full, Morning, Afternoon, Core)

**Total: 46 backtests**

---

## 📊 SUCCESS CRITERIA

### **Target Metrics:**
- ✅ **Win Rate: 65%+** (vs current 36%)
- ✅ **Profit Factor: 5.0+** (vs current 2.64)
- ✅ **Expectancy: ₹1,500+ per trade** (vs current ₹260)
- ✅ **Trade Frequency: 20-25/month** (1+ per day)
- ✅ **Max Drawdown: <10%**

### **Expectancy Comparison:**
| Scenario | WR | R:R | Expectancy | vs Current |
|----------|----|----|-----------|-----------|
| Current | 36% | 2.5 | ₹260 | Baseline |
| Conservative | 55% | 3.0 | ₹1,200 | 4.6x better |
| **Target** | **65%** | **3.0** | **₹1,600** | **6.2x better** |
| Ultra | 70% | 3.5 | ₹2,150 | 8.3x better |

---

## 📁 FILES CREATED

### **Optimization Scripts:**
- `12_batch_backtest_plan.py` - Complete 12-batch plan
- `aggressive_65percent_strategy.py` - Strategy details & math
- `execute_65percent_optimization.py` - Execution plan generator
- `run_aggressive_baseline.py` - Baseline configuration
- `optimization_results_template_20251219_222110.csv` - Results tracking

### **Diagnostic Scripts:**
- `diagnose_today_dec19.py` - Dec 19 no-trades diagnosis
- `backtest_summary_dec18.py` - Dec 18 results analyzer

---

## 🔥 QUICK START

### **Option 1: Dashboard (Manual)**
1. Go to: https://studio--tbsignalstream.us-central1.hosted.app
2. Navigate to Strategy Backtester
3. Select "Run Backtest" tab
4. Set parameters from Aggressive Baseline
5. Run → Results auto-save
6. View in "History" tab

### **Option 2: Automated (Coming Soon)**
- Programmatic execution via API
- Batch processing all 46 tests
- Auto-fill CSV template

---

## 💡 STRATEGY INSIGHTS

### **Why 65% WR is Achievable:**
1. **Stricter Filters** → Only highest-conviction setups
2. **Multi-Timeframe** → Reduce false signals (3 TFs must align)
3. **Better Timing** → Avoid opening/closing volatility
4. **Quality > Quantity** → 20 great trades > 50 mediocre trades
5. **Wider Stops** → Less noise, better runners

### **Trade-Offs:**
✅ **Pros:** Much higher WR, better PF, less stress, consistent profits  
❌ **Cons:** Fewer opportunities, requires patience, may miss some moves

### **Mitigation:**
- Expand to Nifty 100 (more opportunities)
- Extended trading hours (9:45-15:00)
- Balanced parameters (not TOO strict)
- Accept 1+ trade/day minimum

---

## 📈 NEXT STEPS

1. ✅ **Test Aggressive Baseline** (do this first!)
   - If WR < 50%: Parameters too strict → loosen
   - If WR > 60%: Great! → Continue with batches
   
2. ✅ **Run All 12 Batches**
   - Track in CSV template
   - Results auto-save to Firestore
   - View in History tab

3. ✅ **Analyze Results**
   - Sort by Win Rate
   - Find configurations with 65%+ WR AND 20+ trades
   - Select best parameters from each batch

4. ✅ **Combine & Validate**
   - Create optimized config
   - Run final validation backtest
   - Deploy if metrics > baseline

5. ✅ **Go Live**
   - Update bot_config with optimized parameters
   - Monitor performance
   - Adjust if needed

---

## 🚀 DEPLOYMENT STATUS

**Frontend (Dashboard):**
- ✅ Auto-save to Firestore implemented
- ✅ History tab added to Strategy Backtester
- ✅ "Saved!" indicator on success
- ✅ Deployed via Git push (auto-deploys)

**Backend:**
- ✅ No changes needed (existing backtest API works)

**Database (Firestore):**
- ✅ New collection: `backtest_results`
- ✅ Auto-created on first save
- ✅ Stores: strategy, dates, capital, summary, trades, timestamp

**Files:**
- ✅ All optimization scripts created
- ✅ CSV template generated
- ✅ Documentation complete

---

## 🎯 REMEMBER

**Goal:** 65%+ Win Rate with 1+ trade per day  
**Approach:** Quality over Quantity  
**Method:** Systematic 12-batch optimization  
**Tool:** Dashboard auto-saves all results  
**Timeline:** Run all 46 tests, find best config, deploy  

**YOU'RE READY TO START! 🚀**

Run Aggressive Baseline first and see if you hit 50%+ WR!
