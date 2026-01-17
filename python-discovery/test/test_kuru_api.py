
import requests
import json
import time

URL = 'https://rpc.kuru.io/swap'

# WMON -> USDC
PAYLOAD = {
    "tokenIn": "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701",
    "tokenOut": "0x754704Bc059F8C67012fEd69BC8A327a5aafb603",
    "amount": "100000000000000000", # 0.1 WMON (18 decimals)
    "autoSlippage": False,
    "slippageTolerance": 30
}

HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://www.kuru.io',
    'referer': 'https://www.kuru.io/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"🌍 POST {URL}")
print(f"📦 Payload: {json.dumps(PAYLOAD, indent=2)}")

try:
    t0 = time.time()
    resp = requests.post(URL, data=json.dumps(PAYLOAD), headers=HEADERS)
    dt = (time.time() - t0) * 1000
    
    print(f"✅ Response ({dt:.0f}ms): {resp.status_code}")
    print(resp.text)
except Exception as e:
    print(f"❌ Failed: {e}")
