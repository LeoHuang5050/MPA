
from web3 import Web3
import json

RPC_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

MON_ADDR = "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
USDC_ADDR = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"
USER_ADDR = "0x02df3a3F960393F5B349E40A599FEda91a7cc1A7"

ERC20_ABI = [
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

def check_balance():
    print(f"Checking balances for {USER_ADDR} on {RPC_URL}...")
    
    # Native MON
    native_balance = w3.eth.get_balance(USER_ADDR)
    print(f"Native MON: {w3.from_wei(native_balance, 'ether')} MON")
    
    # WMON
    wmon_contract = w3.eth.contract(address=MON_ADDR, abi=ERC20_ABI)
    wmon_bal = wmon_contract.functions.balanceOf(USER_ADDR).call()
    print(f"WMON: {wmon_bal / 10**18} WMON")
    
    # USDC
    usdc_contract = w3.eth.contract(address=USDC_ADDR, abi=ERC20_ABI)
    usdc_bal = usdc_contract.functions.balanceOf(USER_ADDR).call()
    print(f"USDC: {usdc_bal / 10**6} USDC")

if __name__ == "__main__":
    check_balance()
