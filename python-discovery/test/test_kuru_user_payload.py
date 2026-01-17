
import requests
import json
import time

URL = 'https://rpc.kuru.io/swap'

# User's exact payload
PAYLOAD = {
    "tokenIn": "0x00000000eFE302BEAA2b3e6e1b18d08D69a9012a",
    "tokenOut": "0x0000000000000000000000000000000000000000",
    "amount": "1000000",
    "autoSlippage": True,
    "slippageTolerance": 30
}

HEADERS = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://www.kuru.io',
    'referer': 'https://www.kuru.io/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
}

print(f"🌍 POST {URL}")
print(f"📦 Payload: {json.dumps(PAYLOAD, indent=2)}")

try:
    resp = requests.post(URL, data=json.dumps(PAYLOAD), headers=HEADERS)
    print(f"✅ Response: {resp.status_code}")
    print(resp.text)
except Exception as e:
    print(f"❌ Failed: {e}")
