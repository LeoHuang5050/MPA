
from web3 import Web3

RPC_URL = "https://rpc.monad.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

QUOTER_ADDR = "0xD7Ec145b53CB1a62dB42fc1bB27E050d8b835d8F"
V2_FACTORY_CANONICAL = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

AUSD = "0x00000000efe302beaa2b3e6e1b18d08d69a9012a"
USDC_USER = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

# Quoter ABI subset
QUOTER_ABI = [
    {"inputs": [], "name": "factory", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "WETH9", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
]

# V2 Factory ABI
V2_ABI = [
    {"inputs": [{"internalType": "address", "name": "", "type": "address"}, {"internalType": "address", "name": "", "type": "address"}], "name": "getPair", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
]

quoter = w3.eth.contract(address=w3.to_checksum_address(QUOTER_ADDR), abi=QUOTER_ABI)
v2_factory = w3.eth.contract(address=w3.to_checksum_address(V2_FACTORY_CANONICAL), abi=V2_ABI)

print(f"Checking Quoter {QUOTER_ADDR}...")
try:
    f = quoter.functions.factory().call()
    w = quoter.functions.WETH9().call()
    print(f"✅ Quoter Factory: {f}")
    print(f"✅ Quoter WETH9: {w}")
    
    # Check this factory for pool?
    # I'll need V3 Factory ABI (getPool) - Reusing previous check if address matches 0x204f...
except Exception as e:
    print(f"❌ Quoter probe failed: {e}")

print(f"\nChecking V2 Factory {V2_FACTORY_CANONICAL}...")
try:
    pair = v2_factory.functions.getPair(
        w3.to_checksum_address(AUSD),
        w3.to_checksum_address(USDC_USER)
    ).call()
    
    if pair == "0x0000000000000000000000000000000000000000":
        print("❌ No V2 Pair found")
    else:
        print(f"✅ V2 Pair Found: {pair}")
except Exception as e:
    print(f"❌ V2 Probe failed: {e}")
