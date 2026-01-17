
from web3 import Web3
import sys

RPC_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 10}))

USDC_ADDR = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"
USER_ADDR = "0x02df3a3F960393F5B349E40A599FEda91a7cc1A7"

def check():
    if not w3.is_connected():
        print("❌ Cannot connect to local RPC")
        return
        
    print(f"Connected. Chain ID: {w3.eth.chain_id}")
    bal = w3.eth.get_balance(USER_ADDR)
    print(f"MON: {w3.from_wei(bal, 'ether')}")
    
    # Check USDC
    code = w3.eth.get_code(w3.to_checksum_address(USDC_ADDR))
    if len(code) == 0:
        print("❌ USDC contract NOT FOUND on this chain.")
        return
        
    abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
    c = w3.eth.contract(address=USDC_ADDR, abi=abi)
    u_bal = c.functions.balanceOf(USER_ADDR).call()
    print(f"USDC: {u_bal / 10**6}")

if __name__ == "__main__":
    check()
