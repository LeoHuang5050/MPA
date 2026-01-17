from web3 import Web3
from web3_pricing import get_bulk_quotes, get_pool_info
import time
import json
import random
from collections import defaultdict

import os

# Monad Mainnet Token Map (Dynamic Loader)
# Monad Mainnet Token Map (Dynamic Loader)
TOKEN_MAP = {}
ADDR_TO_SYM = {}
TOKEN_DECIMALS = {}

def load_token_map():
    global TOKEN_MAP, TOKEN_DECIMALS, ADDR_TO_SYM
    
    # Default Fallback (Synchronized with web3_pricing.py and monad_tokens.json)
    TOKEN_MAP = {
        "WMON": "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A", 
        "USDC": "0x754704Bc059F8C67012fEd69BC8A327a5aafb603",
        "USDT": "0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D"
    }
    TOKEN_DECIMALS = {
        "WMON": 18, "USDC": 6, "USDT": 6
    }
    
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'monad_tokens.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            count = 0
            for t in data.get('tokens', []):
                if t.get('chainId') == 143:
                    sym = t['symbol']
                    addr = t['address']
                    dec = t['decimals']
                    TOKEN_MAP[sym] = addr
                    ADDR_TO_SYM[addr.lower()] = sym
                    TOKEN_DECIMALS[sym] = dec
                    count += 1
            print(f"✅ Loaded {count} tokens from monad_tokens.json")
        else:
            print("⚠️ monad_tokens.json not found, using default fallback.")
            
    except Exception as e:
        print(f"❌ Error loading token list: {e}")

# Initial Load
load_token_map()

# Initial Price Estimates (USDT value) to bootstrap the cache
# These will be updated dynamically after each scan
PRICE_CACHE = {
    "WMON": 0.027, 
    "USDC": 1.0,
    "USDT": 1.0,
    "CHOG": 0.22,
    "MOYAKI": 0.001,
    "MOLANDAK": 0.001
}

# Scan Tiers (Target USDT Value)
TIERS = [1, 10, 100]

def update_price_cache(results, requests):
    """
    Updates PRICE_CACHE based on the latest scan results relative to USDT.
    This allows the next scan to use more accurate 'amountIn' values.
    """
    # Simple logic: Find any direct rate Token -> USDT in the results
    # We look for Tier 2 ($10) or Tier 3 ($100) results for stability
    
    updates = {}
    
    for req_idx, result in results.items():
        req = requests[req_idx]
        t_in = req['tokenInSymbol']
        t_out = req['tokenOutSymbol']
        
        # If this is a trade TO a stablecoin, use it to update price
        if t_out in ["USDT", "USDC"]:
            # Correct Logic: rate = readable_out / readable_in
            # req['amountReadable'] is the USD target (e.g. 10)
            # result['amountOut'] is raw output units
            
            out_decimals = TOKEN_DECIMALS.get(t_out, 6) # USDT/USDC defaults to 6
            readable_out = result['amountOut'] / (10**out_decimals)
            
            if req['amountReadable'] > 0:
                rate = readable_out / req['amountReadable'] 
                
                # Sanity Check: Price shouldn't behave wildly (e.g. > $1M or < $0.000000001 for these tokens)
                if rate > 0.00000001 and rate < 1000000:
                    if req['tier'] >= 10:
                        updates[t_in] = rate
               
    for t, p in updates.items():
        PRICE_CACHE[t] = p
        # print(f"DEBUG: Updated Cache {t}: ${p:.6f}")

def calculate_net_profit(amount_in_usd, profit_pct, gas_estimate=200000):
    """
    Simulates net profit accounting for Gas.
    amount_in_usd: Input value in USD
    profit_pct: Gross profit percentage
    gas_estimate: Estimated gas units (default 200k for swap)
    """
    gross_profit_usd = amount_in_usd * (profit_pct / 100.0)
    
    # Gas Price: Assumed 50 Gwei for Monad Testnet (can be dynamic)
    GAS_PRICE_GWEI = 50
    gas_cost_mon = (gas_estimate * GAS_PRICE_GWEI) / 10**9
    mon_price = PRICE_CACHE.get("WMON", 0.01)
    gas_cost_usd = gas_cost_mon * mon_price
    
    net_profit_usd = gross_profit_usd - gas_cost_usd
    return net_profit_usd, gas_cost_usd

