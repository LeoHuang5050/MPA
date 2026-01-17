
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arbitrage_engine import TOKEN_MAP
from web3_pricing import KURU_MARKETS, CHOG_ADDR, PINKY_ADDR, WMON_ADDR, USDC_ADDR

print(f"TOKEN_MAP Size: {len(TOKEN_MAP)}")

# Check Specific Addresses
TARGETS = {
    "CHOG": CHOG_ADDR,
    "PINKY": PINKY_ADDR,
    "WMON": WMON_ADDR,
    "USDC": USDC_ADDR
}

for name, addr in TARGETS.items():
    key = addr.lower()
    val = TOKEN_MAP.get(key)
    print(f"{name} ({addr}) -> Key: {key} -> In Map? {'✅ ' + val if val else '❌ MISSING'}")

print("\n--- Kuru Market Pairs ---")
for pair_set in KURU_MARKETS.keys():
    addrs = list(pair_set)
    a0 = addrs[0].lower()
    a1 = addrs[1].lower() if len(addrs) > 1 else "???"
    
    s0 = TOKEN_MAP.get(a0, "UNK")
    s1 = TOKEN_MAP.get(a1, "UNK")
    print(f"Pair {addrs} -> {s0}/{s1}")
