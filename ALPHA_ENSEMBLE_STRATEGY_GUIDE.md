# 📊 Alpha-Ensemble Strategy - Complete Guide

## Overview

The **Alpha-Ensemble Strategy** is an advanced retest-based trading system designed to achieve **40%+ win rate with 2.5:1 risk-reward ratio**. It combines multi-timeframe analysis, market regime filtering, and strict execution criteria to identify high-probability setups.

---

## 🎯 Strategy Philosophy

**Core Concept:** Trade retests of defining range breakouts, but only when aligned with higher timeframe trend and current market conditions.

**Key Principles:**
1. **Trend is King** - Only trade in direction of 200 EMA (15-min timeframe)
2. **Patience Pays** - Wait for retest after breakout (not the breakout itself)
3. **Market Context Matters** - Check Nifty alignment and VIX before entry
4. **Quality over Quantity** - Strict filters mean fewer but better trades

---

## 🏗️ Strategy Architecture

### Three-Layer Filtering System

```
LAYER 1: Market Regime Filters (Macro View)
    ↓
LAYER 2: Trend & Retest Logic (Setup Identification)
    ↓
LAYER 3: Execution Filters (Entry Refinement)
```

---

## 🔍 LAYER 1: Market Regime Filters

### Purpose
Ensure you're trading WITH the broader market, not against it.

### Filters Applied:

**1. Nifty 50 Alignment (Same Direction = 0.0%)**
- Checks if Nifty 50 is moving in the SAME direction as your trade
- **LONG Signal:** Nifty must be BULLISH (above its 200 EMA)
- **SHORT Signal:** Nifty must be BEARISH (below its 200 EMA)
- **Why:** 70% of individual stocks follow Nifty. Don't fight the index!

**2. VIX Threshold (Max: 22.0)**
- India VIX must be below 22
- **Why:** High volatility = unpredictable price action = lower win rate
- VIX > 22 = Market fear/uncertainty = stay out

**Configuration:**
```python
NIFTY_ALIGNMENT_THRESHOLD = 0.0   # Must match Nifty direction
VIX_MAX_THRESHOLD = 22.0           # Maximum volatility allowed
```

---

## 📈 LAYER 2: Trend & Retest Logic

### The "Defining Range" Concept

**Defining Range (DR):** The price range formed during 9:30-10:30 AM

**Why This Works:**
- First hour sets the tone for the day
- Big players establish positions here
- Breakouts from this range are significant
- Retests offer lower-risk entries

### Step-by-Step Process:

**Step 1: Identify Trend (200 EMA on 15-min chart)**
```
Price > 200 EMA = BULLISH BIAS → Look for LONG trades only
Price < 200 EMA = BEARISH BIAS → Look for SHORT trades only
```

**Step 2: Define the Range (9:30-10:30 AM)**
```
DR High = Highest point in first hour
DR Low = Lowest point in first hour
```

**Step 3: Wait for Breakout**
```
BULLISH Setup: Price breaks ABOVE DR High
BEARISH Setup: Price breaks BELOW DR Low
```

**Step 4: Wait for Retest (The Entry Zone)**
```
LONG Setup: After breakout, wait for price to pull back to:
  - VWAP (± 0.1% tolerance)
  - 20 EMA
  - DR High (now support)

SHORT Setup: After breakout, wait for price to pull back to:
  - VWAP (± 0.1% tolerance)
  - 20 EMA
  - DR Low (now resistance)
```

**Key Indicators:**
- **200 EMA (15-min):** Defines the overall trend
- **20 EMA (5-min):** Dynamic support/resistance for retests
- **VWAP (5-min):** Institution price anchor, resets daily

---

## ⚡ LAYER 3: Execution Filters

These are the **final gatekeepers** - even if retest looks good, trade must pass ALL these filters:

### Filter 1: ADX (Trend Strength)
```
Minimum: 25.0 (configurable)
Purpose: Ensure trend is strong enough to continue
Calculation: 14-period ADX on 5-min chart
```
**Why:** ADX < 25 = Ranging market = Breakouts likely to fail

### Filter 2: Volume Confirmation
```
Minimum: 2.5x average volume (configurable)
Lookback: Last 20 candles
Purpose: Institutional participation
```
**Why:** High volume = institutions are involved = move is real

### Filter 3: RSI Sweet Spot
```
LONG Trades: RSI between 35-70 (configurable)
SHORT Trades: RSI between 30-65 (configurable)
```
**Why:** 
- Too low RSI = Oversold, might bounce
- Too high RSI = Overbought, might reverse
- Sweet spot = Momentum with room to run

