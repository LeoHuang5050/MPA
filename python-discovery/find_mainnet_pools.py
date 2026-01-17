
from web3_pricing import w3, UNISWAP_V3_FACTORY_ADDRESS, FACTORY_ABI, WMON_ADDR, USDC_ADDR

print(f"Factory: {UNISWAP_V3_FACTORY_ADDRESS}")
print(f"WMON: {WMON_ADDR}")
print(f"USDC: {USDC_ADDR}")

factory = w3.eth.contract(address=UNISWAP_V3_FACTORY_ADDRESS, abi=FACTORY_ABI)

fees = [100, 500, 3000, 10000]

for fee in fees:
    try:
        pool = factory.functions.getPool(
            w3.to_checksum_address(WMON_ADDR), 
            w3.to_checksum_address(USDC_ADDR), 
            fee
        ).call()
        if pool != "0x0000000000000000000000000000000000000000":
            print(f"✅ Found Pool (Fee {fee}): {pool}")
        else:
            print(f"❌ No Pool (Fee {fee})")
    except Exception as e:
        print(f"Error checking fee {fee}: {e}")
