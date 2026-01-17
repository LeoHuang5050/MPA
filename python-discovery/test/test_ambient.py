from web3_pricing import get_bulk_quotes
import json

# Token Addresses (Monad Mainnet)
WMON = "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
USDC = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"

def test_ambient():
    print("🧪 Testing Ambient DEX Pricing...")
    
    # 1. WMON -> USDC
    amount_in_wmon = 1.0
    raw_in_wmon = int(amount_in_wmon * 10**18)
    
    reqs = [{
        "tokenIn": WMON,
        "tokenOut": USDC,
        "amountIn": raw_in_wmon
    }]
    
    print(f"\n1️⃣  Quoting {amount_in_wmon} WMON -> USDC")
    res = get_bulk_quotes(reqs, return_by_index=True)
    
    best = res['results'].get(0)
    if best:
        print(f"   ✅ Best Quote: {best['amountOut'] / 10**6:.4f} USDC")
        print(f"   📊 DEX: {best['dex']} ({best['fee']})")
        
        print("   📜 All Quotes:")
        all_q = res['results'].get(0).get('all_quotes', [])
        for q in all_q:
            print(f"      - {q['dex']} ({q['fee']}): {q['amountOut'] / 10**6:.4f}")
    else:
        print("   ❌ No quote found.")
        
    print("-" * 30)

    # 2. USDC -> WMON
    amount_in_usdc = 100.0
    raw_in_usdc = int(amount_in_usdc * 10**6)
    
    reqs2 = [{
        "tokenIn": USDC,
        "tokenOut": WMON,
        "amountIn": raw_in_usdc
    }]
    
    print(f"\n2️⃣  Quoting {amount_in_usdc} USDC -> WMON")
    res2 = get_bulk_quotes(reqs2, return_by_index=True)
    
    best2 = res2['results'].get(0)
    if best2:
        print(f"   ✅ Best Quote: {best2['amountOut'] / 10**18:.4f} WMON")
        print(f"   📊 DEX: {best2['dex']} ({best2['fee']})")
    else:
        print("   ❌ No quote found.")

if __name__ == "__main__":
    test_ambient()