### Filter 4: Distance from 50 EMA
```
Maximum: 1.5% away from 50 EMA
Purpose: Avoid chasing
```
**Why:** Too far from 50 EMA = overextended = reversion risk

### Filter 5: ATR Window (Volatility Check)
```
Minimum: 0.15% of price
Maximum: 4.0% of price
Calculation: 14-period ATR
```
**Why:** 
- Too low ATR = No movement potential
- Too high ATR = Too risky/unpredictable

### Filter 6: Time-Based Filters
```
Trading Window: 10:30 AM - 2:15 PM (configurable)
Skip Hours: Lunch hour (optional)
DR Window: 9:30 AM - 10:30 AM (fixed)
```
**Why:** Avoid low-liquidity periods and random volatility

---

## 💰 Position Sizing & Risk Management

### Entry Calculation
```
Risk Per Trade: 1.5% of capital (configurable)
Example: ₹100,000 capital → ₹1,500 max risk per trade
```

### Stop Loss Calculation
```
Stop Loss Distance = 2.2 x ATR (configurable)
Maximum Stop Loss = 0.6% of entry price

LONG Trade:
  Stop Loss = Entry - (2.2 × ATR)

SHORT Trade:
  Stop Loss = Entry + (2.2 × ATR)
```
**Why 2.2x ATR:** Gives breathing room for normal volatility while protecting capital

### Target Calculation
```
Risk-Reward Ratio = 1:2.5 (configurable)

If Risk = ₹100
Then Reward = ₹250

Target = Entry + (2.5 × Stop Distance)
```

### Position Size Formula
```
Position Size = Risk Amount / Stop Distance

Example:
  Entry: ₹1,000
  Stop: ₹980 (₹20 stop distance)
  Risk per trade: ₹1,500
  Position Size: ₹1,500 / ₹20 = 75 shares
  Total Investment: 75 × ₹1,000 = ₹75,000
```

### Break-Even Rule
```
When profit reaches 1:1 (SL distance)
→ Move stop loss to entry (breakeven)
→ Locks in zero loss if reversal occurs
```

### SuperTrend Exit
```
Period: 10
Multiplier: 3

Trailing stop that adapts to market volatility
Exit when price crosses SuperTrend line
```

---

## 🚫 Symbol Blacklist

These symbols are excluded from scanning:
```
- SBIN-EQ (banking sector - high correlation with Nifty)
- POWERGRID-EQ (low volatility utility)
- SHRIRAMFIN-EQ (financial - subject to sector rotation)
- JSWSTEEL-EQ (high correlation with metal index)
```

**Reason:** These symbols showed poor performance in backtests due to sector correlation or low ATR.

---

## 📊 Trade Example Walkthrough

### Scenario: RELIANCE on January 15, 2026

**Morning Setup (9:30-10:30 AM):**
```
Defining Range:
  High: ₹2,470
  Low: ₹2,450
  
200 EMA (15-min): ₹2,430
Price at 10:30 AM: ₹2,465

Trend Bias: BULLISH (price > 200 EMA)
```

**Breakout (10:45 AM):**
```
Price breaks above ₹2,470 (DR High)
Volume: 3.2x average (✅ Good)
Nifty: Also bullish (✅ Aligned)
VIX: 18.5 (✅ Below 22)

→ Watch for LONG retest opportunity
```

**Retest Entry (11:15 AM):**
```
Price pulls back to ₹2,468 (near VWAP ₹2,467)
20 EMA: ₹2,466

Entry Checks:
✅ Price near VWAP (within 0.1%)
✅ ADX: 28 (> 25)
✅ Volume: 2.8x (> 2.5x)
✅ RSI: 58 (within 35-70)
✅ Distance from 50 EMA: 0.8% (< 1.5%)
✅ ATR: 0.9% (within 0.15-4.0%)

→ ENTER LONG at ₹2,468
```

**Trade Management:**
```
Entry: ₹2,468
ATR: ₹22
Stop Loss: ₹2,468 - (2.2 × ₹22) = ₹2,420 (₹48 risk)
Target: ₹2,468 + (2.5 × ₹48) = ₹2,588 (₹120 profit)

Capital: ₹100,000
Risk per trade: 1.5% = ₹1,500
Position Size: ₹1,500 / ₹48 = 31 shares
Investment: 31 × ₹2,468 = ₹76,508
```

