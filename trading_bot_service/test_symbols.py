from nifty200_watchlist import NIFTY200_WATCHLIST

print(f"Total symbols: {len(NIFTY200_WATCHLIST)}")
print(f"\nFirst symbol: {NIFTY200_WATCHLIST[0]}")
print(f"Type: {type(NIFTY200_WATCHLIST[0])}")
print(f"Has 'symbol' key: {'symbol' in NIFTY200_WATCHLIST[0]}")
print(f"Has 'token' key: {'token' in NIFTY200_WATCHLIST[0]}")

# Test slicing
nifty50 = NIFTY200_WATCHLIST[:50]
print(f"\nNifty 50 count: {len(nifty50)}")
print(f"Nifty 50 first: {nifty50[0]}")
print(f"Nifty 50 last: {nifty50[-1]}")
