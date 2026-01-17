import asyncio
import json
import datetime
from collections import deque
from web3 import AsyncWeb3, WebSocketProvider
from web3_pricing import get_pool_info, get_token_balance, get_token_metadata

# Monad Mainnet Configuration
WSS_URL = "wss://rpc.monad.xyz" 
SWAP_TOPIC_V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
SWAP_TOPIC_V2 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
KURU_TOPIC = "0xd9c089818ef223629c2af53488dc47cf2867f157caca778ce77aaa742b8c1079" # Likely OrderMatches

# Minimal Pool ABI for on-the-fly resolution (Uniswap)
POOL_ABI_V3 = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"fee","outputs":[{"name":"","type":"uint24"}],"type":"function"}
]

POOL_ABI_V2 = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint112"},{"name":"_reserve1","type":"uint112"},{"name":"_blockTimestampLast","type":"uint32"}],"type":"function"}
]

# Cache dynamically found pools
KNOWN_POOLS = {}

async def resolve_and_cache_pool(w3, pool_addr):
    """
    Dynamically resolves pool tokens, calculates TVL, sets threshold, and caches it.
    """
    if pool_addr in KNOWN_POOLS: return KNOWN_POOLS[pool_addr]
    
    # Check Kuru Markets First
    from web3_pricing import KURU_MARKETS, get_token_metadata, get_token_balance
    
    dex_source = "Uniswap V3" # Default
    fee_pct = 0.3
    pool_data = None
    
    # Check if this address is a known Kuru Market
    is_kuru = False
    kuru_pair = None
    
    for pair, mkt_addr in KURU_MARKETS.items():
        if mkt_addr.lower() == pool_addr.lower():
            is_kuru = True
            kuru_pair = list(pair)
            dex_source = "Kuru"
            fee_pct = 0.0 # Orderbook
            break
            
    if is_kuru and kuru_pair:
        t0_addr = kuru_pair[0]
        t1_addr = kuru_pair[1]
        
        # Metadata
        meta0 = get_token_metadata(t0_addr)
        meta1 = get_token_metadata(t1_addr)
        
        # TVL - Assume fetch via API separately or estimate?
        # For Log resolution, we just need basic info.
        tvl = 0
        threshold = 50 # Default
        
        pool_data = {
            "name": f"{meta0['symbol']}/{meta1['symbol']} (Kuru)",
            "t0_addr": t0_addr,
            "t1_addr": t1_addr,
            "t0_sym": meta0['symbol'],
            "t1_sym": meta1['symbol'],
            "t0_dec": meta0['decimals'],
            "t1_dec": meta1['decimals'],
            "tvl": tvl,
            "threshold": threshold,
            "fee": 0.0,
            "dex": "Kuru"
        }
        KNOWN_POOLS[pool_addr] = pool_data
        print(f"[{datetime.datetime.now()}] 🆕 Resolved Kuru Market {pool_data['name']}")
        return pool_data

    # Uniswap Resolution (Existing Logic)
    try:
        # Optimistic: Try V3 first
        pool_contract = w3.eth.contract(address=pool_addr, abi=POOL_ABI_V3)
        
        try:
            t0_addr = await pool_contract.functions.token0().call()
            t1_addr = await pool_contract.functions.token1().call()
            fee = await pool_contract.functions.fee().call()
            fee_pct = fee / 10000.0
        except:
            # Fallback to V2
            dex_source = "Uniswap V2"
            pool_contract = w3.eth.contract(address=pool_addr, abi=POOL_ABI_V2)
            t0_addr = await pool_contract.functions.token0().call()
            t1_addr = await pool_contract.functions.token1().call()
            fee_pct = 0.3
        
        meta0 = get_token_metadata(t0_addr)
        meta1 = get_token_metadata(t1_addr)
        
        bal0 = get_token_balance(t0_addr, pool_addr)
        bal1 = get_token_balance(t1_addr, pool_addr)
        
        tvl = 0
        if "USD" in meta0['symbol']: tvl = bal0 * 2
        elif "USD" in meta1['symbol']: tvl = bal1 * 2
        else: 
            if "MON" in meta0['symbol']: tvl = bal0 * 2 * 0.1
            elif "MON" in meta1['symbol']: tvl = bal1 * 2 * 0.1
            else: tvl = 50000
            
        threshold = tvl * 0.005
        if threshold < 50: threshold = 50
        
        pool_name = f"{meta0['symbol']}/{meta1['symbol']} ({fee_pct}%)"
        
        pool_data = {
            "name": pool_name,
            "t0_addr": t0_addr,
            "t1_addr": t1_addr,
            "t0_sym": meta0['symbol'],
            "t1_sym": meta1['symbol'],
            "t0_dec": meta0['decimals'],
            "t1_dec": meta1['decimals'],
            "tvl": tvl,
            "threshold": threshold,
            "fee": fee_pct,
            "dex": dex_source
        }
        
        KNOWN_POOLS[pool_addr] = pool_data
        print(f"[{datetime.datetime.now()}] 🆕 Discovered {pool_data['name']} on {dex_source} (TVL ${tvl:,.0f})")
        return pool_data
        
    except Exception as e:
        return None

