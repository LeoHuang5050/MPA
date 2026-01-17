from web3 import Web3
import json

# Monad Mainnet RPC
RPC_URL = "https://rpc.monad.xyz"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Known Kuru Market: WMON/USDC
# From web3_pricing.py: "0x065C9d28E428A0db40191a54d33d5b7c71a9C394"
MARKET_ADDR = "0x065C9d28E428A0db40191a54d33d5b7c71a9C394"

def find_events():
    print(f"Connecting to {RPC_URL}...")
    if not w3.is_connected():
        print("Failed to connect.")
        return

    latest = w3.eth.block_number
    # Scan last 20 blocks (Monad RPC strict limits)
    start_block = latest - 20
    
    print(f"Scanning logs for {MARKET_ADDR} from {start_block} to {latest}...")
    
    try:
        logs = w3.eth.get_logs({
            "fromBlock": start_block,
            "toBlock": latest,
            "address": MARKET_ADDR
        })
        
        print(f"Found {len(logs)} logs.")
        
        signatures = {}
        
        for log in logs:
            topics = log['topics']
            if not topics: continue
            
            sig = topics[0].hex()
            if sig not in signatures:
                signatures[sig] = {
                    "count": 0,
                    "example_log": log
                }
            signatures[sig]['count'] += 1
            
        print("\n--- Event Signatures Found ---")
        for sig, data in signatures.items():
            print(f"Topic0: {sig} (Count: {data['count']})")
            log = data['example_log']
            data_hex = log['data']
            
            print(f"   Data Length: {len(data_hex)}")
            print(f"   Topics: {[t.hex() for t in log['topics']]}")
            print(f"   Tx: {log['transactionHash'].hex()}")
            
            # Attempt to decode as generic 32-byte words
            try:
                # Convert bytes/HexBytes to hex string
                if hasattr(data_hex, 'hex'):
                    content = data_hex.hex()
                elif isinstance(data_hex, bytes):
                    content = data_hex.hex()
                else: 
                    content = data_hex # Assume string
                
                # Remove 0x if present
                if content.startswith('0x'): content = content[2:]
                
                # Split into 32-byte chunks (64 hex chars)
                chunks = [content[i:i+64] for i in range(0, len(content), 64)]
                print("   Decoded Chunks (Int):")
                for i, c in enumerate(chunks):
                    if len(c) == 64:
                        val = int(c, 16)
                        # Detect potential addresses (heuristic)
                        is_addr = val > 0 and len(hex(val)) == 42 # 0x + 40 chars
                        print(f"    [{i}] {val} (Addr? {is_addr}) (e.g. {val/1e18:.4f})")
                    else:
                        print(f"    [{i}] Raw: {c}")
            except Exception as e:
                print(f"   Decode Error: {e}")
            print("")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_events()
