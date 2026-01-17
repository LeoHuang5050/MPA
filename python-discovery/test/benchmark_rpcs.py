import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor

RPCS = [
    "https://rpc.monad.xyz",
    "https://monad-mainnet.api.onfinality.io/public",
    "https://rpc-mainnet.monadinfra.com",
    "https://monad-mainnet.drpc.org",
    # Testnet
    "https://testnet-rpc.monad.xyz",
    "https://monad-testnet.api.onfinality.io/public",
    "https://monad-testnet.drpc.org"
]

PAYLOAD = {
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": 1
}

def test_rpc(url):
    try:
        start = time.perf_counter()
        resp = requests.post(url, json=PAYLOAD, timeout=5)
        resp.raise_for_status()
        duration = (time.perf_counter() - start) * 1000
        return f"{url}: {duration:.0f}ms (Success)"
    except Exception as e:
        return f"{url}: Failed ({str(e)})"

def main():
    print("🚀 Benchmarking RPCs...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(test_rpc, RPCS)
        
    for res in results:
        print(res)

if __name__ == "__main__":
    main()
