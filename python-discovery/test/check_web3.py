import web3
print(f"Web3 Version: {web3.__version__}")
try:
    from web3 import AsyncWeb3
    print("AsyncWeb3: Available")
except ImportError:
    print("AsyncWeb3: Not Available")

try:
    from web3 import WebSocketProvider
    print("WebSocketProvider (Direct): Available")
except ImportError:
    print("WebSocketProvider (Direct): Not Available")
