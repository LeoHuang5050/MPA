
import json
from concurrent.futures import ThreadPoolExecutor
from web3 import Web3
from web3_pricing import w3

AMBIENT_QUERY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "base", "type": "address"},
            {"internalType": "address", "name": "quote", "type": "address"},
            {"internalType": "uint256", "name": "poolIdx", "type": "uint256"}
        ],
        "name": "queryPrice",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Second Batch of candidates
CANDIDATES = [
   "0xcafd2f0a35a4459fa40c0517e17e6fa2939441ca", # 7 hits
   "0x9563a59c15842a6f322b10f69d1dd88b41f2e97b", # 7 hits
   "0xaE8dc4a7438801Ec4edC0B035EcCCcF3807F4CC1", # 5 hits
   "0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5", # 5 hits
   "0xCa1D5a146B03f6303baF59e5AD5615ae0b9d146D", # 4 hits
   "0x6c84a8f1c29108F47a79964b5Fe888D4f4D0dE40", # 4 hits
   "0x61fFE014bA17989E743c5F6cB21bF9697530B21e", # 4 hits
   "0x3Ff72741fd67D6AD0668d93B41a09248F4700560", # 4 hits
]

# WMON/USDC Pair (Pool 420)
BASE = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
QUOTE = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"

# Ensure sorted for Ambient
if int(BASE, 16) > int(QUOTE, 16):
    BASE, QUOTE = QUOTE, BASE

print(f"🕵️ Testing {len(CANDIDATES)} candidates for WMON/USDC price...")

def check_addr(addr):
    try:
        query_contract = w3.eth.contract(address=addr, abi=AMBIENT_QUERY_ABI)
        # Try queryPrice
        price = query_contract.functions.queryPrice(BASE, QUOTE, 420).call()
        return (addr, True, price)
    except Exception as e:
        return (addr, False, str(e)[:100])

for c in CANDIDATES:
    res = check_addr(c)
    status = "✅ FOUND!" if res[1] else "❌ Failed"
    print(f"{status} {c}: {res[2]}")
    
