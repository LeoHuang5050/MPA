
from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("https://rpc.monad.xyz"))

MARKET_ADDR = w3.to_checksum_address("0x699abc15308156e9a3ab89ec7387e9cfe1c86a3b") # AUSD/USDC
ABI = [{"inputs":[],"name":"bestBidAsk","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]

c = w3.eth.contract(address=MARKET_ADDR, abi=ABI)

print(f"Probing {MARKET_ADDR}...")
try:
    bid, ask = c.functions.bestBidAsk().call()
    print(f"Bid: {bid}")
    print(f"Ask: {ask}")
    
    if bid == 0 and ask == 0:
        print("⚠️ Orderbook is likely empty!")
    else:
        print("✅ Orderbook has liquidity.")
except Exception as e:
    print(f"Error: {e}")
