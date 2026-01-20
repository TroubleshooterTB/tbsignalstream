"""
CRITICAL DIAGNOSTIC - Why is the bot not placing trades?
========================================================

This diagnostic focuses on the CRITICAL issues preventing trade execution.
"""

import os
import sys
import json
from datetime import datetime, timedelta

print("\n" + "=" * 80)
print("CRITICAL DIAGNOSTIC - Trading Bot Not Placing Trades")
print("=" * 80 + "\n")

# Add parent directory to path
sys.path.insert(0, os.path.abspath('.'))

critical_issues = []
warnings = []
passed = []

def check_mark(condition):
    return "[PASS]" if condition else "[FAIL]"

def check(name, condition, fail_msg="", warn_msg=""):
    """Check a condition and log result"""
    if condition:
        passed.append(name)
        print(f"  {check_mark(True)} {name}")
    else:
        if fail_msg:
            critical_issues.append(f"{name}: {fail_msg}")
            print(f"  {check_mark(False)} {name} - CRITICAL: {fail_msg}")
        elif warn_msg:
            warnings.append(f"{name}: {warn_msg}")
            print(f"  {check_mark(False)} {name} - WARNING: {warn_msg}")
        else:
            critical_issues.append(name)
            print(f"  {check_mark(False)} {name} - FAILED")

# TEST 1: Firestore Connection
print("\n1. FIRESTORE CONNECTION")
print("-" * 80)

firestore_path = os.path.join("..", "firestore-key.json")
firestore_exists = os.path.exists(firestore_path)
check("Firestore credentials file", firestore_exists, 
      "firestore-key.json not found - bot cannot read/write data")

if firestore_exists:
    try:
        with open(firestore_path, 'r') as f:
            creds = json.load(f)
        check("Credentials JSON valid", True)
        print(f"  Project: {creds.get('project_id', 'UNKNOWN')}")
    except:
        check("Credentials JSON valid", False, "Invalid JSON format")

# TEST 2: Bot Engine File
print("\n2. BOT ENGINE IMPLEMENTATION")
print("-" * 80)

bot_file = "trading_bot_service/realtime_bot_engine.py"
bot_exists = os.path.exists(bot_file)
check("Bot engine file exists", bot_exists, "Main bot file missing")

if bot_exists:
    with open(bot_file, 'r', encoding='utf-8') as f:
        bot_content = f.read()
    
    # Critical methods
    check("_place_entry_order method", "def _place_entry_order" in bot_content,
          "No method to place orders!")
    check("_on_tick callback", "def _on_tick" in bot_content,
          "Bot cannot receive live price data")
    check("_check_signals method", "def _check_signals" in bot_content or "def check_signals" in bot_content,
          "Bot cannot check for trading signals")
    
    # Check for blocking issues
    if "PAPER_TRADING = True" in bot_content:
        check("Paper trading disabled", False, 
              "PAPER_TRADING=True - bot will NOT place real trades!")
    else:
        check("Paper trading disabled", True)
    
    if "DRY_RUN = True" in bot_content:
        check("Dry run disabled", False,
              "DRY_RUN=True - bot will NOT place real trades!")
    else:
        check("Dry run disabled", True)

# TEST 3: Check Cloud Run Configuration
print("\n3. CLOUD RUN DEPLOYMENT")
print("-" * 80)

cloud_config_path = os.path.join("..", "cloud_run_config.json")
cloud_config_exists = os.path.exists(cloud_config_path)
check("Cloud Run config exists", cloud_config_exists,
      warn_msg="Cannot verify deployment URL")

if cloud_config_exists:
    try:
        with open(cloud_config_path, 'r') as f:
            config = json.load(f)
        service_url = config.get('service_url', '')
        print(f"  Service URL: {service_url}")
        check("Service URL configured", bool(service_url))
    except:
        check("Cloud config JSON valid", False)

# TEST 4: Strategy Files
print("\n4. TRADING STRATEGIES")
print("-" * 80)

strategies = {
    'Alpha Ensemble': 'trading_bot_service/alpha_ensemble_strategy.py',
    'Defining Order': 'trading_bot_service/defining_order_strategy.py',
    'Ironclad': 'trading_bot_service/ironclad_strategy.py',
    'Mean Reversion': 'trading_bot_service/mean_reversion_strategy.py'
}

strategy_count = 0
for name, path in strategies.items():
    if os.path.exists(path):
        print(f"  [PASS] {name}")
        strategy_count += 1
    else:
        print(f"  [WARN] {name} - file not found")

check(f"{strategy_count}/4 strategies available", strategy_count > 0,
      "No strategy files found - bot cannot generate signals")

# TEST 5: Frontend Files
print("\n5. FRONTEND COMPONENTS")
print("-" * 80)

frontend_files = {
    'Dashboard': 'src/components/live-alerts-dashboard.tsx',
    'OTR Widget': 'src/components/otr-compliance-widget.tsx',
    'Regime Indicator': 'src/components/regime-indicator.tsx',
    'Main Page': 'src/app/page.tsx'
}

for name, path in frontend_files.items():
    exists = os.path.exists(path)
    if exists:
        print(f"  [PASS] {name}")
    else:
        print(f"  [WARN] {name} - not found")

