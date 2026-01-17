
from web3 import Web3

RPC_URL = "https://rpc.monad.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

FACTORY_ADDR = "0x204faca1764b154221e35c0d20abb3c525710498" # Monad V3 Factory (Found in Search)
# Note: I'll also try Canonical if this fails.
AUSD = "0x00000000efe302beaa2b3e6e1b18d08d69a9012a"
USDC_USER = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603" # Mainnet USDC

# Standard V3 Factory ABI for getPool
ABI = [{
    "inputs": [
        {"internalType": "address", "name": "tokenA", "type": "address"},
        {"internalType": "address", "name": "tokenB", "type": "address"},
        {"internalType": "uint24", "name": "fee", "type": "uint24"}
    ],
    "name": "getPool",
    "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
}]

factory = w3.eth.contract(address=w3.to_checksum_address(FACTORY_ADDR), abi=ABI)

print(f"Checking for pools in Factory {FACTORY_ADDR}")
print(f"Token A: {AUSD}")
print(f"Token B: {USDC_USER}")

fees = [100, 500, 3000, 10000]

found_any = False
for fee in fees:
    pool = factory.functions.getPool(
        w3.to_checksum_address(AUSD),
        w3.to_checksum_address(USDC_USER),
        fee
    ).call()
    
    if pool == "0x0000000000000000000000000000000000000000":
        print(f"Fee {fee}: No Pool")
    else:
        print(f"Fee {fee}: ✅ Found Pool at {pool}")
        found_any = True

if not found_any:
    print("❌ No AUSD/USDC_USER pools found in the Factory.")
