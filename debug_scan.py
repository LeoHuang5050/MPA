import sys
import os
import json

# Add python-discovery to path
sys.path.append(os.path.join(os.getcwd(), 'python-discovery'))

from arbitrage_engine import scan_market

print("Running scan_market...")
result = scan_market()
print("Scan complete.")

with open('debug_scan_output.json', 'w') as f:
    json.dump(result, f, indent=2)

print("Output saved to debug_scan_output.json")
