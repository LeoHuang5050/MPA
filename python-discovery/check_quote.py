

import logging
from web3 import Web3
import sys

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_real_quote():
    print("\n🔍 Checking REAL Quotes for MON/USDC on Monad Mainnet...")
    
    # Real Monad RPC
    RPC_URL = "https://rpc.monad.xyz" 
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Monad RPC")
        return

    # Real Addresses (Monad Mainnet/Testnet)
    USDC_ADDR = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"
    WMON_ADDR = "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
    QUOTER_ADDR = "0x661E93cca42AfacB172121EF892830cA3b70F08d"

    # Minimal Quoter Interface
    ABI = [{
        "inputs": [{"components": [
            {"internalType": "address", "name": "tokenIn", "type": "address"},
            {"internalType": "address", "name": "tokenOut", "type": "address"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
        ], "internalType": "struct IQuoterV2.QuoteExactInputSingleParams", "name": "params", "type": "tuple"}],
        "name": "quoteExactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}, {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"}, {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"}, {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}],
        "stateMutability": "view", "type": "function"
    }]
    
    quoter = w3.eth.contract(address=QUOTER_ADDR, abi=ABI)
    
    # Check 1: Sell 1 USDC -> Buy MON?
    # User says: 1 USDC = 30 MON. (Cheap MON)
    print(f"\n--- Checking 1 USDC -> MON ---")
    try:
        params = {
            "tokenIn": USDC_ADDR,
            "tokenOut": WMON_ADDR,
            "amountIn": 1 * 10**6, # 1 USDC
            "fee": 3000,
            "sqrtPriceLimitX96": 0
        }
        res = quoter.functions.quoteExactInputSingle(params).call()
        amount_out = res[0] / 10**18
        print(f"✅ Quote: 1 USDC = {amount_out} MON")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Check 2: Sell 1 MON -> Buy USDC?
    print(f"\n--- Checking 1 MON -> USDC ---")
    try:
        params = {
            "tokenIn": WMON_ADDR,
            "tokenOut": USDC_ADDR,
            "amountIn": 1 * 10**18, # 1 MON
            "fee": 3000,
            "sqrtPriceLimitX96": 0
        }
        res = quoter.functions.quoteExactInputSingle(params).call()
        amount_out = res[0] / 10**6
        print(f"✅ Quote: 1 MON = {amount_out} USDC")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    check_real_quote()

