from web3 import Web3
from web3_pricing import get_token_metadata, w3

# Addresses from user screenshot context or common knowledge
WMON_ADDR = "0x760AfE86e5de5fa0Ee542fc7721795a1dBCD9976" 
# aprMON: Need to find it. I'll search logs or just list a few pools.
# But for now checking WMON is a good start.

print(f"Checking WMON: {WMON_ADDR}")
meta = get_token_metadata(WMON_ADDR)
print(f"Metadata: {meta}")

# Check USDC as well
USDC = "0xf817257fed379853cDe0cc4F97AB48448Ee7D13C" # Example, might need to find from logs
# Actually let's just check the one from my source code variables if present
