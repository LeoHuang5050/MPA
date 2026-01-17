
from web3 import Web3
from web3_pricing import w3

# Kuru Router
ROUTER_ADDR = "0x1f5A250c4A506DA4cE584173c6ed1890B1bf7187"
ROUTER = w3.to_checksum_address(ROUTER_ADDR)

# WMON/USDC
WMON = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
USDC = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"

print(f"🕵️ Probing Kuru Router for Market/OrderBook getter...")

# Guessing common factory methods
METHODS = [
    "getMarket(address,address)",
    "getPair(address,address)",
    "markets(address,address)",
    "orderbooks(address,address)",
    "getL2Book(address,address)" 
]

contract_template = w3.eth.contract(address=ROUTER, abi=[])

for sig in METHODS:
    name = sig.split("(")[0]
    print(f"  > Testing {name}...")
    
    # Manually encode since we don't have full ABI
    selector = Web3.keccak(text=sig)[:4].hex()
    
    # Encode params: tokenA, tokenB
    try:
        # Padded addresses (32 bytes)
        data = selector + \
               w3.to_checksum_address(WMON)[2:].zfill(64) + \
               w3.to_checksum_address(USDC)[2:].zfill(64)
        
        res = w3.eth.call({
            "to": ROUTER,
            "data": data
        })
        
        print(f"    ✅ {name} returned: {res.hex()}")
        if len(res) >= 32:
            # Decode address (last 20 bytes of 32-byte word)
            addr = "0x" + res.hex()[-40:]
            print(f"    --> Potential Market Address: {addr}")
            
    except Exception as e:
        print(f"    ❌ {name} failed: {str(e)[:50]}")