def analyze_graph_for_tier(graph, tier_value, pool_info_map=None):
    """
    Finds arbitrage cycles in a specific tier's graph.
    """
    opportunities = []
    pivot = "WMON"
    
    # 1. Spatial (2-Hop)
    for intermediate in graph[pivot]:
        if intermediate not in graph: continue
        
        edge1 = graph[pivot].get(intermediate)
        edge2 = graph[intermediate].get(pivot)
        
        if edge1 and edge2:
            # FILTER: Arbitrage must be between different markets (or at least different fee tiers)
            # Strict Mode: Prevent Same-DEX wash trading (e.g. Kuru -> Kuru on same pair)
            if edge1.get('dex') == edge2.get('dex') and edge1.get('fee') == edge2.get('fee'):
                continue

            rate1 = edge1['rate']
            rate2 = edge2['rate']
            final_rate = rate1 * rate2
            profit_pct = (final_rate - 1) * 100
            
            # SANITY CHECK: Ignore absurd profits (> 500%) -> Likely Data Error
            if profit_pct > 500:
                 # print(f"⚠️ Ignored absurd profit: {profit_pct:.2f}% ({pivot}->{intermediate})")
                 continue
            
            if profit_pct > -100:
                net_profit, gas_cost = calculate_net_profit(tier_value, profit_pct, gas_estimate=300000)
                
                # FILTER: Ignore results where loss exceeds principal (e.g. liquidity dry + gas)
                if net_profit <= -tier_value:
                    continue 

                # Construct Detailed Path Log
                # E.g. "Uniswap V3 (3000): Swap 100 WMON -> 3.5 USDC"
                
                # Input Amount for first leg
                leg1_in = tier_value / PRICE_CACHE.get(pivot, 1.0) # Approx units
                leg1_out = leg1_in * rate1
                leg2_out = leg1_out * rate2
                
                opportunities.append({
                    "strategy": f"Spatial (${tier_value})",
                    "path": f"{pivot} -> {intermediate} -> {pivot}",
                    "token": pivot,
                    "token_pair": f"{pivot}/{intermediate}",
                    "profit_pct": profit_pct,
                    "net_profit_usd": net_profit,
                    "logs": [
                        f"Step 1: {edge1.get('dex')} ({edge1.get('fee')}): Swap {pivot} -> {intermediate}",
                        f"   Rate: {rate1:.6f} | Est. Out: {leg1_out:.4f}",
                        f"Step 2: {edge2.get('dex')} ({edge2.get('fee')}): Swap {intermediate} -> {pivot}",
                        f"   Rate: {rate2:.6f} | Est. Out: {leg2_out:.4f}",
                        f"⛽ Gas: ${gas_cost:.4f} | 💵 Net Profit: ${net_profit:.4f}",
                        f"🌊 Pool Liquidity ({pivot}/{intermediate}): {get_pool_meta(pool_info_map, pivot, intermediate, 'tvl')}",
                        f"🛑 Whale Alert Threshold: > {get_pool_meta(pool_info_map, pivot, intermediate, 'threshold')}",
                        f"🆚 Comparison: Uniswap V3 (Monad) ({profit_pct:.4f}%) vs Simulated DEX B ({profit_pct - 0.06:.4f}%)"
                    ],
                    "details": {
                         "dex1": edge1.get('dex'),
                         "dex2": edge2.get('dex')
                    }
                })
                
    # 2. Triangular (3-Hop)
    for b in graph[pivot]:
        if b not in graph: continue
        for c in graph[b]:
            if c == pivot or c not in graph: continue
            
            edge1 = graph[pivot].get(b)
            edge2 = graph[b].get(c)
            edge3 = graph[c].get(pivot)
            
            if edge1 and edge2 and edge3:
                rate1 = edge1['rate']
                rate2 = edge2['rate']
                rate3 = edge3['rate']
                final_rate = rate1 * rate2 * rate3
                profit_pct = (final_rate - 1) * 100
                
                if profit_pct > -100:
                    net_profit, gas_cost = calculate_net_profit(tier_value, profit_pct, gas_estimate=450000)
                    
                    # FILTER: Ignore results where loss exceeds principal
                    if net_profit <= -tier_value:
                        continue
                    
                    opportunities.append({
                        "strategy": f"Triangular (${tier_value})",
                        "path": f"{pivot} -> {b} -> {c} -> {pivot}",
                        "token": pivot,
                        "profit_pct": profit_pct,
                        "net_profit_usd": net_profit,
                        "logs": [
                            f"Step 1: {pivot} -> {b} (Rate: {rate1:.6f})",
                            f"Step 2: {b} -> {c} (Rate: {rate2:.6f})",
                            f"Step 3: {c} -> {pivot} (Rate: {rate3:.6f})",
                            f"💰 Est. Gas Cost: ${gas_cost:.4f}",
                            f"💵 Net Profit: ${net_profit:.4f}"
                        ]
                    })
                    
    return opportunities


