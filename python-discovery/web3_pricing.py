from web3 import Web3
import json
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# RPC Configuration
# RPC Configuration
# Toggle this to False when deploying to production
USE_LOCAL_FORK = True 

if USE_LOCAL_FORK:
    RPC_URL = "http://127.0.0.1:8545"
else:
    RPC_URL = "https://rpc.monad.xyz"

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 10}))

if USE_LOCAL_FORK:
    # Mock Environment (from deployedContracts.ts)
    UNISWAP_V3_QUOTER_ADDRESS = w3.to_checksum_address("0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512") # MockDEX
    USDC_ADDR = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
    WMON_ADDR = "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
    print(f"🔌 Connected to Local Fork: {RPC_URL}")
    print(f"🛠️ Using Mock Environment: Quoter={UNISWAP_V3_QUOTER_ADDRESS}, USDC={USDC_ADDR}")
else:
    UNISWAP_V3_QUOTER_ADDRESS = w3.to_checksum_address("0x661E93cca42AfacB172121EF892830cA3b70F08d") # Mainnet Quoter
    USDC_ADDR = "0x754704Bc059F8C67012fEd69BC8A327a5aafb603"
    WMON_ADDR = "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
    print(f"🌍 Connected to Monad Mainnet: {RPC_URL}")

# Other Contract Addresses
AMBIENT_QUERY_ADDRESS = w3.to_checksum_address("0xCA00926b6190c2C59336E73F02569c356d7B6b56")
PANCAKESWAP_V3_QUOTER_ADDRESS = w3.to_checksum_address("0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997") 

# Common Constants
CHOG_ADDR = "0x350035555e10d9afaf1566aaebfced5ba6c27777"
PINKY_ADDR = "0x619c9fbdbc94ac3e627ef7e098e3c2a8fb28899e"
AUSD_ADDR = "0x00000000efe302beaa2b3e6e1b18d08d69a9012a" 
SHMON_ADDR = "0x1b68626dca36c7fe922fd2d55e4f631d962de19c"

KURU_MARKETS = {
    # Key format: frozenset({addrA, addrB}) -> MarketAddr
    # WMON/USDC
    frozenset([WMON_ADDR, USDC_ADDR]): "0x065C9d28E428A0db40191a54d33d5b7c71a9C394",
    # CHOG/MON
    frozenset([CHOG_ADDR, WMON_ADDR]): "0x5e5166f02b8f91ab80833270435172078f4178ca",
    # PINKY/MON
    frozenset([PINKY_ADDR, WMON_ADDR]): "0x48958d58941d2436c7c973b064a3be9e581797f4",
    # AUSD/USDC
    frozenset([AUSD_ADDR, USDC_ADDR]): "0x699abc15308156e9a3ab89ec7387e9cfe1c86a3b",
    # MON/AUSD
    frozenset([WMON_ADDR, AUSD_ADDR]): "0x131a2e70a5b31a517a74b8c567149bc294470da9",
    # shMON/MON
    frozenset([SHMON_ADDR, WMON_ADDR]): "0xcc46a703345a18c4ef4be20a447dc8613f0aebc4"
}

# AMBIENT/PANCAKE Disabler: Monad Mainnet only uses Uniswap V3 for now
DISABLE_OTHER_DEXS = False

# ABIs
QUOTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IQuoterV2.QuoteExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
            {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
            {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

AMBIENT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "base", "type": "address"},
            {"internalType": "address", "name": "quote", "type": "address"},
            {"internalType": "uint256", "name": "poolIdx", "type": "uint256"}
        ],
        "name": "queryPrice",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "base", "type": "address"},
            {"internalType": "address", "name": "quote", "type": "address"},
            {"internalType": "uint256", "name": "poolIdx", "type": "uint256"}
        ],
        "name": "queryLiquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    }
]


