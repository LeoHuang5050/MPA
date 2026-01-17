from web3_pricing import get_pool_info, w3

# WMON / USDC (Fee 3000)
# WMON: 0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A
# USDC: 0x754704Bc059F8C67012fEd69BC8A327a5aafb603

t1 = "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
t2 = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"

print("Fetching Pool Info for WMON/USDC (3000)...")
info = get_pool_info(t1, t2, 3000)

if info:
    print(f"✅ Pool Found: {info['address']}")
    print(f"💧 Liquidity: {info['liquidity']}")
    print(f"💲 SqrtPrice: {info['sqrtPriceX96']}")
    liq_eth = info['liquidity'] / 10**18
    print(f"🌊 Liquidity (Approx ETH): {liq_eth:.4f}")
    print(f"🛑 Whale Threshold (0.5%): {liq_eth * 0.005:.4f}")
else:
    print("❌ Pool Info returned None")
