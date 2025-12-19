# 🎯 Parameter Tuning Guide - Dashboard Backtester

## Overview
The dashboard now has **Advanced Parameters** controls that let you fine-tune the Alpha-Ensemble strategy directly from the UI without modifying code. This enables rapid testing to find the optimal 65%+ Win Rate configuration.

## How to Use

### 1. Enable Advanced Parameters
1. Open the dashboard Strategy Backtester
2. Click the toggle switch next to "Advanced Parameters"
3. The parameter controls will expand below

### 2. Adjust Parameters
Use the sliders, inputs, and dropdowns to customize:

#### **Symbol Universe**
- **Top 20 Liquid**: Most liquid stocks (lowest slippage)
- **Nifty 50**: Standard benchmark
- **Nifty 100**: More opportunities
- **Nifty 200 (276 symbols)**: Full universe (recommended for 65%+ WR target)

#### **ADX Threshold** (Slider: 15-35)
- **15-20**: Weak trends, more trades but lower quality
- **25**: Balanced (current baseline)
- **30-35**: Very strong trends only, fewer but higher quality trades
- **Recommendation**: Start at 25, increase to 30 for higher WR

#### **RSI Oversold** (Input: 20-45)
- Lower bound for LONG entries
- **20-30**: Very oversold, rare entries
- **35**: Current baseline
- **40-45**: Less oversold, more entries
- **Recommendation**: Test 30-40 range for optimal entries

#### **RSI Overbought** (Input: 55-80)
- Upper bound for LONG entries
- **55-60**: Conservative entries
- **65**: Current baseline
- **70-80**: Aggressive entries (might catch strong trends)
- **Recommendation**: Test 60-70 range

#### **Volume Multiplier** (Slider: 1.0x - 3.5x)
- Required volume vs 20-day average
- **1.0-1.5x**: Accept low volume (more trades, risky)
- **2.0-2.5x**: Moderate volume confirmation
- **3.0-3.5x**: High volume only (fewer but quality trades)
- **Current**: 2.5x
- **Recommendation**: Test 2.0x for balance, 3.0x for quality

#### **Risk:Reward Ratio** (Slider: 2.0 - 4.0)
- Target profit relative to risk
- **2.0**: Conservative, easier to hit targets
- **2.5**: Balanced (current baseline)
- **3.0-4.0**: Aggressive, higher profit potential
- **Recommendation**: Test 2.5-3.0 range

#### **Timeframe Alignment**
- **1 Timeframe (5min only)**: Most trades, lowest quality
- **2 Timeframes (5min + 15min)**: Good balance (default)
- **3 Timeframes**: High quality, moderate frequency
- **All 4 Timeframes**: Highest quality, fewest trades
- **Recommendation**: Start with 2TF, move to 3TF if WR is low

#### **Trading Hours**
- **Start Time**: Earliest entry (default 09:30)
- **End Time**: Latest entry (default 15:15)
- **Recommendation**: Avoid 12:00-13:00 (toxic hour)

#### **Position Size** (Slider: 1.0% - 5.0%)
- Capital allocated per trade
- **1-2%**: Conservative, safer
- **2-3%**: Moderate risk
- **4-5%**: Aggressive, higher returns but risky
- **Current**: 2.0%
- **Recommendation**: Keep at 2% for testing

#### **Max Concurrent Positions** (Input: 1-10)
- Maximum simultaneous trades
- **1-2**: Very conservative
- **3**: Balanced (current)
- **5-10**: Aggressive diversification
- **Recommendation**: Test 2-5 range

#### **Nifty Alignment**
- **None Required**: Trade regardless of Nifty trend
- **Same Direction**: Only trade in Nifty trend direction
- **Strong (>0.3%)**: Require Nifty moving >0.3%
- **Very Strong (>0.5%)**: Strict confirmation
- **Recommendation**: Test "Same Direction" or "Strong"

## Testing Strategy for 65%+ Win Rate

### 🎯 Aggressive Baseline (Recommended Starting Point)
```
Symbol Universe: Nifty 200 (276 symbols)
ADX Threshold: 30
RSI Oversold: 30
RSI Overbought: 70
Volume Multiplier: 3.0x
Risk:Reward: 3.0
Timeframe Alignment: 3 Timeframes
Trading Hours: 09:30 - 15:15
Position Size: 2.0%
Max Positions: 3
Nifty Alignment: Strong (>0.3%)
```

