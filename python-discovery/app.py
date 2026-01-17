import time
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from web3_pricing import (
    get_best_quote,
    get_pool_info,
    get_kuru_quote,
    KURU_MARKETS,
    w3,
    mainnet_w3,
    get_token_metadata,
    get_token_balance
)
from arbitrage_engine import scan_market, TOKEN_MAP, ADDR_TO_SYM
from graph_search import find_arbitrage_path
from monad_sentinel import monitor_transactions, KNOWN_POOLS
import threading
import datetime
from collections import deque
import asyncio

# Kuru API Stats Cache
KURU_STATS = {}
LAST_KURU_UPDATE = 0
KURU_API_URL = "https://api.kuru.io/api/v2/vaults?limit=100&offset=0"

def update_kuru_stats():
    global KURU_STATS, LAST_KURU_UPDATE
    if time.time() - LAST_KURU_UPDATE < 60: # Cache for 60s
        return

    try:
        headers = {
            "accept": "*/*",
            "origin": "https://www.kuru.io",
            "referer": "https://www.kuru.io/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(KURU_API_URL, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get('data', {}).get('data', [])
            for item in data:
                mkt = item.get('marketaddress', '').lower()
                if not mkt: continue
                
                tvl = item.get('tvl24h', 0)
                base = item.get('basetoken', {})
                quote = item.get('quotetoken', {})
                
                KURU_STATS[mkt] = {
                    "tvl": tvl,
                    "t0_sym": base.get('ticker', 'UNK'),
                    "t1_sym": quote.get('ticker', 'UNK'),
                    "t0_addr": base.get('address'),
                    "t1_addr": quote.get('address')
                }
                
            LAST_KURU_UPDATE = time.time()
            print(f"✅ Updated Kuru Stats ({len(KURU_STATS)} markets)")
        else:
            print(f"⚠️ Kuru API Failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Kuru Fetch Error: {e}")

# Derive Set of Interest (Tokens traded on Kuru)
KURU_TOKENS_SET = set()
for pair in KURU_MARKETS.keys():
    for addr in pair:
        KURU_TOKENS_SET.add(addr.lower())
        KURU_TOKENS_SET.add(addr) # Keep both case variants to be safe

print(f"✅ Active Kuru Tokens: {len(KURU_TOKENS_SET)/2:.0f} assets.")

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

print(f"🚀 App initialized with {len(TOKEN_MAP)} tokens in Global Map.")
print(f"   (WMON Address: {TOKEN_MAP.get('WMON', 'Not Found')})")

# Constants
KNOWN_TOKENS = {
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
}

# Seed Uniswap Pools (Required for Arbitrage Engine, but hidden from Dashboard)
def seed_uniswap_pools():
    print("🌱 Seeding Uniswap V3 Pools for Arbitrage Graph...")
    from web3_pricing import get_pool_info, get_token_metadata, get_token_balance
    
    # Priority Pairs to Track
    pairs = [
        ("WMON", "USDC"),
        ("WMON", "USDT"),
        ("WMON", "CHOG"),
        ("WMON", "DAC"),
        ("WMON", "MOLANDAK")
    ]
    fees = [500, 3000, 10000]
    
    count = 0
    for sym0, sym1 in pairs:
        addr0 = TOKEN_MAP.get(sym0)
        addr1 = TOKEN_MAP.get(sym1)
        if not addr0 or not addr1: continue
        
        for fee in fees:
            try:
                # get_pool_info returns {address, liquidity, ...} or None
                info = get_pool_info(addr0, addr1, fee)
                if info:
                    pool_addr = info['address']
                    if pool_addr in KNOWN_POOLS: continue
                    
                    # Fetch Metadata
                    meta0 = get_token_metadata(addr0)
                    meta1 = get_token_metadata(addr1)
                    
                    # Approx TVL (Sync calls)
                    bal0 = get_token_balance(addr0, pool_addr)
                    bal1 = get_token_balance(addr1, pool_addr)
                    
                    # Simple TVL Algo
                    tvl = 0
                    if "USD" in sym0 or "USD" in sym1:
                        non_usd_bal = bal0 if "USD" in sym1 else bal1
                        usd_bal = bal1 if "USD" in sym1 else bal0
                        tvl = usd_bal * 2
                        if tvl < 100 and non_usd_bal > 0: # If one side empty?
                             tvl = 0 # Ignore empty pools
                    else:
                        # WMON pairs
                        if "WMON" in sym0: tvl = bal0 * 2 * 0.02 # Approx $0.02 Mon (conservative)
                        elif "WMON" in sym1: tvl = bal1 * 2 * 0.02
                    
                    if tvl < 10: continue # Skip dust pools
                    
                    KNOWN_POOLS[pool_addr] = {
                        "name": f"{sym0}/{sym1} ({fee/10000}%)",
                        "t0_addr": addr0,
                        "t1_addr": addr1,
                        "t0_sym": sym0,
                        "t1_sym": sym1,
                        "t0_dec": meta0['decimals'],
                        "t1_dec": meta1['decimals'],
                        "tvl": tvl,
                        "threshold": max(50, tvl * 0.005),
                        "fee": fee / 10000.0,
                        "dex": "Uniswap V3"
                    }
                    count += 1
            except Exception as e:
                print(f"Failed to seed {sym0}/{sym1}: {e}")
                
    print(f"✅ Seeded {count} Uniswap Pools for Graph (Hidden from Dashboard).")

# Run Seeding
seed_uniswap_pools()

# Global Event Log
RECENT_EVENTS = deque(maxlen=50)

def start_background_sentinel():
    """
    Runs the async sentinel in a background thread.
    """
    def run_loop():
        # RUNNING IN THREAD
        print(f"[{datetime.datetime.now()}] 🛡️ Sentinel Background Thread Starting...")
        
        # Callback to update global list
        def on_event(event):
            try:
                # KURU STAGE 2 FILTER: Show if ANY Kuru token is involved
                # Relaxed from strict pair match
                if 'token0' in event and 'token1' in event:
                    t0 = event['token0']['address']
                    t1 = event['token1']['address']
                    
                    if t0 in KURU_TOKENS_SET or t1 in KURU_TOKENS_SET:
                        RECENT_EVENTS.appendleft(event)
                    # else:
                        # print(f"DEBUG: Ignored feed event {event['pool']} (Not Kuru)")
            except Exception as e:
                print(f"Callback Error: {e}")

        # Run the sentinel using asyncio.run() to create a fresh loop for this thread
        try:
            asyncio.run(monitor_transactions(callback=on_event))
        except Exception as e:
            print(f"Sentinel Loop Critical Error: {e}")

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    print("🛡️ Sentinel Thread Launched.")

@app.route('/find_path', methods=['POST'])
def find_path():
    data = request.json
    token_in = data.get('tokenIn', 'WETH')
    token_out = data.get('tokenOut', 'USDC')
    amount = data.get('amount', 1.0)
    
    result, error = find_arbitrage_path(token_in, token_out, amount)
    
    if error:
        return jsonify({"success": False, "message": error}), 400
        
    return jsonify({"success": True, "data": result})

@app.route('/find_arbitrage', methods=['POST'])
def find_arbitrage():
    data = request.json
    token_symbol = data.get('token', 'USDT')
    amount = data.get('amount', 1000)
    mode = data.get('mode', 'all') 
    
    if token_symbol.upper() == "ALL" or token_symbol.upper() == "MARKET":
        # Dynamic Discovery Logic
        dynamic_tokens = {}
        dynamic_decimals = {}
        
        # 1. Harvest tokens from recent live swaps
        if len(RECENT_EVENTS) > 0:
            # Focus on latest WHALE events (Last 10)
            slice_events = list(RECENT_EVENTS)[:10]
            
            for evt in slice_events:
                # User Requirement: Only scan if it's a WHALE_SWAP
                # User Requirement: Only scan if it's a WHALE_SWAP AND involves Kuru tokens
                if evt.get('type') == 'WHALE_SWAP':
                    if 'token0' in evt and 'token1' in evt:
                        t0 = evt['token0']
                        t0_addr = t0['address']
                        
                        t1 = evt['token1']
                        t1_addr = t1['address']
                        
                        # KURU RELAXED FILTER: 
                        # Monitor if AT LEAST ONE token is a Kuru asset
                        # (e.g. Someone buying MON on Uni with ETH -> We want to see it)
                        if t0_addr not in KURU_TOKENS_SET and t1_addr not in KURU_TOKENS_SET:
                            # Both matched tokens are NOT on Kuru -> Ignore
                            # print(f"DEBUG: Skipping {t0['symbol']}/{t1['symbol']} (No Kuru Asset)")
                            continue

                        # If passed filter, add to dynamic list
                        dynamic_tokens[t0['symbol']] = t0['address']
                        dynamic_decimals[t0['symbol']] = t0['decimals']
                        dynamic_tokens[t1['symbol']] = t1['address']
                        dynamic_decimals[t1['symbol']] = t1['decimals']
                
            print(f"🎯 Focused Scan on {len(dynamic_tokens)} Active Whale Tokens")

        # 2. Ensure WMON is present (Vital for pivot)
        if "WMON" not in dynamic_tokens and "WMON" in TOKEN_MAP:
             dynamic_tokens["WMON"] = TOKEN_MAP["WMON"]
             dynamic_decimals["WMON"] = 18

        # Prepare Pool Info Map for Logs
        # Key: (SymbolA, SymbolB) sorted -> Data
        pool_info_map = {}
        for addr, p in KNOWN_POOLS.items():
            key = tuple(sorted([p.get('t0_sym'), p.get('t1_sym')]))
            pool_info_map[key] = p

        # 3. Only Run Scan if we found WHALE activity (plus WMON)
        # Needs at least 2 tokens (Pivot + Target)
        if len(dynamic_tokens) >= 2: 
             # Pass dynamic tokens AND pool info
             result = scan_market(
                 override_tokens=dynamic_tokens, 
                 override_decimals=dynamic_decimals,
                 pool_info_map=pool_info_map
             )
        else:
             # Idle - No Whales Found
             # User Request: Default Scan MON/USDC if no whales
             if "AUSD" in TOKEN_MAP and "USDC" in TOKEN_MAP:
                 print("💤 No Whale Activity. Running Default Scan (AUSD/USDC) [Active Liquidity]...")
                 dynamic_tokens["AUSD"] = TOKEN_MAP["AUSD"]
                 dynamic_decimals["AUSD"] = 6
                 dynamic_tokens["USDC"] = TOKEN_MAP["USDC"]
                 dynamic_decimals["USDC"] = 6
                 
                 result = scan_market(
                     override_tokens=dynamic_tokens, 
                     override_decimals=dynamic_decimals,
                     pool_info_map=pool_info_map
                 )
             else:
                 print("💤 No Whale Activity. Skipping Scan (Missing MON/USDC in Map).")
                 result = {
                     "found": False, 
                     "logs": ["Waiting for Whale Activity..."], 
                     "profit_pct": 0, 
                     "best": None,
                     "ranking": [] 
                 }
             
        if result['best']:
            best = result['best']
            
            # Create a summary log of all results
            total_scanned = result.get('total_scanned', len(result['ranking']))
            summary_logs = [f"🌍 Global Market Scan: Analyzed {total_scanned} Assets"]
            for idx, item in enumerate(result['ranking']):
                # Simple emoji ranking
                icon = "🏆" if idx == 0 else ("🥈" if idx == 1 else ("🥉" if idx == 2 else "•"))
                summary_logs.append(f"{icon} #{idx+1} {item['token']}: {item['profit_pct']:.4f}% ({item['strategy']})")
                
            summary_logs.append("")
            summary_logs.append(f"🔍 Inspecting Winner: {best['token']}...")
            
            # Combine summary with best detailed logs
            # Filter out the specific "Scanning Strategies" line from the detail logs to avoid confusion
            detail_logs = [l for l in best['logs'] if "Scanning Strategies for" not in l]
            final_logs = summary_logs + detail_logs
            
            print(f"📉 Scan Complete. Best Profit: {best['profit_pct']:.4f}% ({best['token']})")
            
            return jsonify({
                "success": True, 
                "data": {
                    "found": best['profit_pct'] > 0,
                    "mode": f"Market Scan (Winner: {best['token']})",
                    "profit": 0, 
                    "profit_pct": best['profit_pct'],
                    "logs": final_logs,
                    "ranking": result['ranking']
                }
            })
        else:
             return jsonify({"success": True, "data": {"found": False, "logs": ["No opportunities found in market."], "profit_pct": 0, "ranking": result.get("ranking", [])}})

    else:
        # Manual/Specific Scan Logic (e.g. "WMON/USDC" or "CHOG")
        print(f"🤖 AI Command: Scanning specific target '{token_symbol}'...")
        
        dynamic_tokens = {}
        dynamic_decimals = {}
        
        # Parse Input
        targets = []
        if "/" in token_symbol:
            targets = token_symbol.split("/")
        else:
            targets = [token_symbol]
            
        # Resolve Tokens
        found_count = 0
        for sym in targets:
            sym_clean = sym.strip().upper()
            # Map standard aliases
            if sym_clean == "MON": sym_clean = "WMON"
            
            if sym_clean in TOKEN_MAP:
                dynamic_tokens[sym_clean] = TOKEN_MAP[sym_clean]
                dynamic_decimals[sym_clean] = 18 if sym_clean == "WMON" else 6 # Approx
                found_count += 1
        
        # Ensure we have at least 2 tokens for a graph (Target + WMON pivot usually)
        if "WMON" not in dynamic_tokens and "WMON" in TOKEN_MAP:
             dynamic_tokens["WMON"] = TOKEN_MAP["WMON"]
             dynamic_decimals["WMON"] = 18

        # Prepare Pool Info
        pool_info_map = {}
        for addr, p in KNOWN_POOLS.items():
            key = tuple(sorted([p.get('t0_sym'), p.get('t1_sym')]))
            pool_info_map[key] = p

        # Run Scan
        if len(dynamic_tokens) >= 2:
             result = scan_market(
                 override_tokens=dynamic_tokens, 
                 override_decimals=dynamic_decimals,
                 pool_info_map=pool_info_map
             )
        else:
             return jsonify({"success": False, "message": f"Could not resolve tokens for '{token_symbol}'. Available: {list(TOKEN_MAP.keys())}"}), 400

        # Return Result
        if result['best']:
            best = result['best']
            # Filter logs
            detail_logs = [l for l in best['logs'] if "Scanning Strategies for" not in l]
            
            return jsonify({
                "success": True, 
                "data": {
                    "found": best['profit_pct'] > 0,
                    "mode": f"Manual Scan ({token_symbol})",
                    "profit": 0, 
                    "profit_pct": best['profit_pct'],
                    "net_profit_usd": best.get('net_profit_usd', 0),
                    "logs": detail_logs,
                    "ranking": result['ranking'],
                    "best": best # Pass full best obj for frontend
                }
            })
        else:
             return jsonify({
                 "success": True, 
                 "data": {
                     "found": False, 
                     "logs": ["No profitable paths found for this pair."], 
                     "profit_pct": 0, 
                     "ranking": [] 
                 }
             })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "Python Discovery Engine"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    return jsonify({
        "success": True, 
        "data": list(RECENT_EVENTS)
    })

@app.route('/pools', methods=['GET'])
def get_pools():
    # 1. Update Stats from Kuru API
    update_kuru_stats()
    
    ambient_pools = []
    
    # 2. Return pools directly from API data
    for mkt_addr, data in KURU_STATS.items():
        real_tvl = data['tvl']
        
        # Dynamic Whale Threshold
        # Logic: Threshold = 0.5% of TVL, capped at min 50, max 2000
        threshold = 50
        if real_tvl > 0:
            calc_threshold = real_tvl * 0.005 # 0.5%
            threshold = max(50, min(calc_threshold, 2000))
        
        ambient_pools.append({
            "name": f"{data['t0_sym']}/{data['t1_sym']}",
            "t0_sym": data['t0_sym'],
            "t1_sym": data['t1_sym'],
            "tvl": real_tvl, 
            "threshold": threshold,
            "fee": 0.0, # Kuru is orderbook
            "dex": "Kuru"
        })
    
    # Sort by TVL descending
    ambient_pools.sort(key=lambda x: x['tvl'], reverse=True)

    return jsonify({
        "success": True, 
        "data": ambient_pools
    })

if __name__ == '__main__':
    print("Starting Python Discovery Service on port 5001...")
    
    # Start Sentinel
    start_background_sentinel()
    
    # Threaded=True allows multiple requests to be processed
    # use_reloader=False prevents duplicate threads
    app.run(host='0.0.0.0', port=5001, threaded=True, use_reloader=False)