async def monitor_transactions(callback=None):
    print(f"[{datetime.datetime.now()}] 🛡️ Sentinel Starting (Dynamic Discovery Mode)...")
    
    async with AsyncWeb3(WebSocketProvider(WSS_URL)) as w3:
        if await w3.is_connected():
             print(f"[{datetime.datetime.now()}] ✅ Connected to Mainnet!")
        else:
             print(f"[{datetime.datetime.now()}] ❌ Failed to connect.")
             return

        try:
            # Subscribe to V3, V2, and Kuru topics
            await w3.eth.subscribe("logs", {"topics": [[SWAP_TOPIC_V3, SWAP_TOPIC_V2, KURU_TOPIC]]})
            print(f"[{datetime.datetime.now()}] 📡 Listening for Swaps, includes Kuru events...")

            recent_events_local = deque(maxlen=100)

            async for log in w3.socket.process_subscriptions():
                try:
                    real_log = log.get('result', log)
                    topics = real_log.get('topics', [])
                    if not topics: continue

                    # Identify Topic
                    topic0_hex = topics[0].hex().lower() if hasattr(topics[0], 'hex') else str(topics[0]).lower()
                    topic0_clean = topic0_hex.replace('0x', '')
                    
                    is_v3 = topic0_clean == SWAP_TOPIC_V3.lower().replace('0x', '')
                    is_kuru = topic0_clean == KURU_TOPIC.lower().replace('0x', '')
                    
                    pool_addr = real_log.get('address', None)
                    if not pool_addr: continue
                    
                    # 1. Resolve Pool (Dynamic)
                    pool_data = await resolve_and_cache_pool(w3, pool_addr)
                    if not pool_data: continue
                    
                    # 2. Decode Log
                    data_hex = real_log.get('data', '0x')
                    if isinstance(data_hex, str): 
                        if data_hex.startswith('0x'): data_bytes = bytes.fromhex(data_hex[2:])
                        else: data_bytes = bytes.fromhex(data_hex)
                    else: data_bytes = bytes(data_hex)

                    amount_in = 0.0; amount_out = 0.0
                    side = "unknown"; symbol_in = ""; symbol_out = ""
                    t0_dec = pool_data['t0_dec']; t1_dec = pool_data['t1_dec']
                    
                    desc_str = ""
                    
                    if is_kuru:
                        # Kuru Decode: [ID, UserAddr, Price(?), Amount(?), Side]
                        # 5 words = 160 bytes? 
                        # Observed Data length 160 chars = 80 bytes? 
                        # Wait, 80 bytes is 2.5 words. My debug script chunked it into 5 chunks of 64 chars (32 bytes)?
                        # Ah, debug script verified data_hex length.
                        # If data hex is 160 chars => 80 bytes => 2.5 words?
                        # Debug script showed:
                        # [0] 2785058 (1 word)
                        # [1] Addr (1 word)
                        # [2] 2237400
                        # [3] 585...
                        # [4] 1
                        # That is 5 words -> 160 Bytes -> 320 Hex Chars.
                        # My Debug script said "Data Length: 160" (Hex chars? Or Bytes?)
                        # If debug script used `len(data_hex)` on a HexBytes object, it returns *bytes* length.
                        # So `len` = 160 => 160 Bytes => 5 Words. Correct.
                        
                        if len(data_bytes) >= 160:
                            # Parse manually for simplicity
                            # word0 = int.from_bytes(data_bytes[0:32], 'big')
                            word1 = int.from_bytes(data_bytes[32:64], 'big') # Addr
                            word2 = int.from_bytes(data_bytes[64:96], 'big') # Price? (Scaled 1e8)
                            word3 = int.from_bytes(data_bytes[96:128], 'big') # Amount? (Wei)
                            word4 = int.from_bytes(data_bytes[128:160], 'big') # Side?
                            
                            # Heuristic Mapping
                            # Price ~ 2237400 -> 0.022 (WMON/USDC)
                            # Amount ~ 5e14 -> 0.0005 MON
                            
                            # Assumption: Word2 = Price (1e8), Word3 = Amount (Base Token)
                            # Determine Base/Quote Token
                            
                            # Kuru Market: WMON/USDC
                            # Usually Token0 is Base, Token1 Quote? Or vice versa.
                            # Kuru API: WMON/USDC -> Price ~ 0.02 (USDC per WMON).
                            # If WMON is Base (18 dec), USDC Quote (6 dec).
                            # Price Scaled 1e8: 0.02 * 1e8 = 2,000,000. Closely matches 2,237,400.
                            # So Price is indeed scaled 1e8.
                            
                            price_val = word2 / 10**8
                            amount_base_wei = word3
                            amount_base = amount_base_wei / (10**t0_dec) # Assume T0 is Base
                            
                            # Calculate Quote Amount (Value)
                            # Value = AmountBase * Price
                            amount_quote = amount_base * price_val
                            
                            # Determine side
                            # Word4: 1 = BUY? 0 = SELL? (Pure Guess, but let's map 1->Buy)
                            side = "buy" if word4 == 1 else "sell"
                            
                            symbol_in = pool_data['t1_sym'] if side=="buy" else pool_data['t0_sym']
                            symbol_out = pool_data['t0_sym'] if side=="buy" else pool_data['t1_sym']
                            
                            amount_in = amount_quote if side=="buy" else amount_base
                            amount_out = amount_base if side=="buy" else amount_quote
                            
                            desc_str = f"KURU Match: {amount_base:.4f} {pool_data['t0_sym']} @ {price_val:.4f}"

                    elif is_v3:
                        if len(data_bytes) < 64: continue
                        a0 = int.from_bytes(data_bytes[0:32], 'big', signed=True)
                        a1 = int.from_bytes(data_bytes[32:64], 'big', signed=True)
                        
                        if a0 > 0: # Check V3 direction logic carefully. a0>0 means Pool GAINED T0 (User SOLD T0)
                            side = "sell"
                            symbol_in = pool_data['t0_sym']; symbol_out = pool_data['t1_sym']
                            amount_in = float(abs(a0)) / (10**t0_dec); amount_out = float(abs(a1)) / (10**t1_dec)
                        else: # User BOUGHT T0
                            side = "buy"
                            symbol_in = pool_data['t1_sym']; symbol_out = pool_data['t0_sym']
                            amount_in = float(abs(a1)) / (10**t1_dec); amount_out = float(abs(a0)) / (10**t0_dec)
                    else:
                        # V2 Swap (amount0In, amount1In, amount0Out, amount1Out)
                        if len(data_bytes) >= 128:
                            a0_in = int.from_bytes(data_bytes[0:32], 'big')
                            a1_in = int.from_bytes(data_bytes[32:64], 'big')
                            a0_out = int.from_bytes(data_bytes[64:96], 'big')
                            a1_out = int.from_bytes(data_bytes[96:128], 'big')
                            
                            if a0_in > 0: # Sold T0
                                side = "sell"
                                amount0_float_in = float(a0_in) / (10 ** t0_dec)
                                amount1_float_out = float(a1_out) / (10 ** t1_dec)
                                symbol_in = pool_data['t0_sym']; symbol_out = pool_data['t1_sym']
                                amount_in = amount0_float_in; amount_out = amount1_float_out
                            else: # Bought T0
                                side = "buy"
                                amount1_float_in = float(a1_in) / (10 ** t1_dec)
                                amount0_float_out = float(a0_out) / (10 ** t0_dec)
                                symbol_in = pool_data['t1_sym']; symbol_out = pool_data['t0_sym']
                                amount_in = amount1_float_in; amount_out = amount0_float_out
                        else:
                            continue

                    # 3. Value Normalization (Passed to next step)
                        
                    
                    # USD Value approx
                    # RELAXED Mode: Allow "fake" USD tokens for testing/simulation.
                    # UI will handle large numbers with compact formatting (e.g. 1.2B).
                    usd_val = 0.0
                    is_usd_pair = False
                    
                    if "USD" in symbol_in: 
                        usd_val = amount_in
                        is_usd_pair = True
                    elif "USD" in symbol_out: 
                        usd_val = amount_out
                        is_usd_pair = True
                    else: 
                        # Fallback for non-USD pairs:
                        # Use 0.1 weighting for MON to keep thresholding sane.
                        usd_val = amount_out * 0.1 

                    
                    # 4. Threshold Check (Classify only, don't filter)
                    is_whale = usd_val > pool_data['threshold']
                    
                    tx_hash = real_log.get('transactionHash', '')
                    if hasattr(tx_hash, 'hex'): 
                        tx_hash = tx_hash.hex()
                    
                    # Safety: Ensure 0x prefix
                    if not str(tx_hash).startswith("0x"):
                        tx_hash = f"0x{tx_hash}"
                    
                    # Determine honest label
                    if is_usd_pair:
                        display_label = f"${usd_val:,.2f}"
                    else:
                        display_label = f"{amount_out:,.2f} {symbol_out}"

                    event = {
                        "type": "WHALE_SWAP" if is_whale else "SWAP",
                        "pool": pool_data['name'],
                        "side": "buy" if side == "buy" else "sell",
                        "description": desc_str if desc_str else f"{side.upper()} {amount_out:.2f} {symbol_out}",
                        "symbolIn": symbol_in,
                        "symbolOut": symbol_out,
                        "amountIn": amount_in,
                        "amountOut": amount_out,
                        "value": usd_val,
                        "label": display_label,
                        "hash": str(tx_hash),
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                        "dex": pool_data.get('dex', 'Uniswap V3'),
                        "pool_address": pool_addr,
                        "token0": {"symbol": pool_data['t0_sym'], "address": pool_data['t0_addr'], "decimals": pool_data['t0_dec']},
                        "token1": {"symbol": pool_data['t1_sym'], "address": pool_data['t1_addr'], "decimals": pool_data['t1_dec']}
                    }
                    
                    # Add to local history safely
                    recent_events_local.appendleft(event)
                        
                    if callback: callback(event)
                        
                    # Notify console
                    if is_whale:
                        print(f"🐋 {event['description']} ({event['label']}) on {pool_data['name']}")
                    # else:
                    #    print(f"🔹 {event['description']} on {pool_data['name']}")

                except Exception as e:
                    print(f"Error Processing Log: {e}")
                    continue

        except Exception as e:
            print(f"Conn Error: {e}")

def main():
    try:
        asyncio.run(monitor_transactions())
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")

if __name__ == "__main__":
    main()
