
from web3_pricing import get_bulk_quotes
from arbitrage_engine import scan_market
import time
import json

# WMON/USDC
TOKEN_A = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701" # WMON
TOKEN_B = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603" # USDC

print("🧪 Testing Kuru Integration (WMON/USDC)...")

requests = [
    {
        "tokenIn": TOKEN_A,
        "tokenOut": TOKEN_B,
        "amountIn": 10**18, # 1 WMON
        "tokenInSymbol": "WMON",
        "tokenOutSymbol": "USDC"
    },
    {
        "tokenIn": TOKEN_B,
        "tokenOut": TOKEN_A,
        "amountIn": 10**6, # 1 USDC
        "tokenInSymbol": "USDC",
        "tokenOutSymbol": "WMON"
    }
]

print("📊 Fetching Quotes...")
t0 = time.time()
results = get_bulk_quotes(requests)
dt = (time.time() - t0) * 1000
print(f"⏱️ Time: {dt:.0f}ms")

# Inspect Results
data = results.get('results', {})
for key, best_quote in data.items():
    print(f"\nKey: {key}")
    
    # Check if 'all_quotes' exists (it should per web3_pricing.py logic)
    all_qs = best_quote.get('all_quotes', [best_quote])
    
    for q in all_qs:
        dex = q.get('dex', 'UNKNOWN')
        strategy = q.get('strategy', 'N/A')
        amt = q.get('amountOut', 0)
        print(f"  > [{dex}] Strategy: {strategy} | AmountOut: {amt}")
        
        if "Kuru" in dex:
            print("    ✅ Kuru Found!")

print("\nDONE")
