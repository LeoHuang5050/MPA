import asyncio
import json
import datetime
from web3 import AsyncWeb3, WebSocketProvider

# Monad Testnet
WSS_URL = "wss://rpc.monad.xyz"
# Uniswap V2 Swap Topic
SWAP_TOPIC_V2 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"

async def monitor_v2():
    print(f"[{datetime.datetime.now()}] 🧪 V2 Monitor Starting on {WSS_URL}...")
    
    async with AsyncWeb3(WebSocketProvider(WSS_URL)) as w3:
        if await w3.is_connected():
             print(f"[{datetime.datetime.now()}] ✅ Connected to Monad Testnet!")
        else:
             print(f"[{datetime.datetime.now()}] ❌ Failed to connect.")
             return

        try:
            # Subscribe to V2 Topic
            subscription_id = await w3.eth.subscribe("logs", {"topics": [SWAP_TOPIC_V2]})
            print(f"[{datetime.datetime.now()}] 📡 Listening for Uniswap V2 Swaps ({SWAP_TOPIC_V2})...")

            async for log in w3.socket.process_subscriptions():
                try:
                    real_log = log.get('result', log)
                    tx_hash = real_log.get('transactionHash', '').hex()
                    address = real_log.get('address', '')
                    
                    print(f"[{datetime.datetime.now()}] 🚨 V2 EVENT DETECTED!")
                    print(f"   Contract: {address}")
                    print(f"   Tx Hash: {tx_hash}")
                    print(f"   Log: {real_log}")
                    print("-" * 40)
                    
                except Exception as e:
                    print(f"Log Parsing Error: {e}")
                    
        except Exception as e:
            print(f"Connection/Subscription Error: {e}")

def main():
    try:
        asyncio.run(monitor_v2())
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")

if __name__ == "__main__":
    main()
