
from web3 import Web3
import json

RPC_URL = "https://rpc.monad.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

MARKET_ADDR = "0x699abc15308156e9a3ab89ec7387e9cfe1c86a3b" # AUSD/USDC Kuru Market

# Generic ERC20/Market Interface
ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
]
# Kuru might not use token0/token1 standard names? 
# "orderBook" usually has base/quote tokens.
# Looking at Kuru docs or previous probe...
# I'll rely on web3_pricing.py KURU_ABI? No, it only had bestBidAsk.
# I'll try token0/token1 first (common standard). If fails, I'll search for Kuru interface.
# Actually, I'll allow failure.

contract = w3.eth.contract(address=w3.to_checksum_address(MARKET_ADDR), abi=ABI)

print(f"Probing Kuru Market: {MARKET_ADDR}")
try:
    t0 = contract.functions.token0().call()
    t1 = contract.functions.token1().call()
    print(f"Token0: {t0}")
    print(f"Token1: {t1}")
except Exception as e:
    print(f"Standard token0/token1 failed: {e}")
    # Try assuming it holds the tokens.
