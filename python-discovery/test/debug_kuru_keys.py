
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from web3_pricing import KURU_MARKETS, WMON_ADDR, USDC_ADDR

print("🔍 Debugging Kuru Keys...")

wmon_checksum = Web3.to_checksum_address(WMON_ADDR)
usdc_checksum = Web3.to_checksum_address(USDC_ADDR)

print(f"WMON Checksum: {wmon_checksum}")
print(f"USDC Checksum: {usdc_checksum}")

key = frozenset([wmon_checksum, usdc_checksum])
print(f"Generated Key: {key}")

print(f"\nScanning Kuru Markets ({len(KURU_MARKETS)} entries):")
found = False
for k, v in KURU_MARKETS.items():
    if k == key:
        print(f"✅ FOUND MATCH! Market: {v}")
        found = True
        break
    # print(f"  - {k}")

if not found:
    print("❌ NO MATCH FOUND in KURU_MARKETS")
    print("\nCompare keys:")
    for k in KURU_MARKETS.keys():
        print(f"  Existing: {k}")
