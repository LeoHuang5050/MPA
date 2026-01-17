
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from web3_pricing import KURU_MARKETS, WMON_ADDR, USDC_ADDR, w3
from arbitrage_engine import TOKEN_MAP

# ERC20 ABI
ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

print("Checking Kuru Market Balances...")

# Check MON/USDC Market specifically
# Kuru UI says ~$82k
# Market Addr: 0x065C9d28E428A0db40191a54d33d5b7c71a9C394 (from check_kuru_markets output)
# Tokens: WMON, USDC

TARGET_MARKET = "0x065C9d28E428A0db40191a54d33d5b7c71a9C394"
MARKET_CHECKSUM = w3.to_checksum_address(TARGET_MARKET)

wmon_contract = w3.eth.contract(address=w3.to_checksum_address(WMON_ADDR), abi=ABI)
usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_ADDR), abi=ABI)

try:
    bal_wmon = wmon_contract.functions.balanceOf(MARKET_CHECKSUM).call() / 1e18
    bal_usdc = usdc_contract.functions.balanceOf(MARKET_CHECKSUM).call() / 1e6
    
    print(f"\nMarket: {TARGET_MARKET} (MON/USDC)")
    print(f"WMON Balance: {bal_wmon:,.2f}")
    print(f"USDC Balance: {bal_usdc:,.2f}")
    
    # Approx Value (assuming MON=$0.40 user showed?? or check cache)
    # Actually wait. User didn't show MON price.
    # But usually WMON ~ USDC value in a balanced pool?
    # Kuru UI: $82k.
    # Total Value = (Bal WMON * P) + Bal USDC.
    print(f"Sum (assuming WMON=$0.50): ${(bal_wmon * 0.50) + bal_usdc:,.2f}")
    
except Exception as e:
    print(f"Error: {e}")

# Check AUSD/USDC (0x699abc15308156e9a3ab89ec7387e9cfe1c86a3b)
# Kuru UI: $258K
MARKET_AUSD = w3.to_checksum_address("0x699abc15308156e9a3ab89ec7387e9cfe1c86a3b")
AUSD_ADDR = "0x00000000efe302beaa2b3e6e1b18d08d69a9012a"
ausd_contract = w3.eth.contract(address=w3.to_checksum_address(AUSD_ADDR), abi=ABI)

try:
    bal_ausd = ausd_contract.functions.balanceOf(MARKET_AUSD).call() / 1e6
    bal_usdc_2 = usdc_contract.functions.balanceOf(MARKET_AUSD).call() / 1e6
    
    print(f"\nMarket: {MARKET_AUSD} (AUSD/USDC)")
    print(f"AUSD Balance: {bal_ausd:,.2f}")
    print(f"USDC Balance: {bal_usdc_2:,.2f}")
    print(f"Total: ${bal_ausd + bal_usdc_2:,.2f}")

except Exception as e:
    print(f"Error: {e}")
