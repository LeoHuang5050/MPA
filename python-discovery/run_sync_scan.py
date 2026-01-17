import time
from arbitrage_engine import scan_market
import json

def main():
    print("🚀 Starting Sync (Threaded) Arbitrage Scanner...")
    start_time = time.time()
    
    # Run the market scan
    result = scan_market()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n✅ Scan Completed in {total_time:.4f} seconds")
    print(f"Total Tokens Scanned: {result['total_scanned']}")
    print(f"Opportunities Found: {result['count']}")
    
    print(f"\n📊 Best Opportunities per Tier:")
    for tier, opp in result.get('best_by_tier', {}).items():
        if opp:
             print(f"  Tier ${tier:<3}: {opp['profit_pct']:>8.4f}%  ({opp['strategy']})")
        else:
             print(f"  Tier ${tier:<3}: No opportunities found")

    if result['best']:
        print(f"\n🏆 Overall Best: {result['best']['token']} ({result['best']['profit_pct']:.4f}%)")
        print(f"Strategy: {result['best']['strategy']}")
        print("\nLogs for Best:")
        for log in result['best']['logs']:
            print(log)
    else:
        print("\nNo profitable opportunities found.")

if __name__ == "__main__":
    main()
