
import json
from arbitrage_engine import scan_market, PRICE_CACHE
from web3_pricing import get_bulk_quotes, DISABLE_OTHER_DEXS, AMBIENT_QUERY_ADDRESS, UNISWAP_V3_QUOTER_ADDRESS

print(f"✨ CONFIG: DISABLE_OTHER_DEXS={DISABLE_OTHER_DEXS}")
print(f"✨ CONFIG: AMBIENT_QUERY={AMBIENT_QUERY_ADDRESS}")
print(f"✨ CONFIG: UNISWAP_QUOTER={UNISWAP_V3_QUOTER_ADDRESS}")

# WMON and USDC
WMON_ADDR = "0x760AfE86e5de5fa0Ee542fc7B713e1c5425701" # From logs
USDC_ADDR = "0xf817257fed379858cDeF50435565097D9D80d9d2" # From monad_tokens.json (hypothetically)

# wait, better use addresses from app logs 
# WMON: 0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701
# USDC: 0x754704Bc059F8C67012fEd69BC8A327a5aafb603 (from step 734)

WMON_ADDR = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
USDC_ADDR = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"

override_tokens = {
    "WMON": WMON_ADDR,
    "USDC": USDC_ADDR
}

override_decimals = {
    "WMON": 18,
    "USDC": 6
}

print(f"🧪 DEBUG: Testing Raw Quotes for WMON <-> USDC")

# Manually construct requests equivalent to what scan_market does
requests = []
tokens = ["WMON", "USDC"]

# Simple 1-tier pass ($10)
target_usdt = 10 
price_in = 1.0 
amount_readable = target_usdt / price_in
raw_amt = int(amount_readable * (10**18)) # WMON 18 decimals

# WMON -> USDC
idx = 0
requests.append({
    "tokenInSymbol": "WMON",
    "tokenOutSymbol": "USDC",
    "tokenIn": WMON_ADDR,
    "tokenOut": USDC_ADDR,
    "amountIn": raw_amt,
    "amountReadable": amount_readable,
    "tier": 10
})

# USDC -> WMON
requests.append({
    "tokenInSymbol": "USDC",
    "tokenOutSymbol": "WMON",
    "tokenIn": USDC_ADDR,
    "tokenOut": WMON_ADDR,
    "amountIn": raw_amt, # Note: Using WMON amount for simplicity but technically wrong decimals if tokenIn is USDC. 
                         # But for test it doesn't matter much if we just check connectivity.
    "amountReadable": amount_readable,
    "tier": 10
})

print(f"  > Sending {len(requests)} requests...")

# Call get_bulk_quotes directly
res = get_bulk_quotes(requests)
output = res['results']
net_ms = res['network_ms']

print(f"  ✅ Received output. MS: {net_ms}")
print("\n🔍 RAW QUOTES RETURNED:")

for req_idx, data in output.items():
    req = requests[req_idx]
    print(f"\nRequest {req_idx}: {req['tokenInSymbol']} -> {req['tokenOutSymbol']}")
    print(f"  Best Quote: {data['amountOut']} ({data['strategy']})")
    
    if 'all_quotes' in data:
        print("  All Quotes:")
        for q in data['all_quotes']:
            print(f"    - [{q['dex']}] Strat: {q['strategy']}, Out: {q['amountOut']}")

