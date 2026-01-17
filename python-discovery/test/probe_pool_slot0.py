
from web3 import Web3
import math

RPC_URL = "https://rpc.monad.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Pools found in Step 2174
POOLS = {
    100: "0x6B405DCA74897c9442d369DcF6c0EC230f7E1c7C",
    500: "0x0E9876A149112242A4C60D589C548ba877C0512e",
    3000: "0xf5F27C3E8DEFf1A3BAdf95CaA2BD2271b1B52192"
}

POOL_ABI = [
    {"inputs": [], "name": "slot0", "outputs": [
        {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
        {"internalType": "int24", "name": "tick", "type": "int24"},
        {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
        {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
        {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
        {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
        {"internalType": "bool", "name": "unlocked", "type": "bool"}
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "liquidity", "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}], "stateMutability": "view", "type": "function"}
]

def get_price_from_sqrt(sqrt_price_x96):
    price = (sqrt_price_x96 / (2**96)) ** 2
    # Adjust for decimals: AUSD (6) -> USDC (6) = No decimal shift needed (10^6/10^6 = 1)
    # Price is USDC per AUSD
    return price

print("Checking Slot0 for Pools...")
for fee, addr in POOLS.items():
    print(f"\n--- Fee {fee} ({addr}) ---")
    try:
        pool = w3.eth.contract(address=w3.to_checksum_address(addr), abi=POOL_ABI)
        slot0 = pool.functions.slot0().call()
        liq = pool.functions.liquidity().call()
        
        sqrt_price = slot0[0]
        tick = slot0[1]
        
        price = get_price_from_sqrt(sqrt_price)
        
        print(f"✅ Liquidity: {liq}")
        print(f"✅ SqrtPrice: {sqrt_price}")
        print(f"✅ Tick: {tick}")
        print(f"✅ Price: {price:.6f} USDC/AUSD")
        
        if liq == 0:
            print("⚠️ LIQUIDITY IS ZERO")
            
    except Exception as e:
        print(f"❌ Failed to read pool: {e}")