### 📊 12-Batch Optimization Plan
Test these variations systematically:

**Batch 1: ADX Threshold**
- Test 20, 25, 30, 35
- Keep other params at baseline
- Goal: Find trend strength sweet spot

**Batch 2: Volume Multiplier**
- Test 2.0x, 2.5x, 3.0x, 3.5x
- Goal: Balance trade frequency vs quality

**Batch 3: RSI Ranges**
- Test combinations: (25-60), (30-65), (35-70), (40-75)
- Goal: Find momentum sweet spots

**Batch 4: Risk:Reward**
- Test 2.0, 2.5, 3.0, 3.5
- Goal: Optimize profit targets

**Batch 5: Timeframe Alignment**
- Test 1TF, 2TF, 3TF, 4TF
- Goal: Find quality vs frequency balance

**Batch 6: Trading Hours**
- Test: 09:30-14:00, 09:30-15:00, 10:00-15:00, 09:30-15:15
- Goal: Avoid toxic hours

**Batch 7: Nifty Alignment**
- Test: None, Same, Strong, Very Strong
- Goal: Market regime filtering effectiveness

**Batch 8: Position Size**
- Test 1.5%, 2.0%, 2.5%, 3.0%
- Goal: Optimal risk allocation

**Batch 9: Max Positions**
- Test 1, 2, 3, 5
- Goal: Diversification vs focus

**Batch 10: Symbol Universe**
- Test NIFTY20, NIFTY50, NIFTY100, NIFTY200
- Goal: Liquidity vs opportunity

## How to Read Results

### ✅ Good Result (Target)
- **Win Rate**: 65%+
- **Profit Factor**: 5.0+
- **Total Trades**: 20-30/month (1+ per day)
- **Returns**: Positive with low drawdown

### ⚠️ Needs Tuning
- **Win Rate**: 40-55% → Increase quality filters (ADX, Volume, Timeframes)
- **Too Few Trades**: <15/month → Loosen filters (lower ADX, RSI ranges, Volume)
- **Too Many Trades**: >50/month → Tighten filters
- **Low Profit Factor**: <2.0 → Adjust R:R ratio, check exit strategy

### ❌ Bad Configuration
- **Win Rate**: <40% → Strategy parameters are too loose
- **Negative Returns**: Reset to baseline, tighten all filters

## Tips for Optimization

1. **Start Conservative**: Begin with aggressive baseline settings (high quality)
2. **Change One Variable**: Test one parameter at a time to isolate effects
3. **Save Results**: Click "Save Results" after each test for comparison
4. **Use History Tab**: Review past tests to identify trends
5. **Test Multiple Periods**: Run 1-month, 3-month, 6-month, 1-year tests
6. **Look for Consistency**: Best settings work across multiple time periods

## Example Test Sequence

```
Test 1: Aggressive Baseline (1 year)
→ If WR < 65%: Increase ADX to 35, Volume to 3.5x

Test 2: Higher Quality (1 year)
→ If WR 65%+ but <15 trades/month: Lower ADX to 28, Volume to 2.8x

Test 3: Balanced (1 year)
→ If WR 65%+ and 20+ trades/month: THIS IS YOUR SWEET SPOT!

Test 4: Validate (3 months recent)
→ Confirm settings work on recent data

Test 5: Deploy
→ Use validated settings for live trading
```

## Deployment

Once you find optimal settings:
1. Document the parameter values
2. Test on recent data (last 1-3 months)
3. Save the configuration
4. Apply same settings to live bot (if needed)
5. Monitor daily performance

## Current Baseline Performance

**1-Year Results (Default Settings)**:
- Win Rate: 38.31%
- Profit Factor: 0.87
- Total Trades: 295
- Returns: -67.78%
- **Status**: ❌ LOSING - Need optimization

**1-Month Results (Default Settings)**:
- Win Rate: 44%
- Profit Factor: 1.40
- Total Trades: 75
- Returns: +81.23%
- **Status**: ⚠️ PROFITABLE but needs improvement

**Target with Optimization**:
- Win Rate: 65%+
- Profit Factor: 5.0+
- Total Trades: 20-30/month
- Returns: 100%+ annually
- **Status**: 🎯 GOAL

## Support

If you need help:
- Check the History tab for past successful configurations
- Compare parameter combinations
- Look for patterns in what works vs what doesn't
- Focus on Win Rate first, then optimize for trade frequency

Good luck finding your 65%+ Win Rate configuration! 🚀
