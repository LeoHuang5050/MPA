
from arbitrage_engine import scan_market, TOKEN_MAP, TOKEN_DECIMALS
import json

print("\n🧪 Testing Kuru-First Scan Logic...")
print(f"Loaded {len(TOKEN_MAP)} tokens from map.")

# Print CHOG addr to verify load
if "CHOG" in TOKEN_MAP:
    print(f"✅ CHOG Address: {TOKEN_MAP['CHOG']}")
else:
    print("❌ CHOG not in TOKEN_MAP!")

# Run Scan (Mock or minimal)
# We just want to see the "Generated X requests" output from scan_market
# But scan_market calls get_bulk_quotes which does networking.
# We can mock get_bulk_quotes or just let it run (it might fail if node is slow but we want to see logs).

print("\n🚀 Starting Scan...")
results = scan_market()

print("\n📊 Scan Results Summary:")
if results:
    ranking = results.get('ranking', [])
    print(f"Found {len(ranking)} opportunities.")
    for opp in ranking:
        print(f"  > {opp['token_pair']} Profit: ${opp['net_profit_usd']:.4f} ({opp['strategy']})")
else:
    print("No results returned.")
