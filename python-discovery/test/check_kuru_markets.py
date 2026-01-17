
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from web3_pricing import KURU_MARKETS, w3

# Load Token Map
try:
    with open('monad_tokens.json', 'r') as f:
        data = json.load(f)
    TOKEN_MAP = {}
    for t in data.get('tokens', []):
        if t.get('chainId') == 143:
            TOKEN_MAP[t['address'].lower()] = t['symbol']
except:
    TOKEN_MAP = {}
    print("⚠️ Could not load monad_tokens.json")

print(f"Checking {len(KURU_MARKETS)} Kuru Markets on Current Chain (143)...")

for pair, addr in KURU_MARKETS.items():
    # pair is frozenset of token addresses
    tokens = list(pair)
    if len(tokens) < 2: continue
    
    t0_addr = tokens[0]
    t1_addr = tokens[1]
    
    s0 = TOKEN_MAP.get(t0_addr.lower(), f"UNK({t0_addr[:6]})")
    s1 = TOKEN_MAP.get(t1_addr.lower(), f"UNK({t1_addr[:6]})")
    
    try:
        addr_checksum = w3.to_checksum_address(addr)
        code = w3.eth.get_code(addr_checksum)
        status = "✅ EXISTS" if len(code) > 0 else "❌ MISSING"
    except Exception as e:
        status = f"❌ ERROR ({e})"
        
    print(f"Market {s0}/{s1} ({addr}): {status}")
