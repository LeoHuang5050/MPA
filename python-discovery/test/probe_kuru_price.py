
from web3 import Web3
from web3_pricing import w3

# Kuru WMON/USDC Market
MARKET_ADDR = "0x065C9d28E428A0db40191a54d33d5b7c71a9C394"
MARKET = w3.to_checksum_address(MARKET_ADDR)

ABI = [
    {
        "inputs": [],
        "name": "bestBidAsk",
        "outputs": [
            {"internalType": "uint32", "name": "", "type": "uint32"},
            {"internalType": "uint32", "name": "", "type": "uint32"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

print(f"🕵️ Probing Kuru Market at {MARKET}...")

contract = w3.eth.contract(address=MARKET, abi=ABI)

try:
    # Manual call to see raw bytes
    selector = Web3.keccak(text="bestBidAsk()")[:4]
    raw_res = w3.eth.call({"to": MARKET, "data": selector})
    print(f"✅ Raw Hex: {raw_res.hex()}")
    
    # Attempt manual slice
    # Expected: 2 * 32 bytes (tuples usually padded to 32 bytes)
    if len(raw_res) >= 64:
        val1 = int.from_bytes(raw_res[0:32], 'big')
        val2 = int.from_bytes(raw_res[32:64], 'big')
        print(f"   Slice [0:32]: {val1} ({hex(val1)})")
        print(f"   Slice [32:64]: {val2} ({hex(val2)})")
    
    # Heuristic check
    # WMON is ~$1 (if peg). USDC is $1.
    # If price is ~1.0, and raw is say 1000, then scale is 1000?
    # Or maybe it's high precision?
    print(f"   Bid Hex: {hex(bid_raw)}")
    print(f"   Ask Hex: {hex(ask_raw)}")

except Exception as e:
    print(f"❌ Failed: {e}")