KURU_ABI = [
    {
        "inputs": [],
        "name": "bestBidAsk",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Initialize Contracts
uniswap_quoter = w3.eth.contract(address=UNISWAP_V3_QUOTER_ADDRESS, abi=QUOTER_ABI)
pancake_quoter = w3.eth.contract(address=PANCAKESWAP_V3_QUOTER_ADDRESS, abi=QUOTER_ABI)
ambient_query = w3.eth.contract(address=AMBIENT_QUERY_ADDRESS, abi=AMBIENT_ABI)

def get_kuru_quote(token_in, token_out, amount_in, decimals_in, decimals_out):
    """
    Fetch Kuru price using bestBidAsk.
    """
    print(f"DEBUG: Entering get_kuru_quote In={token_in} Out={token_out}")
    try:
        # Resolve Market
        # Normalize to lower for map lookup
        t_in_lower = token_in.lower()
        t_out_lower = token_out.lower()
        
        # Determine Market Address
        market_addr = None
        target_pair = frozenset([t_in_lower, t_out_lower])
        
        for k, v in KURU_MARKETS.items():
             # Convert key elements to lower
             k_lower = frozenset([x.lower() for x in k])
             if k_lower == target_pair:
                 market_addr = v
                 break
        
        if not market_addr: 
            # print("DEBUG: Kuru Market Addr Lookup Failed")
            return 0
        
        # Use the local w3 instance (Fork) for Kuru quotes
        market_contract = w3.eth.contract(address=w3.to_checksum_address(market_addr), abi=KURU_ABI)
        
        print(f"DEBUG: Calling bestBidAsk for {market_addr}...")
        t_start = time.time()
        res = market_contract.functions.bestBidAsk().call()
        print(f"DEBUG: bestBidAsk took {time.time() - t_start:.4f}s")
        bid_raw, ask_raw = res # bid (MM buys), ask (MM sells)
        print(f"DEBUG: Kuru Market={market_addr} Bid={bid_raw} Ask={ask_raw}")
        # print(f"DEBUG: In={t_in_lower} Out={t_out_lower} IsInBase={is_token_in_base} Key={target_pair}")
        
        # Determine Base/Quote Assumption
        # WMON/USDC -> WMON is BASE.
        # CHOG/MON -> CHOG is BASE.
        # AUSD/USDC -> AUSD is BASE.
        # shMON/MON -> shMON is BASE.
        
        # Known Quote Tokens (usually Numeraire)
        # If one is Quote, other is Base.
        # Hierarchy: USDC > MON > Others
        
        USDC_LOWER = USDC_ADDR.lower()
        WMON_LOWER = WMON_ADDR.lower() # MON
        
        is_token_in_base = False
        
        # Logic:
        # 1. If pair involves USDC, USDC is Quote.
        # 2. If pair involves MON (and not USDC), MON is Quote.
        
        if USDC_LOWER in target_pair:
            # USDC is Quote. The other is Base.
            # If input is NOT USDC, then input is Base.
            if t_in_lower != USDC_LOWER: is_token_in_base = True
            
        elif WMON_LOWER in target_pair:
            # MON is Quote.
            if t_in_lower != WMON_LOWER: is_token_in_base = True
            
        # Specific overrides if needed (e.g. Stable pairs)
        
        if is_token_in_base:
            # Selling Base -> User hits Bid
            if bid_raw == 0: return 0
            
            # price = bid / 1e18
            # amount_out = amount_in * price
            price_factor = bid_raw / 10**18
            
            # Adjustment for decimals:
            # Price is typically "Quote per Base" scaled by 1e18
            # Out = In * Price
            # Raw Out = (Raw In / 10^InDec) * (Price) * 10^OutDec
            # Raw Out = Raw In * (bid/1e18) * 10^(OutDec - InDec)
            
            factor = 10**(decimals_out - decimals_in)
            amount_out = amount_in * price_factor * factor
            return int(amount_out)
            
        else:
            # Buying Base -> User hits Ask
            # Input is Quote. Output is Base.
            if ask_raw == 0: return 0
            
            # price = ask / 1e18
            # Out = In / price
            price_factor = ask_raw / 10**18
            
            factor = 10**(decimals_out - decimals_in)
            amount_out = (amount_in / price_factor) * factor
            return int(amount_out)

    except Exception as e:
        print(f"Kuru Error: {e}")
        import traceback
        traceback.print_exc()
        return 0




def get_uniswap_v3_price(token_in, token_out, amount_in, fee):
    try:
        # Monad Testnet Quoter might behave same as Mainnet V2
        # Function: quoteExactInputSingle(params)
        params = {
            "tokenIn": w3.to_checksum_address(token_in),
            "tokenOut": w3.to_checksum_address(token_out),
            "amountIn": int(amount_in),
            "fee": fee,
            "sqrtPriceLimitX96": 0
        }
        
        try:
            # Sync call
            quote = uniswap_quoter.functions.quoteExactInputSingle(params).call()
            amount_out = quote[0]
            gas_estimate = quote[3]
            return amount_out, gas_estimate
        except Exception:
            # traceback.print_exc()
            return 0, 0
            
    except Exception as e:
        # print(f"Uniswap V3 Error (Fee {fee}): {e}")
        return 0, 0

def get_pancakeswap_v3_price(token_in, token_out, amount_in, fee=500): 
    return 0, 0 # Disabled for Monad Testnet

def get_ambient_price(base, quote, amount_in):
    return 0, 0 # Disabled for Monad Testnet

# Multicall3 Address (Standard on most EVM chains)
MULTICALL3_ADDRESS = w3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")

MULTICALL3_ABI = [
    {
        "inputs": [
            {"internalType": "bool", "name": "requireSuccess", "type": "bool"},
            {
                "components": [
                    {"internalType": "address", "name": "target", "type": "address"},
                    {"internalType": "bytes", "name": "callData", "type": "bytes"}
                ],
                "internalType": "struct Multicall3.Call[]",
                "name": "calls",
                "type": "tuple[]"
            }
        ],
        "name": "tryAggregate",
        "outputs": [
            {
                "components": [
                    {"internalType": "bool", "name": "success", "type": "bool"},
                    {"internalType": "bytes", "name": "returnData", "type": "bytes"}
                ],
                "internalType": "struct Multicall3.Result[]",
                "name": "returnData",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Uniswap V3 Factory
UNISWAP_V3_FACTORY_ADDRESS = w3.to_checksum_address("0x204faca1764b154221e35c0d20abb3c525710498")

FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "uint24", "name": "", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

POOL_ABI = [
    {
        "input": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

uniswap_factory = w3.eth.contract(address=UNISWAP_V3_FACTORY_ADDRESS, abi=FACTORY_ABI)

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

# --- TOKEN CACHE LOADING ---
TOKEN_CACHE = {}
MAINNET_RPC_URL_FALLBACK = "https://rpc.monad.xyz" # Fallback for metadata
mainnet_w3 = Web3(Web3.HTTPProvider(MAINNET_RPC_URL_FALLBACK, request_kwargs={'timeout': 5}))

def load_token_cache():
    try:
        import os
        base_path = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_path, "monad_tokens.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                for t in data.get('tokens', []):
                    # Store by lower-case address for robust lookup
                    TOKEN_CACHE[t['address'].lower()] = {
                        "symbol": t['symbol'],
                        "decimals": t['decimals']
                    }
            print(f"✅ Loaded {len(TOKEN_CACHE)} tokens from local JSON cache.")
        else:
            print("⚠️ monad_tokens.json not found, using RPC only.")
    except Exception as e:
        print(f"⚠️ Failed to load token cache: {e}")

# Load immediately on import
load_token_cache()

def get_token_metadata(token_address):
    # 1. Check Local Cache First (Fast & Reliable)
    addr_lower = token_address.lower()
    if addr_lower in TOKEN_CACHE:
        return TOKEN_CACHE[addr_lower]

    contract_address = w3.to_checksum_address(token_address)

    # 2. Try Primary RPC (Local Fork)
    try:
        token_contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)
        symbol = token_contract.functions.symbol().call()
        decimals = token_contract.functions.decimals().call()
        
        # Cache it
        TOKEN_CACHE[addr_lower] = {"symbol": symbol, "decimals": decimals}
        return {"symbol": symbol, "decimals": decimals}
    except Exception:
        # 3. Fallback: Try Mainnet RPC (for new tokens not in fork)
        try:
            # print(f"⚠️ Local lookup failed for {token_address}, trying Mainnet...")
            token_contract_main = mainnet_w3.eth.contract(address=contract_address, abi=ERC20_ABI)
            symbol = token_contract_main.functions.symbol().call()
            decimals = token_contract_main.functions.decimals().call()
            
            # Cache it
            TOKEN_CACHE[addr_lower] = {"symbol": symbol, "decimals": decimals}
            return {"symbol": symbol, "decimals": decimals}
        except Exception:
            return {"symbol": "UNK", "decimals": 18}

def get_token_balance(token_address, owner_address):
    try:
        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        balance = token_contract.functions.balanceOf(w3.to_checksum_address(owner_address)).call()
        decimals = token_contract.functions.decimals().call()
        return balance / (10 ** decimals)
    except Exception as e:
        # print(f"Error fetching balance: {e}")
        return 0.0

def get_pool_info(token_in, token_out, fee):
    """
    Fetches Pool Address, Liquidity, and Slot0 (Price) for a pair.
    """
    try:
        t_in = w3.to_checksum_address(token_in)
        t_out = w3.to_checksum_address(token_out)
        
        # 1. Get Pool Address
        pool_addr = uniswap_factory.functions.getPool(t_in, t_out, fee).call()
        if pool_addr == "0x0000000000000000000000000000000000000000":
            return None
            
        pool_contract = w3.eth.contract(address=pool_addr, abi=POOL_ABI)
        
        # 2. Get Liquidity & Slot0
        liquidity = pool_contract.functions.liquidity().call()
        slot0 = pool_contract.functions.slot0().call()
        
        return {
            "address": pool_addr,
            "liquidity": liquidity,
            "sqrtPriceX96": slot0[0],
            "tick": slot0[1]
        }
    except Exception as e:
        # print(f"Pool Info Error: {e}")
        return None

multicall_contract = w3.eth.contract(address=MULTICALL3_ADDRESS, abi=MULTICALL3_ABI)

def get_best_quote(token_in_addr, token_out_addr, amount_in):
    """
    Queries all DEXs in a SINGLE batch using Multicall3.
    """
    quotes = []
    
    # Uniswap V3 Fee Tiers
    fee_tiers = [100, 500, 3000, 10000]
    token_in_addr = w3.to_checksum_address(token_in_addr)
    token_out_addr = w3.to_checksum_address(token_out_addr)
    
    # Construct Batch Calls
    calls = []
    for fee in fee_tiers:
        params = {
            "tokenIn": token_in_addr,
            "tokenOut": token_out_addr,
            "amountIn": int(amount_in),
            "fee": fee,
            "sqrtPriceLimitX96": 0
        }
        # Encode the call data manually for Multicall
        # Use build_transaction to get the data payload
        tx = uniswap_quoter.functions.quoteExactInputSingle(params).build_transaction({'gas': 0, 'gasPrice': 0})
        call_data = tx['data']
        calls.append({
            "target": UNISWAP_V3_QUOTER_ADDRESS,
            "callData": call_data
        })
    
    t0_net = time.perf_counter()
    
    print(f"DEBUG: Executing Uni V3 Multicall for {len(calls)} calls...")
    t_start = time.time()
    try:
        # Execute Batch (1 RPC Request)
        results = multicall_contract.functions.tryAggregate(False, calls).call()
        print(f"DEBUG: Multicall took {time.time() - t_start:.4f}s")
    except Exception as e:
        print(f"Multicall failed after {time.time() - t_start:.4f}s: {e}")
        t1_net = time.perf_counter()
        return {"best": None, "all_quotes": [], "network_ms": (t1_net - t0_net) * 1000}

    t1_net = time.perf_counter()
    network_duration = (t1_net - t0_net) * 1000 # ms
    
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # Decode Results
    for i, (success, return_data) in enumerate(results):
        fee = fee_tiers[i]
        # print(f"DEBUG: Fee {fee} Success: {success} Len: {len(return_data)} Data: {return_data.hex()}")
        
        if success and len(return_data) > 0:
            try:
                # Decode: amountOut, sqrtPriceX96After, initializedTicksCrossed, gasEstimate
                from eth_abi import decode
                decoded_data = decode(
                    ['uint256', 'uint160', 'uint32', 'uint256'],
                    return_data
                )
                amount_out = decoded_data[0]
                gas_estimate = decoded_data[3]
                # print(f"DEBUG: Fee {fee} Decoded amountOut: {amount_out}")
                
                if amount_out > 0:
                    quotes.append({
                        "dex": "Uniswap V3",
                        "fee": fee,
                        "amountOut": amount_out,
                        "gasEstimate": gas_estimate,
                        "timestamp": now # Atomically consistent timestamp
                    })
            except Exception as e:
                # print(f"DEBUG: Decode failed for {fee}: {e}")
                pass # Decoding failed, likely pool revert string

    # --- ADDED: Kuru Quote Check ---
    try:
        # Check if pair is in Kuru (check all permutations or relies on get_kuru_quote logic)
        # get_kuru_quote handles the map check internally.
        
        # Need decimals for Kuru calculation
        from web3_pricing import get_token_metadata # Import internally if needed, or rely on module scope
        
        meta_in = get_token_metadata(token_in_addr)
        meta_out = get_token_metadata(token_out_addr)
        
        dec_in = meta_in.get('decimals', 18)
        dec_out = meta_out.get('decimals', 18)
        
        kuru_out = get_kuru_quote(token_in_addr, token_out_addr, int(amount_in), dec_in, dec_out)
        
        if kuru_out > 0:
            quotes.append({
                "dex": "Kuru",
                "fee": 0, # Orderbook
                "amountOut": kuru_out,  
                "gasEstimate": 150000, # Approx gas for Kuru Swap
                "timestamp": now
            })
            print(f"✅ Found Kuru Quote: {kuru_out}")

    except Exception as e:
        print(f"Kuru Single Quote Error: {e}")

                
    if not quotes:
        return {"best": None, "all_quotes": [], "network_ms": network_duration}
        
    # Sort by amountOut descending
    sorted_quotes = sorted(quotes, key=lambda x: x['amountOut'], reverse=True)
    best = sorted_quotes[0]
    
    return {
        "best": best,
        "all_quotes": sorted_quotes,
        "network_ms": network_duration
    }



# ----------------------------------------------------------------------------------
# BULK QUOTING LOGIC (Multicall)
# ----------------------------------------------------------------------------------




# ... (Previous Functions)

def get_bulk_quotes(requests, return_by_index=False):
    """
    Executes a massive batch of pricing queries in a SINGLE Multicall (Parallel Chunks).
    requests: List of dicts: {"tokenIn": address, "tokenOut": address, "amountIn": int}
    return_by_index: If True, returns dict keyed by request index (int). If False, keyed by (tokenIn, tokenOut).
    """
    import concurrent.futures
    
    fee_tiers = [100, 500, 3000, 10000]
    total_calls = []
    
    # Map raw global call index to metadata: (req_idx, type, pool_idx/fee)
    # Types: "UNI", "AMB"
    call_map = {}
    
    # 1. Build Calldata
    for req_idx, req in enumerate(requests):
        t_in = w3.to_checksum_address(req['tokenIn'])
        t_out = w3.to_checksum_address(req['tokenOut'])
        amt = int(req['amountIn'])
        
        # A. Uniswap V3 Calls
        for fee in fee_tiers:
            try:
                params_tuple = (t_in, t_out, amt, fee, 0)
                call_data = uniswap_quoter.encode_abi("quoteExactInputSingle", args=[params_tuple])
                
                call_idx = len(total_calls)
                total_calls.append({
                    "target": UNISWAP_V3_QUOTER_ADDRESS,
                    "callData": call_data
                })
                call_map[call_idx] = (req_idx, "UNI", fee)
            except Exception as e:
                # print(f"Error encoding UNI tx for req {req_idx}: {e}")
                pass

        # B. Ambient Calls (If enabled)
        if not DISABLE_OTHER_DEXS:
            try:
                # Determine Base/Quote (Sorted by address)
                if int(t_in, 16) < int(t_out, 16):
                    base, quote = t_in, t_out
                    is_buy = True # We are selling Base? No, Base < Quote.
                                # queryPrice returns Price of Base in Quote?
                                # Usually Price = Quote / Base
                else:
                    base, quote = t_out, t_in
                    is_buy = False
                
                # Check Standard Pool Idx (36000, 420)
                for pool_idx in [36000, 420]:
                    # 1. Price Call
                    call_data_price = ambient_query.encode_abi("queryPrice", args=[base, quote, pool_idx])
                    call_idx_p = len(total_calls)
                    total_calls.append({
                        "target": AMBIENT_QUERY_ADDRESS,
                        "callData": call_data_price
                    })
                    call_map[call_idx_p] = (req_idx, "AMB_PRICE", pool_idx)
                    
                    # 2. Liquidity Call
                    call_data_liq = ambient_query.encode_abi("queryLiquidity", args=[base, quote, pool_idx])
                    call_idx_l = len(total_calls)
                    total_calls.append({
                        "target": AMBIENT_QUERY_ADDRESS,
                        "callData": call_data_liq
                    })
                    call_map[call_idx_l] = (req_idx, "AMB_LIQ", pool_idx)
            except Exception as e:
                print(f"Error encoding AMB tx: {e}")

    if not total_calls:
        return {}
    
    # 2. Parallel Chunk Execution
    BATCH_SIZE = 40
    chunks = [total_calls[i:i + BATCH_SIZE] for i in range(0, len(total_calls), BATCH_SIZE)]
    print(f"    (Splitting {len(total_calls)} calls into {len(chunks)} parallel batches...)")
    
    t0 = time.time()
    all_results = [None] * len(total_calls) 
    
    def fetch_chunk(chunk_index, chunk_calls):
        try:
            return multicall_contract.functions.tryAggregate(False, chunk_calls).call()
        except:
            return []

    kuru_futures = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # 1. Submit Multicall Chunks
        future_to_chunk = {
            executor.submit(fetch_chunk, idx, chunk): (idx, chunk) 
            for idx, chunk in enumerate(chunks)
        }
        
        # 2. Submit Kuru Requests (Concurrent)
        if not DISABLE_OTHER_DEXS:
            for req_idx, req in enumerate(requests):
                # Basic check if pair supported to avoid spam
                key = frozenset([req['tokenIn'], req['tokenOut']])
                is_supported = False
                for k in KURU_MARKETS:
                     if req['tokenIn'] in k and req['tokenOut'] in k:
                         is_supported = True
                         break
                
                if is_supported:
                    # Resolve decimals dynamically
                    # Utilize the cache we already have in this file
                    meta_in = get_token_metadata(req['tokenIn'])
                    meta_out = get_token_metadata(req['tokenOut'])
                    
                    dec_in = meta_in.get('decimals', 18)
                    dec_out = meta_out.get('decimals', 18)
                    
                    fut = executor.submit(get_kuru_quote, 
                                          req['tokenIn'], req['tokenOut'], int(req['amountIn']), 
                                          dec_in, dec_out)
                    kuru_futures.append((req_idx, fut))

        # 3. Process Multicall Results
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_idx, _ = future_to_chunk[future]
            chunk_results = future.result()
            
            start_offset = chunk_idx * BATCH_SIZE
            for i, result_data in enumerate(chunk_results):
                if i >= len(chunk_results): continue # Safety
                if start_offset + i < len(all_results):
                    all_results[start_offset + i] = result_data

    t1 = time.time()
    network_ms = (t1 - t0) * 1000
    
    # 3. Decode & Aggregate
    aggregated_results = {} # req_idx -> list of quotes
    temp_amb_results = {} # Store Ambient partials
    
    # Process Kuru Results
    if not DISABLE_OTHER_DEXS and kuru_futures:
        for req_idx, future in kuru_futures:
            try:
                kuru_amt = future.result()
                if kuru_amt > 0:
                     if req_idx not in aggregated_results: aggregated_results[req_idx] = []
                     aggregated_results[req_idx].append({
                         "dex": "Kuru (OrderBook)",
                         "strategy": "Kuru",
                         "fee": 0, # Flat fee? Or maker/taker? Assume 0 for now or integrated in price
                         "amountOut": kuru_amt,
                         "gas": 150000 # Estimate
                     })
            except Exception as e:
                # print(f"Kuru Future Error: {e}")
                pass
    
    from eth_abi import decode
    
    for i, item in enumerate(all_results):
        if not item: continue
        success, return_data = item
        if not success or not return_data: continue
            
        meta = call_map.get(i)
        if not meta: continue
        req_idx, dex_type, param = meta
        
        try:
            # Temp store for Ambient merging (handled in outer scope)


            if dex_type == "UNI":
                decoded = decode(['uint256', 'uint160', 'uint32', 'uint256'], return_data)
                amount_out = decoded[0]
                gas = decoded[3]
                
                if amount_out > 0:
                    if req_idx not in aggregated_results: aggregated_results[req_idx] = []
                    aggregated_results[req_idx].append({
                        "dex": "Uniswap V3",
                        "strategy": f"Uni V3 ({param})",
                        "fee": param,
                        "amountOut": amount_out,
                        "gas": gas
                    })
                    
            elif dex_type == "AMB_PRICE":
                price_q64 = decode(['uint128'], return_data)[0]
                key = (req_idx, param)
                if key not in temp_amb_results: temp_amb_results[key] = {}
                temp_amb_results[key]['price_q64'] = price_q64
                
            elif dex_type == "AMB_LIQ":
                liq = decode(['uint128'], return_data)[0]
                key = (req_idx, param)
                if key not in temp_amb_results: temp_amb_results[key] = {}
                temp_amb_results[key]['liq'] = liq

        except Exception as e:
            pass

    # Process Ambient Merged Results
    for (req_idx, pool_idx), data in temp_amb_results.items():
        price_q64 = data.get('price_q64', 0)
        liq = data.get('liq', 0)
        
        # FILTER: Require Liquidity > 1000
        if price_q64 > 0 and liq > 1000:
             # Ambient returns Q64.64 Price (Raw Ratio)
             price = price_q64 / (2**64)
             
             req = requests[req_idx]
             amt_in = int(req['amountIn'])
             t_in = w3.to_checksum_address(req['tokenIn'])
             t_out = w3.to_checksum_address(req['tokenOut'])
             
             if int(t_in, 16) < int(t_out, 16):
                 amount_out = amt_in * price
             else:
                 amount_out = amt_in / price
             
             if amount_out > 0:
                 if req_idx not in aggregated_results: aggregated_results[req_idx] = []
                 aggregated_results[req_idx].append({
                     "dex": "Ambient",
                     "strategy": f"Ambient ({pool_idx})",
                     "fee": 500,
                     "amountOut": int(amount_out),
                     "gas": 150000 
                 })

            
            
    # 4. Find Best for each Request
    final_output = {}
    for req_idx, quotes in aggregated_results.items():
        req = requests[req_idx]
        
        # Sort by amountOut desc
        sorted_quotes = sorted(quotes, key=lambda x: x['amountOut'], reverse=True)
        best = sorted_quotes[0]
        best['all_quotes'] = sorted_quotes
        
        if return_by_index:
            final_output[req_idx] = best
        else:
            key = (req['tokenIn'], req['tokenOut'])
            final_output[key] = best
        
    return {"results": final_output, "network_ms": network_ms}
