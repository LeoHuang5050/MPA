
from web3_pricing import get_best_quote
from web3 import Web3

WMON = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
USDC_USER = "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

AMOUNT = 1 * 10**18 # 1 WMON

print(f"Checking WMON -> USDC_USER ({USDC_USER})")

res = get_best_quote(WMON, USDC_USER, AMOUNT)
if res and res['best']:
    print(f"✅ Price: {res['best']['amountOut']/1e6} USDC (Fee: {res['best']['fee']})")
else:
    print(f"❌ No Quote for WMON -> USDC_USER")