# TEST 6: Check Main.py for API endpoints
print("\n6. API ENDPOINTS")
print("-" * 80)

main_file = "trading_bot_service/main.py"
if os.path.exists(main_file):
    with open(main_file, 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    endpoints = ['/health', '/start', '/stop', '/status']
    for endpoint in endpoints:
        has_endpoint = endpoint in main_content
        if has_endpoint:
            print(f"  [PASS] {endpoint}")
        else:
            print(f"  [WARN] {endpoint} - not found")
else:
    print("  [FAIL] main.py not found")

# TEST 7: Critical Code Checks in Bot Engine
print("\n7. CRITICAL BOT LOGIC CHECKS")
print("-" * 80)

if bot_exists:
    # Check for trading enabled logic
    has_trading_check = "trading_enabled" in bot_content
    print(f"  {'[INFO]' if has_trading_check else '[WARN]'} Trading enabled check: {'Found' if has_trading_check else 'Not found'}")
    
    # Check for market hours validation
    has_market_hours = "market_hours" in bot_content or "is_market_open" in bot_content
    print(f"  {'[PASS]' if has_market_hours else '[WARN]'} Market hours check: {'Found' if has_market_hours else 'Not found'}")
    
    # Check for signal validation
    has_signal_validation = "validate_signal" in bot_content or "check_signal" in bot_content
    print(f"  {'[INFO]' if has_signal_validation else '[INFO]'} Signal validation: {'Found' if has_signal_validation else 'Not implemented'}")
    
    # Check for position limits
    has_position_limits = "max_positions" in bot_content or "position_limit" in bot_content
    print(f"  {'[INFO]' if has_position_limits else '[INFO]'} Position limits: {'Found' if has_position_limits else 'Not configured'}")
    
    # Check for error handling in order placement
    has_error_handling = "try:" in bot_content and "except" in bot_content
    print(f"  {'[PASS]' if has_error_handling else '[WARN]'} Error handling: {'Implemented' if has_error_handling else 'Missing'}")

# SUMMARY
print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

print(f"\nPassed: {len(passed)}")
print(f"Warnings: {len(warnings)}")
print(f"Critical Issues: {len(critical_issues)}")

if critical_issues:
    print("\n" + "!" * 80)
    print("CRITICAL ISSUES PREVENTING TRADE EXECUTION:")
    print("!" * 80)
    for i, issue in enumerate(critical_issues, 1):
        print(f"\n{i}. {issue}")

if warnings:
    print("\n" + "-" * 80)
    print("WARNINGS (Non-blocking but should be addressed):")
    print("-" * 80)
    for i, warn in enumerate(warnings, 1):
        print(f"{i}. {warn}")

# ROOT CAUSE ANALYSIS
print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS - Why No Trades in 2 Months?")
print("=" * 80)

print("\nPossible reasons the bot isn't placing trades:\n")

reasons = []

if not firestore_exists:
    reasons.append("1. FIRESTORE CREDENTIALS MISSING - Bot cannot read config or write signals")

if "PAPER_TRADING = True" in bot_content:
    reasons.append("2. PAPER TRADING MODE ENABLED - Bot is in simulation mode, not real trading")

if "trading_enabled" in bot_content:
    reasons.append("3. TRADING MAY BE DISABLED - Check 'trading_enabled' flag in bot_config Firestore")

if "_place_entry_order" not in bot_content:
    reasons.append("4. NO ORDER PLACEMENT METHOD - Bot cannot execute trades")

if "_check_signals" not in bot_content and "check_signals" not in bot_content:
    reasons.append("5. NO SIGNAL CHECKING - Bot cannot identify trading opportunities")

if not reasons:
    reasons.append("Code structure looks OK. Need to check:")
    reasons.append("   - Bot configuration in Firestore (trading_enabled flag)")
    reasons.append("   - Symbol universe configuration (is it empty?)")
    reasons.append("   - Cloud Run logs (is bot crashing after startup?)")
    reasons.append("   - Activity feed in Firestore (what's the last logged action?)")
    reasons.append("   - Angel One API credentials (are they valid?)")
    reasons.append("   - Market hours check (is bot only running outside market hours?)")

for reason in reasons:
    print(f"  {reason}")

# NEXT STEPS
print("\n" + "=" * 80)
print("IMMEDIATE ACTION ITEMS:")
print("=" * 80)

actions = [
    "1. Check Firestore 'bot_config' collection - verify 'trading_enabled: true'",
    "2. Check Firestore 'bot_config' collection - verify 'symbol_universe' is not empty",
    "3. Check Firestore 'activity_feed' - see what bot logged after 'BOT_STARTED'",
    "4. Check Cloud Run logs - look for errors/exceptions after bot startup",
    "5. Verify Angel One credentials are set in Cloud Run environment variables",
    "6. Check if bot is only running outside market hours (9:15 AM - 3:30 PM)",
    "7. Test signal generation manually with current market data",
    "8. Verify WebSocket connection is receiving live price data"
]

for action in actions:
    print(f"\n{action}")

print("\n" + "=" * 80)
print("END OF DIAGNOSTIC")
print("=" * 80 + "\n")
