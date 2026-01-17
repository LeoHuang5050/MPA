
import sys
import os
from web3 import Web3

# Add current dir to path to import local modules
sys.path.append(os.getcwd())

from web3_pricing import w3, get_best_quote, get_token_metadata, get_kuru_quote, WMON_ADDR, USDC_ADDR, UNISWAP_V3_QUOTER_ADDRESS
from arbitrage_engine import TOKEN_MAP

def test_swap_diagnostic():
    print(f"--- SWAP DIAGNOSTIC SCAN ---")
    print(f"Connected to RPC: {w3.provider.endpoint_uri}")
    print(f"Chain ID: {w3.eth.chain_id}")
    
    # 1. Check Contracts Existence (Verified Monad Mainnet Addresses)
    targets = [
        ("WMON (Mainnet)", "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"),
        ("USDC (Mainnet)", "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"),
        ("MockDEX (Local)", "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"),
        ("MockUSDC (Local)", "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"),
        ("HiveAccount", "0x0165878A594ca255338adfa4d48449f69242Eb8F")
    ]
    
    for name, addr in targets:
        code = w3.eth.get_code(w3.to_checksum_address(addr))
        exists = len(code) > 0
        print(f"Contract {name} at {addr}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")

    # 2. Test Token Resolution
    t_in = "MON"
    t_out = "USDC"
    addr_in = TOKEN_MAP.get("WMON") # graph_search converts MON to WMON
    addr_out = TOKEN_MAP.get("USDC")
    
    print(f"\nResolution:")
    print(f"  {t_in} -> {addr_in}")
    print(f"  {t_out} -> {addr_out}")

    print(f"\nTesting Kuru Quote directly (10 MON -> USDC)...")
    try:
        from web3_pricing import get_token_metadata
        # Check if we should use Mock USDC decimals (18 in some mocks, 6 in others)
        meta_out = get_token_metadata(addr_out)
        dec_out = meta_out.get('decimals', 6)
        
        amt_in_raw = 10 * 10**18
        k_out = get_kuru_quote(addr_in, addr_out, amt_in_raw, 18, dec_out)
        print(f"  Kuru Raw Output: {k_out}")
        if k_out > 0:
            print(f"  Kuru Human Output: {k_out / 10**dec_out} USDC")
        else:
            print(f"  Kuru returned 0 (Likely bestBidAsk is (0,0) on this fork)")
    except Exception as e:
        print(f"  Kuru Error: {e}")

    # 4. Test Uni Quote directly
    print(f"\nTesting get_best_quote (includes Multicall for Uni & individual Kuru)...")
    res = get_best_quote(addr_in, addr_out, amt_in_raw)
    
    if res['best']:
        print(f"🏆 BEST QUOTE FOUND: {res['best']['dex']}")
        print(f"  Amount Out: {res['best']['amountOut']}")
        for q in res['all_quotes']:
            print(f"  - {q['dex']} (Fee {q['fee']}): {q['amountOut']}")
    else:
        print(f"❌ NO QUOTES FOUND")
        print(f"  Network Duration: {res.get('network_ms', 0):.2f}ms")

if __name__ == "__main__":
    test_swap_diagnostic()
