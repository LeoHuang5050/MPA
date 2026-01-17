
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3_pricing import w3, KURU_MARKETS, KURU_ABI
from web3 import Web3

print("--- Chain ID Verification ---")
chain_id = w3.eth.chain_id
print(f"Current Web3 Chain ID: {chain_id}")

EXPECTED_CHAIN_ID = 10143
if chain_id == EXPECTED_CHAIN_ID:
    print("✅ Chain ID matches Monad Testnet (10143)")
else:
    print(f"❌ Chain ID MISMATCH! Expected {EXPECTED_CHAIN_ID}, got {chain_id}")

print("\n--- Kuru Market Verification ---")
# Pick the AUSD/USDC market
# KURU_MARKETS keys are frozensets of addresses.
# I need to find the one for AUSD/USDC
AUSD = "0x00000000efe302beaa2b3e6e1b18d08d69a9012a"
USDC = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"

market_addr = None
for k, v in KURU_MARKETS.items():
    if AUSD in k and USDC in k:
        market_addr = v
        break

if market_addr:
    print(f"Testing Kuru Market: {market_addr}")
    contract = w3.eth.contract(address=w3.to_checksum_address(market_addr), abi=KURU_ABI)
    try:
        # Call bestBidAsk (view function)
        bid, ask = contract.functions.bestBidAsk().call()
        print(f"✅ Contract Response: Bid={bid}, Ask={ask}")
        print("Kuru Market is ACTIVE and responding on this chain.")
    except Exception as e:
        print(f"❌ Contract Call Failed: {e}")
else:
    print("❌ Could not find AUSD/USDC market in configuration.")
