"""
CRITICAL COMPARISON: v3.0 FIXED vs BASELINE
============================================

Goal: Achieve 60% WR while maintaining 20%+ returns

BASELINE (v2.3 with 11:00 blocked):
------------------------------------
Total Trades:    56
Win Rate:        46.43%
Total Return:    ₹23,599 (23.60%)
Expectancy:      ₹421
Profit Factor:   1.88
Average Trade:   ₹421

Breakdown:
- Winning Trades: 26 (46.43%)
- Losing Trades:  30 (53.57%)
- Avg Win:        ₹1,700
- Avg Loss:       ₹-900

v3.0 FIXED (Blacklist + RSI Extremes):
---------------------------------------
Total Trades:    12
Win Rate:        58.33%
Total Return:    ₹8,757.70 (8.76%)
Expectancy:      ₹729.81
Profit Factor:   2.69
Average Trade:   ₹729.81

Breakdown:
- Winning Trades: 7 (58.33%)
- Losing Trades:  5 (41.67%)
- Avg Win:        ₹1,992.04
- Avg Loss:       ₹-1,037.32

================================================================================
CRITICAL ANALYSIS:
================================================================================

✅ WINS:
- Win Rate improved from 46.43% → 58.33% (+11.9%)
- Expectancy improved from ₹421 → ₹729.81 (+73%)
- Profit Factor improved from 1.88 → 2.69 (+43%)
- Trade quality MUCH BETTER

❌ LOSS:
- Returns dropped from 23.60% → 8.76% (-62.7%)
- Trade count dropped from 56 → 12 (-78.6%)
- **FILTERS TOO RESTRICTIVE**

================================================================================
THE PROBLEM:
================================================================================

We eliminated TOO MANY trades:
- Hour blocks (10:00, 11:00, 12:00, 13:00, 15:00): ~40% of trading hours blocked
- Blacklist: 4 symbols eliminated
- RSI Extremes: 35-65 range blocking valid reversals
- Late entry volume: 2.5x requirement blocking end-of-day setups
- Weak breakout/momentum: Blocking 0.5-0.7% moves

Trade count needed: ~40-50 trades (not 12!)
- 56 trades at 46.43% WR = ₹23,599
- 40 trades at 60% WR = ~₹29,200 (estimated)
- 12 trades at 58.33% WR = ₹8,757.70

================================================================================
SOLUTION OPTIONS:
================================================================================

OPTION 1: KEEP BLACKLIST, RELAX OTHER FILTERS
----------------------------------------------
Current config:
  ✅ Symbol Blacklist: ENABLED (keeps WR high)
  ✅ RSI Extremes: 35-65 (blocks 7 trades)
  ❌ Hour Blocks: 10:00, 11:00, 12:00, 13:00, 15:00 (blocks ~60% of day)
  ❌ Late Entry Volume: 2.5x (blocks valid setups)
  ❌ Weak Breakout: 0.6% threshold (blocks 0.5% valid moves)

Proposed changes:
  ✅ Symbol Blacklist: KEEP (proven to improve WR)
  ⚠️ RSI Extremes: WIDEN to 30-70 (reduce rejections)
  ✅ Hour Blocks: REMOVE 12:00 and 13:00 (add back 20-25 trades)
  ✅ Late Entry Volume: REDUCE to 1.5x (more realistic)
  ✅ Weak Breakout: REDUCE to 0.4% (capture smaller moves)

Expected outcome:
- ~35-40 trades (vs 12 current)
- 55-60% WR (blacklist keeps quality high)
- ~₹20-25K returns (40 trades × ₹600 expectancy)

OPTION 2: SELECTIVE HOUR UNBLOCKING
------------------------------------
Hour analysis from baseline:
- 10:00 hour: 0% WR (KEEP BLOCKED)
- 11:00 hour: 20% WR (KEEP BLOCKED - tested)
- 12:00 hour: 12.5% WR (UNBLOCK - add ~10 trades)
- 13:00 hour: 33.33% WR (UNBLOCK - add ~12 trades)
- 15:00 hour: 44.4% WR (UNBLOCK - add ~8 trades)

Rationale:
- 12:00 hour WR is low BUT we now have blacklist
- 13:00 hour WR 33.33% + blacklist = likely 50%+
- 15:00 hour WR 44.4% + blacklist = likely 55%+

Expected outcome:
- ~42 trades (12 current + 30 from unblocked hours)
- 52-58% WR (blacklist prevents chronic losers)
- ~₹22-28K returns

OPTION 3: DISABLE RSI EXTREMES, ENABLE S/R AT 0.2%
---------------------------------------------------
RSI Extremes blocked 7 trades (RSI 12-33 oversold bounces)
- These might be VALID reversal trades
- RSI 22-30 bounces can win if support holds

S/R Proximity at 0.2% vs 0.4%:
- 0.4% blocked 61 trades (TOO STRICT)
- 0.2% would block ~30 trades (extreme proximity)
- Could capture entries 0.21-0.39% from S/R

Expected outcome:
- ~30 trades (add back RSI trades, block extreme S/R)
- 54-58% WR (S/R filter adds quality)
- ~₹18-22K returns

================================================================================
RECOMMENDED APPROACH: OPTION 1 (Conservative)
================================================================================

Step 1: Unblock 12:00 and 13:00 hours
--------------------------------------
Rationale:
- These hours had 12.5% and 33.33% WR WITHOUT blacklist
- WITH blacklist blocking SBIN/POWERGRID/SHRIRAMFIN/JSWSTEEL, likely 45-55% WR
- Adds ~22 trades back into system

Code changes needed in run_backtest_defining_order.py:
- Line ~560: Change SKIP_12_HOUR = True → False
- Line ~570: Change SKIP_13_HOUR = True → False

Expected: ~34 trades, 54-58% WR, ~₹20-24K returns

Step 2: If returns still low, reduce late entry volume requirement
-------------------------------------------------------------------
Current: 2.5x volume after 14:30
Proposed: 1.5x volume after 14:30

Code changes:
- Line ~640: Change LATE_ENTRY_VOLUME_MULTIPLIER = 2.5 → 1.5

Expected: +4-6 trades, maintains WR

Step 3: If still needed, widen RSI range
-----------------------------------------
Current: 35-65 (30 point range)
Proposed: 30-70 (40 point range)

Code changes:
- Line ~109: RSI_SAFE_LOWER = 35 → 30
- Line ~110: RSI_SAFE_UPPER = 65 → 70

Expected: +5-7 trades from RSI 30-35 and 65-70 zones

================================================================================
EXECUTION PLAN:
================================================================================

TEST 1: Unblock 12:00 and 13:00 hours (most conservative)
- Expected: ~34 trades, 54-58% WR, ₹20-24K returns
- If successful → DONE
- If WR drops below 52% → Re-block 12:00 (weakest hour)

TEST 2: If Test 1 successful but returns <20%, reduce late entry volume
- Change 2.5x → 1.5x
- Expected: +4-6 trades, maintains WR

TEST 3: If still <20% returns, widen RSI range
- Change 35-65 → 30-70
- Expected: +5-7 trades

TARGET ACHIEVED:
- 38-45 trades
- 56-60% WR
- ₹22-28K returns (22-28%)
- Expectancy: ₹550-700

================================================================================
"""

print(__doc__)
