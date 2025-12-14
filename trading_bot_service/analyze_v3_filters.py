"""
Quick analysis of v3.0 filter rejections from backtest output
"""

# From the visible terminal output, let me count v3.0 rejections:

v3_rejections = {
    "S/R Proximity (0.4%)": [
        # ABFRL-EQ
        "14:00: SHORT - only 0.14% room",
        "14:05: SHORT - only 0.13% room", 
        "14:10: SHORT - only 0.17% room",
        "14:20: SHORT - only 0.18% room",
        "14:25: SHORT - only 0.18% room",
        "14:30: SHORT - only 0.32% room",
        # ABFRL-EQ LONG
        "14:00: LONG - only 0.10% room",
        "14:15: LONG - only 0.22% room",
        # DIVISLAB-EQ SHORT
        "14:20: SHORT - only 0.04% room",
        "14:25: SHORT - only 0.07% room",
        "14:30: SHORT - only 0.03% room",
        # DIVISLAB-EQ SHORT (Dec 10)
        "14:10: SHORT - only 0.08% room",
        "14:15: SHORT - only 0.01% room",
        "14:20: SHORT - only 0.04% room",
        "14:25: SHORT - only 0.01% room",
        "14:30: SHORT - only 0.13% room",
        # DIVISLAB-EQ LONG
        "14:00: LONG - only 0.08% room",
        "14:05: LONG - only 0.03% room",
        "14:10: LONG - only 0.01% room",
        # SHRIRAMFIN-EQ
        "14:00: SHORT - only 0.12% room",
        "14:05: SHORT - only 0.15% room",
        "14:10: SHORT - only 0.04% room",
        "14:15: SHORT - only 0.29% room",
        # SHRIRAMFIN-EQ LONG
        "14:00: LONG - only 0.28% room",
        "14:05: LONG - only 0.22% room",
        "14:10: LONG - only 0.28% room",
        "14:30: LONG - only 0.32% room",
        # SHRIRAMFIN-EQ Dec 5 LONG
        "14:00: LONG - only 0.08% room",
        "14:05: LONG - only 0.21% room",
        "14:10: LONG - only 0.08% room",
        "14:15: LONG - only 0.14% room",
        "14:20: LONG - only 0.11% room",
        "14:25: LONG - only 0.06% room",
        # TRENT-EQ Dec 1
        "14:50: SHORT - only 0.02% room",
        # TRENT-EQ Dec 5
        "14:45: SHORT - only 0.10% room",
        # TRENT-EQ Dec 8
        "14:00: SHORT - only 0.04% room",
        "14:05: SHORT - only 0.10% room",
        "14:10: SHORT - only 0.18% room",
        "14:15: SHORT - only 0.19% room",
        "14:20: SHORT - only 0.32% room",
        "14:25: SHORT - only 0.22% room",
        "14:30: SHORT - only 0.11% room",
        # TRENT-EQ Dec 10
        "14:00: SHORT - only 0.02% room",
        "14:05: SHORT - only 0.12% room",
        "14:10: SHORT - only 0.07% room",
        "14:15: SHORT - only 0.00% room",
        "14:20: SHORT - only 0.02% room",
        "14:25: SHORT - only 0.10% room",
        "14:30: SHORT - only 0.23% room",
        "14:50: SHORT - only 0.14% room",
        # TRENT-EQ Dec 12
        "14:00: SHORT - only 0.26% room",
        "14:20: SHORT - only 0.22% room",
        "14:25: SHORT - only 0.16% room",
        "14:30: SHORT - only 0.23% room",
        # LTIM-EQ Dec 4
        "14:00: LONG - only 0.25% room",
        "14:05: LONG - only 0.23% room",
        "14:10: LONG - only 0.18% room",
        "14:15: LONG - only 0.22% room",
        "14:20: LONG - only 0.22% room",
        "14:25: LONG - only 0.25% room",
        "14:30: LONG - only 0.28% room",
    ],
    
    "RSI Extremes (35-65)": [
        # LTIM-EQ Dec 5
        "14:00: LONG - RSI 27",
        "14:05: LONG - RSI 29",
        "14:10: LONG - RSI 29",
        "14:15: LONG - RSI 26",
        "14:20: LONG - RSI 22",
        "14:25: LONG - RSI 30",
        "14:30: LONG - RSI 28",
    ],
    
    "Symbol Blacklist": [
        # Note: SHRIRAMFIN-EQ traded despite blacklist - filter must have allowed it through
        # Let me check if there were actual blacklist rejections...
    ]
}

sr_count = len(v3_rejections["S/R Proximity (0.4%)"])
rsi_count = len(v3_rejections["RSI Extremes (35-65)"])

print("=" * 80)
print("v3.0 GRANDMASTER FILTER REJECTION ANALYSIS")
print("=" * 80)
print()
print(f"📊 S/R Proximity Filter (0.4% threshold): {sr_count} rejections")
print(f"   - Blocked entries with 0.00-0.32% room to support/resistance")
print(f"   - These are VERY TIGHT rejections near S/R zones")
print()
print(f"📊 RSI Extreme Filter (35-65 range): {rsi_count} rejections")
print(f"   - Blocked RSI 22-30 LONG entries (oversold bounces)")
print(f"   - All on LTIM-EQ Dec 5 at 14:00 hour")
print()
print("=" * 80)
print("CRITICAL FINDINGS:")
print("=" * 80)
print()
print("1. ⚠️ S/R Filter TOO STRICT:")
print("   - Blocking entries with 0.13-0.28% room")
print("   - Market entries often occur 0.1-0.5% from S/R")
print("   - 0.4% threshold eliminates most valid setups")
print()
print("2. ⚠️ RSI Filter WORKING BUT AGGRESSIVE:")
print("   - RSI 22-30 are VALID oversold bounce setups")
print("   - Only 7 rejections vs 60+ S/R rejections")
print("   - RSI filter is NOT the main problem")
print()
print("3. ✅ Symbol Blacklist NOT WORKING:")
print("   - SHRIRAMFIN-EQ traded 3 times (all LOSSES: -₹1,009, -₹1,226, -₹1,212)")
print("   - Blacklist filter FAILED to block this chronic loser")
print("   - Need to check implementation")
print()
print("=" * 80)
print("RECOMMENDATIONS:")
print("=" * 80)
print()
print("Option A: DISABLE S/R filter entirely")
print("   - Run v3.0 with ONLY symbol blacklist + RSI 35-65")
print("   - Expected: ~50 trades, see if blacklist alone improves WR")
print()
print("Option B: LOWER S/R to 0.1%")
print("   - Only block entries within 0.1% of S/R (extreme rejection zones)")
print("   - Expected: ~40-45 trades")
print()
print("Option C: FIX BLACKLIST + DISABLE S/R")
print("   - Symbol blacklist is broken (SHRIRAMFIN traded despite being blacklisted)")
print("   - Fix the blacklist logic first")
print("   - Then test with just blacklist + RSI filters")
print()
print("⚠️ URGENT: SHRIRAMFIN-EQ blacklist FAILURE")
print("   - Filter shows: 'v3.0: Blacklisted symbol SHRIRAMFIN-EQ (0/2)'")
print("   - But still allowed 3 trades through (all SL hits)")
print("   - Total damage: ₹-3,448 from a blacklisted symbol!")
print()
