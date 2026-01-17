import requests
import json
import time

print("🔍 Testing Global Market Scan...")
start = time.time()
try:
    resp = requests.post("http://localhost:5001/find_arbitrage", json={
        "token": "ALL",
        "amount": 1000
    })
    print(f"⏱️ Time: {time.time() - start:.2f}s")
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(e)
