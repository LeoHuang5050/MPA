import asyncio
import json
import datetime
from web3 import AsyncWeb3, WebSocketProvider

# Monad Mainnet Configuration
WSS_URL = "wss://rpc.monad.xyz" 
SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"

# Cache for Pool -> {t0_symbol, t1_symbol, t0_dec, t1_dec}
POOL_CACHE = {}

# Minimal ABIs
POOL_ABI = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"}
]
ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]

async def resolve_pool_info(w3, pool_addr):
    if pool_addr in POOL_CACHE: return POOL_CACHE[pool_addr]
    
    try:
        pool_contract = w3.eth.contract(address=pool_addr, abi=POOL_ABI)
        t0_addr = await pool_contract.functions.token0().call()
        t1_addr = await pool_contract.functions.token1().call()
        
        t0_contract = w3.eth.contract(address=t0_addr, abi=ERC20_ABI)
        t1_contract = w3.eth.contract(address=t1_addr, abi=ERC20_ABI)
        
        # Parallel fetch could be better but this is fine for debug
        t0_sym = await t0_contract.functions.symbol().call()
        t0_dec = await t0_contract.functions.decimals().call()
        
        t1_sym = await t1_contract.functions.symbol().call()
        t1_dec = await t1_contract.functions.decimals().call()
        
        info = {
            "t0": t0_sym, "t0_addr": t0_addr, "t0_dec": t0_dec,
            "t1": t1_sym, "t1_addr": t1_addr, "t1_dec": t1_dec
        }
        POOL_CACHE[pool_addr] = info
        return info
    except Exception as e:
        # print(f"Metadata fetch failed: {e}")
        return None

async def debug_monitor():
    print(f"[{datetime.datetime.now()}] 🛡️ SMART MONITOR: Connecting to {WSS_URL}...")
    
    async with AsyncWeb3(WebSocketProvider(WSS_URL)) as w3:
        if await w3.is_connected():
            print(f"[{datetime.datetime.now()}] ✅ Connected to Mainnet!")
        else:
            print(f"[{datetime.datetime.now()}] ❌ Failed to connect.")
            return

        try:
            subscribe_params = {"topics": [SWAP_TOPIC]}
            await w3.eth.subscribe("logs", subscribe_params)
            print(f"[{datetime.datetime.now()}] 📡 Listening... (Resolving Tokens on the fly)")
            
            count = 0
            async for log in w3.socket.process_subscriptions():
                count += 1
                try:
                    real_log = log
                    if 'result' in log:
                        real_log = log['result']
                        
                    pool_addr = real_log.get('address', None)
                    if not pool_addr: continue
                    
                    tx_hash = real_log.get('transactionHash', '')
                    if hasattr(tx_hash, 'hex'): tx_hash = tx_hash.hex()
                    elif isinstance(tx_hash, bytes): tx_hash = tx_hash.hex()
                    else: tx_hash = str(tx_hash)

                    # 1. Decode Log Data
                    from eth_abi import decode
                    raw_data = real_log.get('data', b'')
                    
                    if hasattr(raw_data, 'hex'): data_bytes = bytes(raw_data)
                    elif isinstance(raw_data, str) and raw_data.startswith('0x'): data_bytes = bytes.fromhex(raw_data[2:])
                    elif isinstance(raw_data, str): data_bytes = bytes.fromhex(raw_data)
                    else: data_bytes = raw_data
                        
                    # amount0, amount1 (Signed Integers!)
                    decoded = decode(['int256', 'int256', 'uint160', 'uint128', 'int24'], data_bytes)
                    amount0 = decoded[0]
                    amount1 = decoded[1]
                    
                    # 2. Resolve Metadata
                    pool_info = await resolve_pool_info(w3, pool_addr)
                    
                    if pool_info:
                        t0_sym = pool_info['t0']
                        t1_sym = pool_info['t1']
                        
                        val0 = amount0 / (10**pool_info['t0_dec'])
                        val1 = amount1 / (10**pool_info['t1_dec'])
                        
                        direction_str = ""
                        # Uniswap V3: 
                        # amount0 < 0 => User SOLD t0, sending it INTO contract
                        # amount0 > 0 => User BOUGHT t0, taking it OUT of contract
                        
                        if amount0 < 0:
                            # T0 In, T1 Out => Sell T0 for T1
                            direction_str = f"🔴 SELL {abs(val0):.4f} {t0_sym} -> BUY {abs(val1):.4f} {t1_sym}"
                        else:
                            # T0 Out, T1 In => Buy T0 with T1
                            direction_str = f"🟢 BUY {abs(val0):.4f} {t0_sym} with {abs(val1):.4f} {t1_sym}"
                            
                        print(f"[{count}] {direction_str}")
                        print(f"   Pool: {t0_sym}/{t1_sym} ({pool_addr})")
                    else:
                        print(f"[{count}] 🔁 SWAP (Unknown Pool: {pool_addr})")
                        print(f"   Amt0: {amount0}")
                        print(f"   Amt1: {amount1}")
                        
                    print(f"   Tx:   {tx_hash}\n")

                except Exception as e:
                    print(f"   ⚠️ Error: {e}")
                    
        except Exception as e:
            print(f"Connection error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(debug_monitor())
    except KeyboardInterrupt:
        print("\n🛑 Debug stopped.")
