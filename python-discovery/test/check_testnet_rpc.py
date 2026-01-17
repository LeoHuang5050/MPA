
from web3 import Web3

TESTNET_RPC = "https://testnet-rpc.monad.xyz"
w3 = Web3(Web3.HTTPProvider(TESTNET_RPC))

print(f"Connecting to {TESTNET_RPC}...")
try:
    if w3.is_connected():
        cid = w3.eth.chain_id
        print(f"✅ Connected! Chain ID: {cid}")
        if cid == 10143:
            print("confirmed: This is Monad Testnet.")
            
            # Check Kuru Market (AUSD/USDC) from Mainnet config
            KURU_ADDR = "0x699abc15308156e9a3ab89ec7387e9cfe1c86a3b"
            code_kuru = w3.eth.get_code(w3.to_checksum_address(KURU_ADDR))
            if len(code_kuru) > 0:
                print(f"✅ Kuru Market {KURU_ADDR} EXISTS on Testnet!")
            else:
                print(f"❌ Kuru Market {KURU_ADDR} DOES NOT EXIST on Testnet.")

            # Check Uniswap Quoter
            QUOTER_ADDR = "0xD7Ec145b53CB1a62dB42fc1bB27E050d8b835d8F"
            code_quoter = w3.eth.get_code(w3.to_checksum_address(QUOTER_ADDR))
            if len(code_quoter) > 0:
                print(f"✅ Uniswap Quoter {QUOTER_ADDR} EXISTS on Testnet!")
            else:
                print(f"❌ Uniswap Quoter {QUOTER_ADDR} DOES NOT EXIST on Testnet.")
        else:
            print(f"Mismatch: Expected 10143, got {cid}")
    else:
        print("❌ Connection Failed.")
except Exception as e:
    print(f"❌ Error: {e}")
