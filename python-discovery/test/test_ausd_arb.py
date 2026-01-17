
from web3 import Web3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3_pricing import get_kuru_quote, get_best_quote, KURU_MARKETS, w3

# Constants
AUSD = "0x00000000efe302beaa2b3e6e1b18d08d69a9012a"
USDC = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603" 
AMOUNT_IN = 100 * 10**6 # 100 AUSD (Assuming 6 decimals)
DECIMALS_AUSD = 6
DECIMALS_USDC = 6

import web3_pricing
print(f"Loaded web3_pricing from: {web3_pricing.__file__}")

print(f"\n🔍 Testing AUSD -> USDC Arbitrage\n")
import sys
# 1. Test Kuru Quote
print("--- Kuru Quote ---")
sys.stdout.flush()
key = frozenset([AUSD, USDC])
if key in KURU_MARKETS:
    print(f"✅ Market Found: {KURU_MARKETS[key]}")
    try:
        # Fixed Signature: (token_in, token_out, amount_in, decimals_in, decimals_out)
        k_out = get_kuru_quote(AUSD, USDC, AMOUNT_IN, DECIMALS_AUSD, DECIMALS_USDC)
        k_out_fmt = k_out / 10**DECIMALS_USDC
        print(f"💰 100 AUSD -> {k_out_fmt:.6f} USDC")
    except Exception as e:
        print(f"❌ Kuru Error: {e}")
        k_out = 0
else:
    print(f"❌ Market NOT Found.")
    k_out = 0

# 2. Test Uniswap Quote
print("\n--- Uniswap V3 Quote ---")
try:
    u_res = get_best_quote(AUSD, USDC, AMOUNT_IN)
    if u_res['best']:
        best = u_res['best']
        u_out_fmt = best['amountOut'] / 10**DECIMALS_USDC
        print(f"💰 100 AUSD -> {u_out_fmt:.6f} USDC (Fee: {best['fee']} - {best['dex']})")
        
        if k_out > 0:
            price_k = k_out_fmt / 100
            price_u = u_out_fmt / 100
            print(f"\nPrices (USDC per AUSD):")
            print(f"Kuru: ${price_k:.6f}")
            print(f"Uni:  ${price_u:.6f}")
            
            # Simple Arbitrage Logic
            # If Kuru Price > Uni Price: Buy on Uni, Sell on Kuru
            # If Uni Price > Kuru Price: Buy on Kuru, Sell on Uni
            
            if price_k > price_u * 1.001: # 0.1% buffer
                profit = (price_k - price_u) * 100
                print(f"✨ ARB OPPORTUNITY: Buy Uni -> Sell Kuru (Profit: ${profit:.4f} per 100 AUSD)")
            elif price_u > price_k * 1.001:
                profit = (price_u - price_k) * 100
                print(f"✨ ARB OPPORTUNITY: Buy Kuru -> Sell Uni (Profit: ${profit:.4f} per 100 AUSD)")
            else:
                print("📉 No significant spread.")
    else:
        print("❌ No liquidity on Uniswap.")
except Exception as e:
    print(f"❌ Uniswap Error: {e}")
