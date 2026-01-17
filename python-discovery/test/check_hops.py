
from web3_pricing import get_best_quote
from web3 import Web3

# Tokens
AUSD = "0x00000000efe302beaa2b3e6e1b18d08d69a9012a"
USDC_MAIN = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"
WMON = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"

AMOUNT = 100 * 10**6 # 100 AUSD / USDC
AMOUNT_WMON = 1 * 10**18 # 1 WMON

print("Checking Multi-Hop Path Liquidity:")
print(f"1. AUSD -> WMON (In: 100 AUSD)")
res = get_best_quote(AUSD, WMON, AMOUNT)
if res and res['best']:
    amt = res['best']['amountOut']
    print(f"   ✅ Out: {amt/1e18} WMON (Fee: {res['best']['fee']})")
else:
    print(f"   ❌ No Liquidity")

print(f"2. WMON -> USDC (In: 1 WMON)")
res = get_best_quote(WMON, USDC_MAIN, AMOUNT_WMON)
if res and res['best']:
    amt = res['best']['amountOut']
    print(f"   ✅ Out: {amt/1e6} USDC (Fee: {res['best']['fee']})")
else:
    print(f"   ❌ No Liquidity")
    
print(f"3. Direct AUSD -> USDC (In: 100 AUSD)")
res = get_best_quote(AUSD, USDC_MAIN, AMOUNT)
if res and res['best']:
    amt = res['best']['amountOut']
    print(f"   ✅ Out: {amt/1e6} USDC (Fee: {res['best']['fee']})")
else:
    print(f"   ❌ No Liquidity")
