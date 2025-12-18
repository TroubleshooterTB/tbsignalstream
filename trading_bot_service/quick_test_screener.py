"""
Quick Test: Alpha-Ensemble Screener
====================================

Tests screening logic with small sample before full backtest
Validates all 4 screening layers work correctly
"""

import sys
from datetime import datetime
from alpha_ensemble_screener import AlphaEnsembleScreener

def test_screener():
    """Quick test of screening functionality"""
    
    print("\n" + "=" * 80)
    print("ALPHA-ENSEMBLE SCREENER - QUICK TEST")
    print("=" * 80)
    print("\nThis will test the screening logic on a single day")
    print("Full backtest available in test_alpha_screener.py\n")
    
    # Get credentials
    print("Enter your Angel One credentials:")
    client_code = input("Client Code: ").strip()
    password = input("Password/MPIN: ").strip()
    totp = input("TOTP Code: ").strip()
    api_key = input("API Key: ").strip()
    
    # Authenticate
    import requests
    url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-PrivateKey': api_key
    }
    
    payload = {
        "clientcode": client_code,
        "password": password,
        "totp": totp
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') and data.get('data'):
            jwt_token = data['data']['jwtToken']
            print("\n✅ Authentication successful!")
        else:
            print("\n❌ Authentication failed")
            return
    else:
        print("\n❌ Authentication failed")
        return
    
    # Create screener
    screener = AlphaEnsembleScreener(api_key, jwt_token)
    
    # Test date
    test_date = input("\nEnter test date (YYYY-MM-DD) or press Enter for today: ").strip()
    
    if not test_date:
        test_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n{'=' * 80}")
    print(f"TESTING SCREENER ON: {test_date}")
    print(f"{'=' * 80}\n")
    
    # Fetch Nifty data
    from datetime import timedelta
    to_date = (datetime.strptime(test_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    from_date = (datetime.strptime(test_date, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d %H:%M")
    
    print("📊 Fetching Nifty 50 data...")
    nifty_data = screener.fetch_historical_data('NIFTY 50', '99926000', 'FIVE_MINUTE', from_date, to_date)
    
    if nifty_data.empty:
        print("❌ Failed to fetch Nifty data")
        return
    
    print(f"✅ Nifty data fetched: {len(nifty_data)} candles\n")
    
    # Run screening
    print("🔍 Running screening on universe...")
    print(f"   Universe size: {len(screener.NIFTY_200_SYMBOLS)} stocks")
    print(f"   Target: Top 25 candidates\n")
    
    top_25 = screener.screen_stocks(test_date, nifty_data)
    
    # Print results
    print("\n" + "=" * 80)
    print("📊 SCREENING RESULTS SUMMARY")
    print("=" * 80)
    
    if not top_25:
        print("\n⚠️ No stocks passed screening criteria")
        print("\nPossible reasons:")
        print("1. Market was NEUTRAL (Nifty <0.3% move)")
        print("2. No stocks met all 4 filter criteria")
        print("3. Test date may not have market data")
        return
    
    print(f"\n✅ {len(top_25)} candidates selected")
    print("\nTop 10 Candidates:")
    print("=" * 80)
    print(f"{'Rank':<6} {'Symbol':<20} {'Score':<8} {'Move%':<8} {'ADX':<6} {'Vol Mult':<8} {'ATR%'}")
    print("-" * 80)
    
    for i, candidate in enumerate(top_25[:10], 1):
        print(f"{i:<6} {candidate['symbol']:<20} "
              f"{candidate['score']:>7.2f} "
              f"{candidate['move_pct']:>7.2f}% "
              f"{candidate['adx']:>5.1f} "
              f"{candidate['volume_ratio']:>7.1f}x "
              f"{candidate['atr_pct']:>6.2f}%")
    
    print("\n" + "=" * 80)
    print("✅ SCREENER TEST COMPLETE")
    print("=" * 80)
    
    print("\nNext Steps:")
    print("1. Run full backtest: python test_alpha_screener.py")
    print("2. Fetch complete Nifty 200: python fetch_nifty200_symbols.py")
    print("3. Review README: README_ALPHA_SCREENER.md")
    
    # Show sample candidate details
    if top_25:
        print("\n" + "=" * 80)
        print("SAMPLE CANDIDATE DETAILS (Top Stock)")
        print("=" * 80)
        
        top_stock = top_25[0]
        print(f"\nSymbol: {top_stock['symbol']}")
        print(f"Sector: {top_stock['sector']}")
        print(f"Composite Score: {top_stock['score']:.2f}")
        print(f"\nFilter Results:")
        print(f"   ✅ Market Move: {top_stock['move_pct']:+.2f}% (>0.3% required)")
        print(f"   ✅ ADX: {top_stock['adx']:.1f} (>25 required)")
        print(f"   ✅ Volume: {top_stock['volume_ratio']:.1f}x average (>2.0x required)")
        print(f"   ✅ ATR: {top_stock['atr_pct']:.2f}% (1.0-4.0% range)")
        print(f"\nThis stock would be monitored for retest entry signals.")


if __name__ == "__main__":
    test_screener()
