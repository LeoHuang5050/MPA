import asyncio
import time
from arbitrage_engine import scan_market
import json

async def main():
    print("🚀 Starting Async Arbitrage Scanner...")
    start_time = time.time()
    
    # Run the market scan
    result = await scan_market()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n✅ Scan Completed in {total_time:.4f} seconds")
    print(f"Total Tokens Scanned: {result['total_scanned']}")
    print(f"Opportunities Found: {result['count']}")
    
    if result['best']:
        print(f"\n🏆 Best Opportunity: {result['best']['token']} ({result['best']['profit_pct']:.4f}%)")
        print("\nLogs for Best:")
        for log in result['best']['logs']:
            print(log)
    else:
        print("\nNo profitable opportunities found.")

    # Dump full JSON for debugging
    # print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
