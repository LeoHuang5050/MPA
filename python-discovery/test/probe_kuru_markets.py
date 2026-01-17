
import requests
import json
import re

URLS_TO_TEST = [
    "https://rpc.kuru.io/markets",
    "https://rpc.kuru.io/tokens",
    "https://rpc.kuru.io/pairs",
    "https://api.kuru.io/markets",
    "https://www.kuru.io/api/markets"
]

PAGE_URL = "https://www.kuru.io/liquidity"

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'accept': 'application/json, text/plain, */*'
}

print("🕵️ Probing Kuru API Endpoints...")

found_data = False

for url in URLS_TO_TEST:
    try:
        print(f"  > GET {url} ...", end="", flush=True)
        resp = requests.get(url, headers=HEADERS, timeout=3)
        print(f" Status: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"    ✅ JSON Found! Keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                print(f"    Sample: {str(data)[:200]}")
                found_data = True
                break
            except:
                print("    (Not JSON)")
    except Exception as e:
        print(f" Error: {e}")

if not found_data:
    print(f"\n📄 Fetching Page: {PAGE_URL} ...")
    try:
        resp = requests.get(PAGE_URL, headers=HEADERS)
        html = resp.text
        print(f"  > Length: {len(html)} chars")
        
        # Look for NEXT_DATA or typical raw JSON structs
        # Regex for addresses
        addrs = re.findall(r'0x[a-fA-F0-9]{40}', html)
        print(f"  > Found {len(addrs)} potential addresses.")
        
        # Look for Moncock?
        if "moncock" in html.lower():
            print("  ✅ 'moncock' found in HTML text.")
        else:
            print("  ❌ 'moncock' NOT found in HTML text.")

        # Try to find built-in JSON blobs
        matches = re.findall(r'\{"address":"0x[a-fA-F0-9]{40}".*?\}', html)
        if matches:
            print(f"  > Found {len(matches)} JSON-like address objects.")
            print(f"  Sample: {matches[0][:200]}")

    except Exception as e:
        print(f"Failed to fetch page: {e}")