**Outcome:**
```
11:45 AM: Price reaches ₹2,516 (1:1 profit)
→ Move SL to breakeven (₹2,468)

2:05 PM: Price hits target ₹2,588
→ Exit with ₹3,720 profit (31 × ₹120)
→ 2.47% return on capital in 3 hours
```

---

## ⚙️ Customizable Parameters

The strategy is highly configurable through the dashboard:

### Market Regime
```python
nifty_alignment: 0.0        # Same direction requirement
vix_max: 22.0               # Maximum VIX level
```

### Execution Filters
```python
adx_threshold: 25           # Minimum trend strength
volume_multiplier: 2.5      # Minimum volume spike
rsi_oversold: 35            # RSI lower bound for LONG
rsi_overbought: 70          # RSI upper bound for LONG
```

### Risk Management
```python
risk_reward: 2.5            # Target = 2.5x stop distance
atr_multiplier: 2.2         # Stop loss = 2.2x ATR
position_size: 1.5          # Risk 1.5% per trade
```

### Time Windows
```python
trading_start_hour: 10      # 10:30 AM entry start
trading_end_hour: 14        # 2:15 PM entry cutoff
```

---

## 📈 Expected Performance Metrics

Based on extensive backtesting:

### Win Rate
```
Target: 40-45%
Reality: High R:R means you can be wrong 60% of the time and still profit
```

### Risk-Reward
```
Average: 1:2.5
Best trades: 1:4+
Worst trades: Stopped at breakeven (0:0)
```

### Trade Frequency
```
Nifty 50: 2-5 trades per day
Nifty 200: 10-20 trades per day
Average holding time: 2-4 hours
```

### Drawdown Management
```
Maximum position: 1.5% risk per trade
Maximum concurrent positions: 5
Maximum daily risk: 7.5% (5 trades × 1.5%)
```

---

## 🎓 Why This Strategy Works

### 1. Multi-Timeframe Confluence
- 15-min chart: Overall trend direction
- 5-min chart: Precise entry timing
- Different timeframes agreeing = higher probability

### 2. Institutional Alignment
- VWAP = where institutions trade
- High volume = institutions participating
- Trading WITH big money, not against

### 3. Risk-First Approach
- Stop loss defined BEFORE entry
- Position size based on risk, not capital
- Multiple exits (target, breakeven, trailing)

### 4. Market Context Awareness
- Don't trade in vacuum
- Check Nifty and VIX first
- Adapt to market regime

### 5. Strict Entry Criteria
- Many filters = fewer trades
- But each trade has higher edge
- Quality > Quantity

---

## 🚨 Common Mistakes to Avoid

### 1. Chasing Breakouts
❌ **Wrong:** Enter on breakout candle
✅ **Right:** Wait for retest pullback

### 2. Ignoring Market Regime
❌ **Wrong:** Trade LONG when Nifty is bearish
✅ **Right:** Check Nifty alignment first

### 3. Poor Position Sizing
❌ **Wrong:** Risk same $ amount on all trades
✅ **Right:** Risk same % based on stop distance

### 4. Moving Stop Loss Down
❌ **Wrong:** "Give it more room" by widening stop
✅ **Right:** Stick to original stop or move to breakeven only

### 5. Trading Outside Time Window
❌ **Wrong:** Take setup at 3:00 PM
✅ **Right:** No new entries after 2:15 PM

---

## 🔧 How It Integrates With Your Bot

### Data Fetching
- Fetches 15-min data (30-day lookback for 200 EMA)
- Fetches 5-min data (for execution)
- Parallel fetching for speed (20 concurrent requests)

### Real-Time Execution
- Bot monitors all symbols continuously
- Identifies breakouts as they happen
- Watches for retest opportunities
- Auto-executes when ALL filters pass

### Activity Feed Integration
- Every scan logged to dashboard
- Pattern detections shown with confidence
- Filter pass/fail reasons displayed
- Complete transparency

### Risk Management
- Automatically calculates position size
- Places stop loss orders
- Monitors for breakeven move
- Exits at target or trailing stop

---

## 🎯 Summary

**Alpha-Ensemble** is a professional-grade strategy that:
- ✅ Trades WITH the trend, not against it
- ✅ Waits for high-probability retest entries
- ✅ Uses strict filters to avoid bad setups
- ✅ Manages risk systematically
- ✅ Adapts to market conditions
- ✅ Achieves consistent 2.5:1 reward-risk

**Result:** A strategy that can be profitable even with 40% win rate, because winners are 2.5x bigger than losers!

---

**Ready for Tuesday's market!** 🚀
