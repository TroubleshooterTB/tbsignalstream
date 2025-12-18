# Paper Trading Plan - December 19, 2025

## Objective
Test 4 new strategies simultaneously in paper mode to identify which performs best before risking real capital.

---

## Strategies to Test

### 1. Mean Reversion (Primary - Highest Priority)
**File:** `strategy_mean_reversion_v1.py`

**Entry Logic:**
- LONG: Price < VWAP by 0.5%, RSI < 30, near lower BB, Volume > 1.5x, prev candle RED
- SHORT: Price > VWAP by 0.5%, RSI > 70, near upper BB, Volume > 1.5x, prev candle GREEN

**Exit:**
- Target: VWAP (mean reversion)
- Stop Loss: 0.3%
- Risk-Reward: 1:1.5

**Expected:**
- Win rate: 50-60%
- Trades/day: 2-5
- Best for: Ranging markets

---

### 2. VWAP + SuperTrend Confluence (Secondary)
**Entry Logic:**
- LONG: Price crosses above VWAP + SuperTrend GREEN + Volume > 2.5x + 2 candle confirmation
- SHORT: Price crosses below VWAP + SuperTrend RED + Volume > 2.5x + 2 candle confirmation

**Exit:**
- Target: 1% move
- Stop Loss: SuperTrend line (dynamic)
- Trail with SuperTrend

**Expected:**
- Win rate: 45-55%
- Trades/day: 1-3
- Best for: Trending markets

---

### 3. Improved Opening Range (Tertiary)
**Entry Logic (9:45-11:00 AM only):**
- LONG: Price > 15-min high + RSI 30-50 (counter-trend) + Volume > 1.5x + Strong green candle
- SHORT: Price < 15-min low + RSI 50-70 (counter-trend) + Volume > 1.5x + Strong red candle

**Exit:**
- Target: 2x ATR (dynamic)
- Stop Loss: 1x ATR (dynamic)

**Expected:**
- Win rate: 40-50%
- Trades/day: 1-2
- Best for: Morning momentum

---

### 4. Last Hour Momentum (Experimental)
**Entry Logic (2:30-3:15 PM only):**
- LONG: Higher highs + higher lows + RSI > 60 + Increasing volume
- SHORT: Lower highs + lower lows + RSI < 40 + Increasing volume

**Exit:**
- Target: 3:20 PM close (hold till near close)
- Stop Loss: 0.5%
- Exit all by 3:25 PM

**Expected:**
- Win rate: 45-55%
- Trades/day: 0-1
- Best for: Institutional flow

---

## Trading Schedule for December 19, 2025

### Pre-Market (8:00-9:00 AM)
- [ ] Check global markets (US close, Asia open)
- [ ] Review previous day's trades (Dec 18)
- [ ] Identify 5 stocks to watch (from Nifty 50)
- [ ] Set alerts: VWAP, RSI 30/70, SuperTrend flip

### Market Open (9:15-9:30 AM)
- [ ] Observe opening volatility (NO TRADES)
- [ ] Let first 15 minutes settle
- [ ] Calculate initial VWAP levels

### First Hour (9:30-11:00 AM)
- [ ] **Strategy 3:** Look for Opening Range breakouts
- [ ] Monitor all 4 strategies for signals
- [ ] Document every signal (taken or rejected)

### Mid-Day (11:00-12:00 PM)
- [ ] **Strategy 1 & 2:** Mean Reversion + VWAP/ST
- [ ] Active trading period
- [ ] Track positions

### Lunch Hour (12:00-2:00 PM)
- [ ] **NO TRADES** (avoid choppy period)
- [ ] Review morning trades
- [ ] Adjust stop losses if needed
- [ ] Plan afternoon strategy

### Afternoon (2:00-2:30 PM)
- [ ] **Strategy 1 & 2:** Resume trading
- [ ] Watch for VWAP mean reversion setups

### Last Hour (2:30-3:15 PM)
- [ ] **Strategy 4:** Last hour momentum trades
- [ ] Close out mean reversion positions
- [ ] Prepare for EOD

### Market Close (3:15-3:30 PM)
- [ ] Exit all remaining positions by 3:25 PM
- [ ] Calculate daily P&L
- [ ] Document all trades

### Post-Market (3:30-5:00 PM)
- [ ] Complete trading journal
- [ ] Calculate metrics for each strategy
- [ ] Identify best/worst trades
- [ ] Plan adjustments for next day

---

## Risk Management Rules

### Position Sizing:
```
Max risk per trade: 1% of capital
Capital: ₹100,000 (paper)
Max loss per trade: ₹1,000

Formula:
Quantity = ₹1,000 / (Entry Price * SL%)

Example: RELIANCE @ ₹1500, SL 0.5%
Quantity = 1000 / (1500 * 0.005) = 133 shares
Max loss = 133 * ₹7.50 = ₹997.50 ✓
```

### Daily Limits:
- Max loss per day: **3% = ₹3,000**
- Max trades per day: **10 total** (across all strategies)
- Max positions concurrent: **2**
- After 2 consecutive losses: **30-min break**
- After 3 losing trades: **STOP for day**

### Strategy Allocation:
- Strategy 1 (Mean Reversion): **50% of trades**
- Strategy 2 (VWAP+ST): **25% of trades**
- Strategy 3 (Opening Range): **15% of trades**
- Strategy 4 (Last Hour): **10% of trades**

---

## Watchlist (December 19, 2025)

