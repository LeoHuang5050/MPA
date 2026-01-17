import time
import json
from arbitrage_engine import scan_all_arbitrage

def monitor_mon():
    runs = 4
    interval = 15
    amount = 100 # Default to 100 MON
    
    results = []
    
    print(f"🚀 Starting MON Arbitrage Monitor")
    print(f"   Target: MON | Amount: {amount}")
    print(f"   Schedule: {runs} runs, every {interval}s")
    print("-" * 60)
    
    for i in range(runs):
        run_id = i + 1
        print(f"🕒 [Run {run_id}/{runs}] Scanning...", end="\r")
        
        start_ts = time.strftime("%H:%M:%S")
        try:
            # Execute Scan
            res = scan_all_arbitrage("MON", amount)
            
            # Extract Data
            strategy = res.get('mode', 'Unknown')
            profit = res.get('profit', 0.0)
            profit_pct = res.get('profit_pct', 0.0)
            
            # Identify Best Path (brief description)
            path_desc = "N/A"
            if res.get('path'):
                # e.g. "MON->USDC->MON"
                tokens = [step['tokenIn'] for step in res['path']]
                tokens.append(res['path'][-1]['tokenOut'])
                path_desc = "->".join(tokens)
            
            results.append({
                "run": run_id,
                "time": start_ts,
                "strategy": strategy,
                "profit": profit,
                "yield": profit_pct,
                "path": path_desc
            })
            
            print(f"✅ [Run {run_id}/{runs}] {start_ts} | {strategy} | PnL: {profit:+.4f} MON ({profit_pct:+.4f}%)")
            
        except Exception as e:
            print(f"❌ [Run {run_id}/{runs}] Error: {e}")
            results.append({
                "run": run_id, 
                "time": start_ts,
                "strategy": "Error",
                "profit": 0, 
                "yield": 0, 
                "path": str(e)
            })
        
        if i < runs - 1:
            time.sleep(interval)
            
    print("-" * 60)
    print("📊 SUMMARY REPORT")
    print(f"{'Run':<4} | {'Time':<8} | {'Strategy':<10} | {'Yield (%)':<10} | {'Profit (MON)':<12} | {'Path'}")
    print("-" * 80)
    
    total_yield = 0
    best_run = None
    
    for r in results:
        print(f"{r['run']:<4} | {r['time']:<8} | {r['strategy']:<10} | {r['yield']:<9.4f}% | {r['profit']:<12.4f} | {r['path']}")
        total_yield += r['yield']
        if best_run is None or r['yield'] > best_run['yield']:
            best_run = r
            
    avg_yield = total_yield / runs
    print("-" * 80)
    print(f"📈 Average Yield: {avg_yield:+.4f}%")
    if best_run:
        print(f"🏆 Best Run: #{best_run['run']} ({best_run['yield']:+.4f}%) via {best_run['path']}")

if __name__ == "__main__":
    monitor_mon()
