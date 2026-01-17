
from web3 import Web3

RPC_URL = "https://rpc.monad.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

QUOTER_ADDR = "0xD7Ec145b53CB1a62dB42fc1bB27E050d8b835d8F"
AUSD = w3.to_checksum_address("0x00000000efe302beaa2b3e6e1b18d08d69a9012a")
USDC = w3.to_checksum_address("0x754704Bc059F8C67012fEd69BC8A327a5aafb603")

# Quoter V2 ABI (Just quoteExactInputSingle)
# Note: Monad Quoter might be V1 or V2?
# The error "Multicall failed" earlier might be due to encoding.
# I'll try generic V2 ABI
HASH_ABI = [{
    "inputs": [
        {
            "components": [
                {"internalType": "address", "name": "tokenIn", "type": "address"},
                {"internalType": "address", "name": "tokenOut", "type": "address"},
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint24", "name": "fee", "type": "uint24"},
                {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
            ],
            "internalType": "struct IQuoterV2.QuoteExactInputSingleParams",
            "name": "params",
            "type": "tuple"
        }
    ],
    "name": "quoteExactInputSingle",
    "outputs": [
        {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
        {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
        {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
        {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}
    ],
    "stateMutability": "nonpayable",
    "type": "function"
}]

# V1 Fallback ABI
V1_ABI = [{
    "inputs": [
        {"internalType": "address", "name": "tokenIn", "type": "address"},
        {"internalType": "address", "name": "tokenOut", "type": "address"},
        {"internalType": "uint24", "name": "fee", "type": "uint24"},
        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
        {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
    ],
    "name": "quoteExactInputSingle",
    "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
    "stateMutability": "nonpayable",
    "type": "function"
}]

quoter = w3.eth.contract(address=w3.to_checksum_address(QUOTER_ADDR), abi=HASH_ABI)
quoter_v1 = w3.eth.contract(address=w3.to_checksum_address(QUOTER_ADDR), abi=V1_ABI)

AMOUNT = 100 * 10**6
FEES = [100, 500, 3000]

print(f"Checking Quotes for 100 AUSD -> USDC (0x754...) on Monad")

for fee in FEES:
    print(f"\n--- Fee {fee} ---")
    
    # Try V2 Call
    try:
        params = {
            "tokenIn": AUSD,
            "tokenOut": USDC,
            "amountIn": AMOUNT,
            "fee": fee,
            "sqrtPriceLimitX96": 0
        }
        res = quoter.functions.quoteExactInputSingle(params).call()
        amt = res[0]
        print(f"✅ V2 Quote: {amt/1e6} USDC")
    except Exception as e:
        print(f"❌ V2 Failed: {e}")
        
        # Try V1 Call
        try:
            res = quoter_v1.functions.quoteExactInputSingle(AUSD, USDC, fee, AMOUNT, 0).call()
            # V1 returns int or tuple?
            if isinstance(res, int): amt = res 
            else: amt = res[0]
            print(f"✅ V1 Quote: {amt/1e6} USDC")
        except Exception as e1:
            print(f"❌ V1 Failed: {e1}")
