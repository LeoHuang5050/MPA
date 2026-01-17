
from web3_pricing import get_best_quote
from web3 import Web3

# Tokens
AUSD = "0x00000000efe302beaa2b3e6e1b18d08d69a9012a"
USDC_MAIN = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603" # Current config
USDC_TEST = "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea" # Monad Tokens JSON
USDC_GECKO = "0x3f23d172e0b0497b6aab290b4207b58c1b4ad8e0" # Gecko
USDC_USER = "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" # User Screenshot (Mainnet addr)

AMOUNT_IN = 1 * 10**5 # 0.1 AUSD (Assuming 6 decimals)

print(f"Comparing AUSD Prices (Amount In: {AMOUNT_IN/1e6} AUSD)")
print(f"Using Quoter via Multicall (get_best_quote)")

def check(name, addr):
    print(f"\n--- {name} ({addr}) ---")
    try:
        # Assuming USDC has 6 decimals? User screenshot USDC usually 6.
        # But if it's bridged WETH maybe 18?
        # get_best_quote signature: (token_in, token_out, amount_in, decimals_in, decimals_out)
        # Note: get_best_quote returns dict {"best": ..., "all_quotes": ...}
        res = get_best_quote(AUSD, addr, AMOUNT_IN)
        if res and res['best']:
            amt = res['best']['amountOut']
            fee = res['best']['fee']
            print(f"✅ Price: {amt/1e6} USDC (Fee: {fee})")
        else:
            print(f"❌ No Quote (Liquidity < {AMOUNT_IN})")
    except Exception as e:
        print(f"Error: {e}")

check("USDC_MAIN (Current)", USDC_MAIN)
check("USDC_TEST (JSON)", USDC_TEST)
check("USDC_GECKO", USDC_GECKO)
check("USDC_USER (Screenshot)", USDC_USER)
