
import json
from arbitrage_engine import scan_market

# WMON and moncock addresses from discovery
WMON_ADDR = "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A"
MONCOCK_ADDR = "0x3d0322302F3A374c4E968a3563964d3F893a7433"

override_tokens = {
    "WMON": WMON_ADDR,
    "moncock": MONCOCK_ADDR
}

override_decimals = {
    "WMON": 18,
    "moncock": 18
}

print(f"🧪 Testing Arbitrage for WMON <-> moncock")
print(f"WMON: {WMON_ADDR}")
print(f"moncock: {MONCOCK_ADDR}")

result = scan_market(override_tokens, override_decimals)

print("\n📊 Scan Result Summary:")
print(f"Total Scanned: {result.get('total_scanned')}")
print(f"Opportunities Found: {result.get('count')}")

if result.get('count') > 0:
    print("\n✅ Top Opportunity Logs:")
    for log in result['ranking'][0]['logs']:
        print(f"  {log}")
else:
    print("\n❌ No opportunities found.")
    
print("\n🔍 Raw Best Result (full dump):")
print(json.dumps(result, indent=2, default=str))
