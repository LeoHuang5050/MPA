
import requests
import json
import time

URL = "https://api.kuru.io/api/v2/vaults?limit=100&offset=0"

HEADERS = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'origin': 'https://www.kuru.io',
    'referer': 'https://www.kuru.io/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"🌍 GET {URL} ...")

try:
    resp = requests.get(URL, headers=HEADERS, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        
        # Drill down into nested 'data' if present
        inner_data = data.get('data', {})
        items = inner_data.get('data', []) # Standard pattern: {data: {data: [...]}}
        
        # Verify extraction
        if not items:
            print("⚠️ Inner 'data.data' is empty. Dumping keys:")
            if isinstance(inner_data, dict):
                 print(f"Inner Keys: {inner_data.keys()}")
            
        print(f"✅ Extracted Items Count: {len(items)}")

        moncock_addr = "0x3d0322302F3A374c4E968a3563964d3F893a7433".lower()
        wmon_addr = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701".lower() 
        
        found_moncock = False
        
        with open("kuru_markets_debug.json", "w") as f:
            json.dump(items, f, indent=2)

        for i, item in enumerate(items):
            if i == 0:
                print(f"Sample Item Keys: {item.keys()}")
                print(f"Sample Full Dump: {json.dumps(item)[:500]}")
            
            # Robust Extraction (LOWERCASE KEYS from API)
            t_base = (item.get('basetoken') or {}).get('address', '').lower()
            t_quote = (item.get('quotetoken') or {}).get('address', '').lower()
            
            # Key is 'marketaddress'
            m_addr = item.get('marketaddress') or item.get('vaultaddress') or item.get('address')
            
            sym_base = (item.get('basetoken') or {}).get('ticker', '???')
            sym_quote = (item.get('quotetoken') or {}).get('ticker', '???')
            
            print(f"  > Pair {i}: {sym_base}/{sym_quote} ({m_addr})")
            
            if (t_base == moncock_addr and t_quote == wmon_addr) or \
               (t_base == wmon_addr and t_quote == moncock_addr):
                   print(f"\n🚀 FOUND MONCOCK MARKET!")
                   print(f"   Address: {m_addr}")
                   found_moncock = True
                   
        if not found_moncock:
            print("\n❌ Moncock market not found in this batch.")

    else:
        print(f"❌ Error: {resp.text}")

except Exception as e:
    print(f"❌ Exception: {e}")