def get_pool_meta(pool_map, t1, t2, field):
    if not pool_map: return "Unknown"
    # Try both orders
    key1 = tuple(sorted([t1, t2]))
    if key1 in pool_map:
        val = pool_map[key1].get(field, "Unknown")
        if isinstance(val, (int, float)):
             if field == 'tvl': return f"${val:,.2f}"
             if field == 'threshold': return f"${val:,.2f}"
        return val
    return "Unknown"

def scan_market(override_tokens=None, override_decimals=None, pool_info_map=None):
    """
    Dynamic Multi-Tier Scan:
    1. Calculate amounts for each token to match $1, $10, $100.
    2. Fetch ALL tiers in ONE Multicall.
    3. Analyze each tier separately.
    """
    print(f"🌍 Starting Dynamic Multi-Tier Scan...")
    start_time = time.time()
    
    # 0. determine token set
    if override_tokens and len(override_tokens) > 1:
        print(f"  🔹 Using Dynamic Token Set: {override_tokens}")
        # print(f"  🔹 Using Dynamic Token Set: {list(override_tokens.keys())}")
        target_map = override_tokens
        target_decimals = override_decimals or {}
    else:
        target_map = TOKEN_MAP
        target_decimals = TOKEN_DECIMALS

    # 1. Build Requests for All Pairs & Tiers
    tokens = list(target_map.keys())
    requests = []
    
    # Track which request belongs to which tier: req_idx -> tier_idx
    req_tier_map = {} 
    
    for t_in in tokens:
        price_in = PRICE_CACHE.get(t_in, 0.000001) # Avoid div by zero
        if price_in == 0: price_in = 0.000001
        
        for tier_idx, target_usdt in enumerate(TIERS):
            # Calculate dynamic amountIn to match target value
            # e.g. Target $10, Price $0.027 -> Amount = 370 WMON
            amount_readable = target_usdt / price_in
            dec = target_decimals.get(t_in, 18)
            raw_amt = int(amount_readable * (10**dec))
            
            # Avoid dust errors for weird tokens
            if raw_amt <= 0: raw_amt = 1000
            
            for t_out in tokens:
                if t_in == t_out: continue
                
                # FILTER: Must be in Kuru OR Known Pools
                from web3_pricing import KURU_MARKETS
                
                # Check Kuru (Handle Checksum)
                addr_a = Web3.to_checksum_address(target_map[t_in])
                addr_b = Web3.to_checksum_address(target_map[t_out])
                kuru_key = frozenset([addr_a, addr_b])
                in_kuru = kuru_key in KURU_MARKETS
                
                # Check Uniswap (pool_info_map)
                in_uni = False
                if pool_info_map:
                    uni_key = tuple(sorted([t_in, t_out]))
                    if uni_key in pool_info_map:
                        in_uni = True
                        
                if not in_kuru and not in_uni:
                    # Skip if neither DEX has this pair
                    continue

                req_idx = len(requests)
                requests.append({
                    "tokenInSymbol": t_in,
                    "tokenOutSymbol": t_out,
                    "tokenIn": target_map[t_in],
                    "tokenOut": target_map[t_out],
                    "amountIn": raw_amt,
                    "amountReadable": amount_readable,
                    "tier": target_usdt
                })
                req_tier_map[req_idx] = target_usdt
            
    print(f"  > Generated {len(requests)} requests ({len(tokens)*(len(tokens)-1)} Edges * {len(TIERS)} Tiers).")
    
    # 2. Fetch Snapshot
    print(f"  > Fetching Market Snapshot (Multicall)...")
    snapshot = get_bulk_quotes(requests, return_by_index=True)
    results = snapshot.get("results", {}) # Keyed by req_idx
    network_ms = snapshot.get("network_ms", 0)
    
    print(f"  ✅ Snapshot received in {network_ms:.0f}ms.")
    
    # 3. Update Price Cache
    update_price_cache(results, requests)
    
    # 4. Separate Results by Tier and Build Graphs
    # graphs[tier_value][tokenIn][tokenOut] = data
    tier_graphs = defaultdict(lambda: defaultdict(dict))
    
    for req_idx, quote in results.items():
        req = requests[req_idx]
        tier = req['tier']
        t_in = req['tokenInSymbol']
        t_out = req['tokenOutSymbol']
        
        amount_out_raw = quote['amountOut']
        dec_out = TOKEN_DECIMALS.get(t_out, 18)
        readable_out = amount_out_raw / (10**dec_out)
        
        rate = readable_out / req['amountReadable']
        
        tier_graphs[tier][t_in][t_out] = {
            "rate": rate,
            "fee": quote.get('fee', 3000),
            "dex": quote.get('dex', 'Unknown'),
            "strategy": quote.get('strategy', 'Unknown')
        }
        
    # 5. Analyze Each Tier
    all_opps = []
    best_by_tier = {}
    
    for tier in TIERS:
        opps = analyze_graph_for_tier(tier_graphs[tier], tier, pool_info_map)
        opps.sort(key=lambda x: x['net_profit_usd'], reverse=True)
        if opps:
            best_by_tier[tier] = opps[0]
        else:
            best_by_tier[tier] = None
            
        all_opps.extend(opps)
        
    all_opps.sort(key=lambda x: x['net_profit_usd'], reverse=True)
    
    best_opp = all_opps[0] if all_opps else None

    simulated_comparison = None
    if best_opp:
        # Simulate "Competitor DEX"
        spread = random.uniform(-0.5, 0.5)
        competitor_profit = best_opp['profit_pct'] + spread
        simulated_comparison = {
            "dex_a": "Uniswap V3 (Monad)",
            "dex_b": "Simulated DEX B",
            "profit_a": best_opp['profit_pct'],
            "profit_b": competitor_profit,
            "spread": abs(spread),
            "winner": "Uniswap V3" if best_opp['profit_pct'] > competitor_profit else "Simulated DEX B"
        }
        # Note: Comparison is already in logs from analyze_graph_for_tier, no need to append.
    
    total_time = time.time() - start_time
    
    return {
        "total_scanned": len(tokens),
        "count": len(all_opps),
        "tiers_scanned": TIERS,
        "best_by_tier": best_by_tier,
        "best": {
            "token": "WMON",
            "profit_pct": best_opp['profit_pct'] if best_opp else 0,
            "net_profit_usd": best_opp.get('net_profit_usd', 0) if best_opp else 0,
            "logs": best_opp['logs'] if best_opp else [],
            "strategy": best_opp['strategy'] if best_opp else "None",
            "comparison": simulated_comparison
        },
        "ranking": all_opps[:5],
        "total_time": total_time
    }

if __name__ == "__main__":
    res = scan_market()
    print(json.dumps(res, indent=2))