### Primary (High liquidity, tight spreads):
1. **RELIANCE** - Best liquidity
2. **HDFCBANK** - Banking sector
3. **INFY** - IT sector
4. **ICICIBANK** - Banking
5. **TCS** - IT

### Secondary (Good volume):
6. **KOTAKBANK** - Only profitable in v2.1
7. **SBIN** - PSU Bank
8. **BHARTIARTL** - Telecom
9. **HINDUNILVR** - FMCG
10. **ITC** - FMCG

### Rules:
- Trade only 2-3 stocks per day initially
- Focus on RELIANCE + HDFCBANK (highest liquidity)
- Add more stocks as confidence builds

---

## Trade Documentation Template

For EACH trade (taken or rejected), document:

```markdown
### Trade #X - [TIME]

**Symbol:** RELIANCE
**Strategy:** Mean Reversion
**Direction:** LONG
**Signal Strength:** 4/5 filters passed

**Entry Analysis:**
- Price: ₹1487 (below VWAP ₹1495)
- VWAP Deviation: -0.53% ✓
- RSI: 28 (oversold) ✓
- BB: Touching lower band ✓
- Volume: 1.8x average ✓
- Prev Candle: RED ✗

**Trade Details:**
- Entry: ₹1487
- Stop Loss: ₹1483 (0.3%)
- Target: ₹1495 (VWAP)
- Quantity: 250 shares
- Risk: ₹1,000

**Exit:**
- Exit Price: ₹1494
- Exit Reason: VWAP reached
- P&L: ₹1,750 (+0.47%)
- Capital After: ₹101,750

**Lessons:**
- Good setup, waited for 4/5 filters
- Exited at VWAP as planned
- Could have held for full target
```

---

## Success Metrics (End of Day)

### Required Data:
- [ ] Total trades taken
- [ ] Win rate %
- [ ] Profit factor
- [ ] Total P&L (₹)
- [ ] Return %
- [ ] Max drawdown
- [ ] Average win vs average loss
- [ ] Best trade / Worst trade

### Strategy Comparison:
| Strategy | Trades | Wins | Win % | P&L | Notes |
|----------|--------|------|-------|-----|-------|
| Mean Reversion | - | - | - | - | - |
| VWAP+ST | - | - | - | - | - |
| Opening Range | - | - | - | - | - |
| Last Hour | - | - | - | - | - |
| **TOTAL** | - | - | - | - | - |

### Decision Criteria (After 1 Week):
Continue strategy if:
- ✅ Win rate > 50%
- ✅ Profit factor > 1.3
- ✅ Positive total P&L
- ✅ Max drawdown < 5%

Drop strategy if:
- ❌ Win rate < 40%
- ❌ Profit factor < 1.0
- ❌ Negative total P&L
- ❌ Max drawdown > 10%

---

## Emergency Protocols

### If Daily Loss Hits -3% (₹3,000):
1. **STOP TRADING IMMEDIATELY**
2. Close all open positions
3. Step away from screen for 1 hour
4. Review what went wrong
5. DO NOT revenge trade

### If 2 Consecutive Losses:
1. Take 30-minute break
2. Review trade entries
3. Check if following rules
4. Reduce position size by 50% for next trade

### If 3 Losing Trades in a Row:
1. **STOP FOR THE DAY**
2. Market conditions may have changed
3. Review strategy selection
4. Come back fresh tomorrow

---

## Weekly Review (Every Sunday)

### Calculate:
- [ ] Total trades for week
- [ ] Overall win rate
- [ ] Total P&L
- [ ] Best performing strategy
- [ ] Worst performing strategy
- [ ] Most common mistakes

### Decisions:
- [ ] Which strategy to focus on next week?
- [ ] Which strategy to drop?
- [ ] Any parameter adjustments needed?
- [ ] Position size adjustments?

### Rules:
- If week is negative → Reduce position size 50% next week
- If 2 weeks negative → PAUSE all trading, complete redesign
- If week is positive → Continue same approach, don't overtrade

---

## Phase Progression

### Phase 1: Paper Trading (Week 1 - Dec 19-26)
- Test all 4 strategies
- Document everything
- Find best 1-2 strategies
- Refine parameters

### Phase 2: Extended Paper (Week 2-4 - Dec 27 - Jan 16)
- Focus on best 1-2 strategies only
- Increase position size in paper
- Test different market conditions
- Build confidence

### Phase 3: Micro Live (Week 5 - Jan 17-23)
- **IF** profitable in Phase 2:
  - Use ₹10,000 real money only
  - Trade 1 lot only
  - Same rules as paper
  - Track emotional impact

### Phase 4: Full Capital (Week 9+ onwards)
- **IF** profitable in Phase 3:
  - Require: 55%+ win rate, 1.5+ PF, 50+ trades
  - Gradually scale up
  - Max 2% risk per trade
  - Keep detailed journal

---

## Tomorrow's Immediate Actions (Dec 19, 9:00 AM)

### ✅ DO:
1. Open paper trading platform
2. Load Mean Reversion strategy code
3. Set alerts for RELIANCE + HDFCBANK
4. Keep trading journal open
5. Focus on quality over quantity

### ❌ DO NOT:
1. Use real money
2. Trade during lunch (12-2 PM)
3. Take more than 10 trades
4. Risk more than 1% per trade
5. Revenge trade after losses

---

**Status:** READY FOR PAPER TRADING  
**Start Date:** December 19, 2025, 9:15 AM IST  
**Review Date:** December 26, 2025 (End of Week 1)  
**Go-Live Date:** TBD (Only after proving profitability)
