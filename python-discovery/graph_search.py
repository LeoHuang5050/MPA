from web3_pricing import get_best_quote
import math
from arbitrage_engine import TOKEN_MAP # Dynamic Token Map

def find_arbitrage_path(token_in_symbol, token_out_symbol, amount_in):
    """
    Finds the best path by querying multiple DEXs via Web3.
    """
    token_in_symbol = token_in_symbol.upper()
    token_out_symbol = token_out_symbol.upper()
    
    # Alias Normalization
    if token_in_symbol == "ETH": token_in_symbol = "WETH"
    if token_out_symbol == "ETH": token_out_symbol = "WETH"
    if token_in_symbol == "MON": token_in_symbol = "WMON"
    if token_out_symbol == "MON": token_out_symbol = "WMON"
    
    # 1. Resolve Addresses (Dynamic)
    token_in_addr = TOKEN_MAP.get(token_in_symbol)
    token_out_addr = TOKEN_MAP.get(token_out_symbol)
    
    if not token_in_addr or not token_out_addr:
        return None, f"Unsupported token: {token_in_symbol if not token_in_addr else token_out_symbol}. Available: {list(TOKEN_MAP.keys())}"
        
    print(f"Finding best path for {amount_in} {token_in_symbol} -> {token_out_symbol} using On-Chain Pricing...")
    
    # 2. Get Best Quote
    # Adjust decimals. USDT/USDC = 6, WETH/DAI = 18.
    decimals_in = 18
    if token_in_symbol in ["USDC", "USDT"]: decimals_in = 6
    if token_in_symbol == "WBTC": decimals_in = 8
    
    raw_amount_in = int(float(amount_in) * (10**decimals_in))
    
    quote_result = get_best_quote(token_in_addr, token_out_addr, raw_amount_in)
    
    if not quote_result or not quote_result.get('best'):
        return None, "No liquidity found on supported DEXs (Uniswap V3, Kuru, Pancake V3, Ambient)."
        
    best_quote = quote_result['best']
    all_quotes = quote_result['all_quotes']
        
    # 3. Format Result
    decimals_out = 18
    if token_out_symbol in ["USDC", "USDT"]: decimals_out = 6
    if token_out_symbol == "WBTC": decimals_out = 8
    
    expected_output = float(best_quote['amountOut']) / (10**decimals_out)
    
    print(f"Best Route: {best_quote['dex']} (Fee: {best_quote['fee']}) -> {expected_output} {token_out_symbol}")
    
    # Format comparison list
    comparison = []
    for q in all_quotes:
        out_fmt = float(q['amountOut']) / (10**decimals_out)
        comparison.append({
            "dex": q['dex'],
            "fee": q['fee'],
            "amountOut": out_fmt,
            "gasEstimate": q['gasEstimate'],
            "isBest": q == best_quote
        })
    
    # Construct "Path" object
    detailed_path = [{
        "tokenIn": token_in_symbol,
        "tokenOut": token_out_symbol,
        "fee": best_quote['fee'],
        "dex": best_quote['dex'],
        "amountOut": expected_output
    }]
    
    return {
        "path": detailed_path,
        "raw_path": [token_in_symbol, token_out_symbol],
        "expectedOutput": expected_output,
        "dex": best_quote['dex'],
        "quotes": comparison
    }, None

