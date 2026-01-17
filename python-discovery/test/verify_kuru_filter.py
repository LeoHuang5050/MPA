
from web3_pricing import KURU_MARKETS

# Derive Set
KURU_TOKENS_SET = set()
for pair in KURU_MARKETS.keys():
    for addr in pair:
        KURU_TOKENS_SET.add(addr.lower())
        KURU_TOKENS_SET.add(addr)

print(f"✅ Active Kuru Tokens: {len(KURU_TOKENS_SET)/2:.0f} assets.")

# Mock Events
evts = [
    {
        "type": "WHALE_SWAP", 
        "token0": {"symbol": "CHOG", "address": "0x350035555e10d9afaf1566aaebfced5ba6c27777", "decimals": 18}, # Kuru Asset
        "token1": {"symbol": "WMON", "address": "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701", "decimals": 18}  # Kuru Asset
    },
    {
        "type": "WHALE_SWAP", 
        "token0": {"symbol": "FAKE", "address": "0x1111111111111111111111111111111111111111", "decimals": 18}, # Mixed
        "token1": {"symbol": "WMON", "address": "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701", "decimals": 18}  # Kuru Asset
    },
    {
        "type": "WHALE_SWAP", 
        "token0": {"symbol": "GARBAGE", "address": "0x9999999999999999999999999999999999999999", "decimals": 18},
        "token1": {"symbol": "TRASH", "address": "0x8888888888888888888888888888888888888888", "decimals": 18}
    }
]

dynamic_tokens = {}

print("\n🔍 Running Relaxed Filter Logic...")

for evt in evts:
    if evt.get('type') == 'WHALE_SWAP':
        t0 = evt['token0']
        t1 = evt['token1']
        t0_addr = t0['address']
        t1_addr = t1['address']
        
        # KEY LOGIC: Relaxed
        if t0_addr not in KURU_TOKENS_SET and t1_addr not in KURU_TOKENS_SET:
            print(f"❌ Rejected {t0['symbol']}/{t1['symbol']} (No Kuru Asset)")
            continue
            
        print(f"✅ Accepted {t0['symbol']}/{t1['symbol']}")
        dynamic_tokens[t0['symbol']] = t0['address']

if "CHOG" in dynamic_tokens and "FAKE" in dynamic_tokens and "GARBAGE" not in dynamic_tokens:
    print("\n🎉 TEST PASSED: Relaxed Filter works (Accepted Mixed, Rejected Garbage).")
else:
    print("\n🚨 TEST FAILED!")
