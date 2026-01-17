
from web3 import Web3
from web3_pricing import w3

# Kuru Router
ROUTER_ADDR = "0x1f5A250c4A506DA4cE584173c6ed1890B1bf7187"
ROUTER = w3.to_checksum_address(ROUTER_ADDR)

# WMON/USDC
WMON = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
USDC = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"

# Common ABIs to test
ABIS = {
    "getAmountsOut": [
        {
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "path", "type": "address[]"}
            ],
            "name": "getAmountsOut",
            "outputs": [{"name": "amounts", "type": "uint256[]"}],
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "getAmountOut": [
        {
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"}
            ],
            "name": "getAmountOut",
            "outputs": [{"name": "amountOut", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "quote": [
        {
             "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"}
            ],
            "name": "quote",
            "outputs": [{"name": "amountOut", "type": "uint256"}],
             "stateMutability": "view",
            "type": "function"
        }
    ]
}

print(f"🕵️ Probing Kuru Router at {ROUTER}...")

amount_in = int(0.1 * 10**18) # 0.1 WMON

for method_name, abi in ABIS.items():
    contract = w3.eth.contract(address=ROUTER, abi=abi)
    print(f"  > Testing {method_name}...")
    try:
        if method_name == "getAmountsOut":
            res = contract.functions.getAmountsOut(amount_in, [WMON, USDC]).call()
            print(f"    ✅ Success! Result: {res}")
        elif method_name == "getAmountOut":
            res = contract.functions.getAmountOut(amount_in, WMON, USDC).call()
            print(f"    ✅ Success! Result: {res}")
        elif method_name == "quote":
             res = contract.functions.quote(amount_in, WMON, USDC).call()
             print(f"    ✅ Success! Result: {res}")
             
    except Exception as e:
        print(f"    ❌ Failed: {str(e)[:50]}...")
