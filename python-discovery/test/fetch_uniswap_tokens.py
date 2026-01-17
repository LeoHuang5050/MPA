import requests
import json
import os

URL = 'https://gateway.ipfs.io/ipns/tokens.uniswap.org'
CHAIN_ID = 10143
OUTPUT_FILE = "uniswap_monad_tokens.json"

print(f"Fetching Uniswap Token List from {URL}...")

try:
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    tokens = data.get('tokens', [])
    monad_tokens = [t for t in tokens if t.get('chainId') == CHAIN_ID]
    
    print(f"Found {len(monad_tokens)} tokens for Chain ID {CHAIN_ID}.")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(monad_tokens, f, indent=4)
        
    print(f"✅ Saved to {OUTPUT_FILE}")
    
    # Print USDC address if found
    for t in monad_tokens:
        if t['symbol'] == 'USDC':
            print(f"ℹ️  Official USDC Address: {t['address']}")
            
except Exception as e:
    print(f"❌ Error fetching token list: {e}")
