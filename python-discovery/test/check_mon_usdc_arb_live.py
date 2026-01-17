
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from web3 import Web3
from web3_pricing import w3, get_pool_info, get_uniswap_v3_price, USDC_ADDR

# 1. SETUP ADDRESSES
WMON_KURU = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701" 
WMON_UNI = "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
USDC = USDC_ADDR

# Kuru Market Address (MON/USDC)
MARKET_KURU = "0x065C9d28E428A0db40191a54d33d5b7c71a9C394"

print("🔍 Checking MON/USDC Arbitrage Live...")
print(f"  Uniswap WMON: {WMON_UNI}")
print(f"  Kuru WMON:    {WMON_KURU}")

def check_arb():
    # 1. Get Uniswap Price (Sell 1 WMON -> USDC)
    amount_in_wmon = 1 * 10**18
    fees = [100, 500, 3000, 10000]
    
    uni_prices = {}
    
    for fee in fees:
        try:
            # get_uniswap_v3_price(token_in, token_out, amount, fee)
            usdc_out = get_uniswap_v3_price(WMON_UNI, USDC, amount_in_wmon, fee)
            if usdc_out > 0:
                val = usdc_out / 10**6
                uni_prices[fee] = val
                print(f"  ✅ Uniswap (Fee {fee}): 1 MON = ${val:.6f}")
        except Exception as e:
            # print(f"Error Uniswap {fee}: {e}")
            pass

    # 2. Get Kuru Price
    import requests
    price_kuru = 0.0
    try:
        resp = requests.get(f"https://api.kuru.io/api/v1/market/{MARKET_KURU}")
        data = resp.json()
        price_kuru = float(data.get('stats', {}).get('lastPrice', 0))
    except:
        pass
        
    print(f"\n📊 Snapshot:")
    if price_kuru > 0:
        print(f"  Kuru Orderbook:        1 MON ≈ ${price_kuru:.6f}")
    else:
        print(f"  Kuru:                  (API Error)")

    # Compare
    for fee, u_price in uni_prices.items():
        if price_kuru > 0:
            diff = abs(u_price - price_kuru)
            pct = (diff / price_kuru) * 100
            if pct > 0.05: # Show gaps > 0.05%
                print(f"\n💡 Gap (Fee {fee}): {pct:.2f}%")
                if u_price > price_kuru:
                     print(f"  Strategy: Buy Kuru (${price_kuru}) -> Sell Uniswap (${u_price})")
                else:
                     print(f"  Strategy: Buy Uniswap (${u_price}) -> Sell Kuru (${price_kuru})")

if __name__ == "__main__":
    check_arb()
