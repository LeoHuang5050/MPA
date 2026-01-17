
from web3 import Web3

RPC_TARGET = "https://rpc.monad.xyz"

def check_remote():
    w3 = Web3(Web3.HTTPProvider(RPC_TARGET))
    if not w3.is_connected():
        print(f"❌ Could not connect to {RPC_TARGET}")
        return
        
    print(f"Connected to {RPC_TARGET}")
    print(f"Chain ID: {w3.eth.chain_id}")
    
    targets = [
        ("WMON (143)", "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"),
        ("USDC (143)", "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"),
        ("Uni Quoter V2", "0x661E93cca42AfacB172121EF892830cA3b70F08d")
    ]
    
    for name, addr in targets:
        code = w3.eth.get_code(w3.to_checksum_address(addr))
        print(f"{name} at {addr}: {'✅ EXISTS' if len(code) > 0 else '❌ NOT FOUND'}")

if __name__ == "__main__":
    check_remote()
