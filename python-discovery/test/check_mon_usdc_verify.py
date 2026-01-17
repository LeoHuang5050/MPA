
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from web3_pricing import w3, UNISWAP_V3_FACTORY_ADDRESS, FACTORY_ABI, USDC_ADDR

# Candidates for WMON
WMON_CANDIDATES = {
    "WMON_Real": "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701",
    "WMON_Alt": "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
}

FEES = [100, 500, 3000, 10000]

print(f"🏭 Checking Factory: {UNISWAP_V3_FACTORY_ADDRESS}")
factory = w3.eth.contract(address=UNISWAP_V3_FACTORY_ADDRESS, abi=FACTORY_ABI)

found_pool = False

for name, addr in WMON_CANDIDATES.items():
    print(f"\n🔍 Checking {name} ({addr}) <-> USDC ({USDC_ADDR})...")
    
    for fee in FEES:
        try:
            pool = factory.functions.getPool(
                w3.to_checksum_address(addr), 
                w3.to_checksum_address(USDC_ADDR), 
                fee
            ).call()
            
            if pool != "0x0000000000000000000000000000000000000000":
                print(f"✅ FOUND POOL! Fee: {fee}")
                print(f"   Address: {pool}")
                found_pool = True
            else:
                pass # print(f"   No pool for fee {fee}")
        except Exception as e:
            print(f"   ❌ Error {fee}: {e}")

if not found_pool:
    print("\n❌ No pools found for any candidate.")
    print("Possibilities:")
    print("1. Factory address is wrong.")
    print("2. Tokens are not listed on this V3 Factory.")
else:
    print("\n✅ Verification Complete. Pool Exists.")
