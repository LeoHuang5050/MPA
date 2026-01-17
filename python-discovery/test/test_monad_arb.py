from web3_pricing import get_best_quote
from arbitrage_engine import TOKEN_MAP
import json

try:
    print("Testing Liquidity for USDC -> WMON on Monad Mainnet...")
    usdc = TOKEN_MAP["USDC"]
    wmon = TOKEN_MAP["WMON"]
    amount_in = 10 * 10**6 # 10 USDC
    
    print(f"Quoting {amount_in} USDC ({usdc}) -> WMON ({wmon})...")
    res = get_best_quote(usdc, wmon, amount_in)
    
    print(json.dumps(res, indent=2))
except Exception as e:
    import traceback
    traceback.print_exc()
