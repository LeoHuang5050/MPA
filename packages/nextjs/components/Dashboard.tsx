import { useState, useEffect } from "react";

export default function Dashboard() {
    const [events, setEvents] = useState<any[]>([]);
    const [pools, setPools] = useState<any[]>([]);
    const [arbitrage, setArbitrage] = useState<any>(null);
    const [scanning, setScanning] = useState(false);
    const [expandedIds, setExpandedIds] = useState<number[]>([]); // Track expanded rows for details
    const [searchTerm, setSearchTerm] = useState("");
    const [filterSide, setFilterSide] = useState<'all' | 'buy' | 'sell'>('all');
    const [showAll, setShowAll] = useState(false);

    // Helper for compact numbers
    const formatCompactNumber = (num: number) => {
        if (!num) return '0';
        return Intl.NumberFormat('en-US', {
            notation: "compact",
            maximumFractionDigits: 2
        }).format(num);
    };

    // Data Fetching
    const fetchEvents = async () => {
        try {
            const res = await fetch("http://localhost:5001/events");
            const json = await res.json();
            if (json.success) setEvents(json.data);
        } catch (e) {
            console.error("Error fetching events:", e);
        }
    };

    const fetchPools = async () => {
        try {
            const res = await fetch("http://localhost:5001/pools");
            const json = await res.json();
            if (json.success) setPools(json.data);
        } catch (e) {
            console.error("Error pools:", e);
        }
    };

    // Poll Data
    useEffect(() => {
        fetchEvents();
        fetchPools();

        const interval = setInterval(() => {
            fetchEvents();
            fetchPools();
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    // Poll Arbitrage
    useEffect(() => {
        const fetchArbitrage = async () => {
            setScanning(true);
            try {
                const res = await fetch("http://localhost:5001/find_arbitrage", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ token: "MARKET", mode: "market" })
                });
                const json = await res.json();
                if (json.success) setArbitrage(json.data);
            } catch (e) {
                console.error("Error arbitrage:", e);
            } finally {
                setScanning(false);
            }
        };
        fetchArbitrage();
        const interval = setInterval(fetchArbitrage, 10000);
        return () => clearInterval(interval);
    }, []);

    // Filter Logic
    const filteredEvents = events.filter(e => {
        // 1. Search Text
        const matchesSearch = e.pool.toLowerCase().includes(searchTerm.toLowerCase()) ||
            e.symbolIn.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (e.symbolOut && e.symbolOut.toLowerCase().includes(searchTerm.toLowerCase()));

        // 2. Buy/Sell Side
        const matchesSide = filterSide === 'all' || e.side === filterSide;

        // 3. Whale vs All
        // If showAll is false, ONLY show WHALE_SWAP.
        // If showAll is true, show everything.
        const matchesType = showAll ? true : e.type === 'WHALE_SWAP';

        return matchesSearch && matchesSide && matchesType;
    });

    const filteredPools = pools.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="p-6 max-w-[1600px] mx-auto space-y-6">
            <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-teal-200 to-emerald-400 tracking-tighter drop-shadow-lg">
                MONAD PULSE ARBITRAGE (MPA)
            </h1>

            {/* Status Bar */}
            <div className="flex justify-between items-center bg-gray-900/40 p-3 rounded-xl border border-teal-900/30 backdrop-blur-sm mb-6">
                {/* ... (Search Bar kept same) ... */}
                <div className="relative w-96">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                    <input
                        type="text"
                        className="block w-full pl-10 pr-3 py-2 border border-teal-900/30 rounded-lg leading-5 bg-gray-800/50 text-teal-100 placeholder-gray-500 focus:outline-none focus:bg-gray-900/80 focus:ring-1 focus:ring-teal-500 sm:text-sm transition-all duration-200"
                        placeholder="Filter Token (e.g. APR, WMON)..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* SECTION A: WHALE STREAM */}
                <div className="bg-gray-800/40 rounded-3xl p-6 border border-teal-900/30 shadow-2xl backdrop-blur-xl relative overflow-hidden group hover:border-teal-500/30 transition-all duration-300 h-[600px] flex flex-col">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-teal-500/5 rounded-full blur-3xl -z-10 transition-opacity group-hover:opacity-100 opacity-50"></div>

                    <div className="flex justify-between items-center mb-6">

                        <div className="flex gap-2 items-center">
                            {/* Mode Toggle: Whales vs All */}
                            {/* Mode Toggle: Whales vs All */}
                            <div className="flex items-center bg-gray-900/50 rounded-lg p-0.5 border border-teal-900/30 mr-4">
                                <button
                                    onClick={() => setShowAll(false)}
                                    className={`px-4 py-1 text-xs font-medium rounded-l-md transition-all flex items-center gap-2 ${!showAll
                                        ? 'bg-purple-500/20 text-purple-300 shadow-sm border-r border-teal-900/30'
                                        : 'text-gray-400 hover:text-purple-200 hover:bg-white/5'
                                        }`}
                                >
                                    <span>🐋</span> Whales
                                </button>
                                <div className="w-[1px] h-4 bg-gray-700/50"></div>
                                <button
                                    onClick={() => setShowAll(true)}
                                    className={`px-4 py-1 text-xs font-medium rounded-r-md transition-all flex items-center gap-2 ${showAll
                                        ? 'bg-blue-500/20 text-blue-300 shadow-sm border-l border-teal-900/30'
                                        : 'text-gray-400 hover:text-blue-200 hover:bg-white/5'
                                        }`}
                                >
                                    <span>🌎</span> All
                                </button>
                            </div>

                            <div className="flex bg-gray-900/50 rounded-lg p-1 border border-teal-900/30">
                                <button
                                    onClick={() => setFilterSide('all')}
                                    className={`px-3 py-1 text-xs rounded-md transition-all ${filterSide === 'all' ? 'bg-teal-500/20 text-teal-300 shadow-sm' : 'text-gray-400 hover:text-teal-200'}`}
                                >All</button>
                                <button
                                    onClick={() => setFilterSide('buy')}
                                    className={`px-3 py-1 text-xs rounded-md transition-all ${filterSide === 'buy' ? 'bg-green-500/20 text-green-300 shadow-sm' : 'text-gray-400 hover:text-green-200'}`}
                                >Buy</button>
                                <button
                                    onClick={() => setFilterSide('sell')}
                                    className={`px-3 py-1 text-xs rounded-md transition-all ${filterSide === 'sell' ? 'bg-red-500/20 text-red-300 shadow-sm' : 'text-gray-400 hover:text-red-200'}`}
                                >Sell</button>
                            </div>
                        </div>
                    </div>
                    <div className="card-body p-0 overflow-y-auto no-scrollbar relative bg-gradient-to-b from-transparent to-black/20 flex-1">
                        {filteredEvents.length === 0 ? (
                            <div className="flex items-center justify-center h-full text-gray-500 animate-pulse">
                                {searchTerm ? "No matching whales found." : "Listening for Mainnet Swaps..."}
                            </div>
                        ) : (
                            <div className="flex flex-col gap-3 p-4">
                                {filteredEvents.map((e, i) => (
                                    <div key={i} className={`
                                        flex items-center gap-3 p-3 rounded-xl border-l-4 shadow-lg transform transition-all hover:scale-105 active:scale-95
                                        ${e.side === 'buy' ? 'bg-green-900/10 border-green-500' : 'bg-red-900/10 border-red-500'}
                                    `}>
                                        <div className={`text-2xl ${e.side === 'buy' ? 'animate-bounce' : ''}`}>
                                            {e.side === 'buy' ? '🟢' : '🔴'}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            {/* CLEANER LAYOUT: Merged value into title */}
                                            <div className="flex justify-between items-baseline">
                                                <span className={`font-bold text-lg ${e.side === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                                                    {e.side === 'buy' ? 'BUY' : 'SELL'} {formatCompactNumber(e.amountOut)} {e.symbolOut || e.pool.split('/')[1]}
                                                </span>
                                            </div>

                                            <div className="flex justify-between items-center mt-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="badge badge-xs badge-neutral text-[10px] text-gray-400 border-gray-700">
                                                        {e.dex || 'Uniswap V3'}
                                                    </span>
                                                    <div className="text-xs text-gray-500 font-mono">
                                                        Pool: {e.pool}
                                                    </div>
                                                </div>
                                                <div className="text-xs font-mono text-gray-400">
                                                    {e.timestamp}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right pl-2">
                                            <div className="font-bold text-white text-md">
                                                {e.value > 1000000 ? `$${formatCompactNumber(e.value)}` :
                                                    (e.label && e.label.includes('$') ? e.label : formatCompactNumber(e.amountOut))}
                                            </div>
                                            <a
                                                href={`https://monadscan.com/tx/${e.hash}`}
                                                target="_blank"
                                                className="text-[10px] text-blue-400 hover:underline block mt-1"
                                                rel="noreferrer"
                                            >
                                                View Tx ↗
                                            </a>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* SECTION B: LIQUIDITY MAP */}
                <div className="card bg-base-100 shadow-2xl border border-gray-800 h-[600px]">
                    <div className="card-header p-4 border-b border-gray-800 bg-black/40 flex justify-between items-center">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            💧 Liquidity Depth (Kuru)
                        </h2>
                    </div>
                    <div className="card-body p-6 space-y-6 overflow-y-auto">
                        {filteredPools.length === 0 ? (
                            <div className="text-center text-gray-500 mt-20">
                                {searchTerm ? "No matching pools." : (
                                    <>
                                        <span className="loading loading-bars loading-lg"></span>
                                        <p className="mt-4">Analysing Pools...</p>
                                    </>
                                )}
                            </div>
                        ) : (
                            filteredPools.map((pool, i) => (
                                <div key={i} className="group relative">
                                    <div className="flex justify-between items-center mb-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-sm text-gray-300">{pool.name}</span>
                                            <span className="badge badge-xs badge-info badge-outline text-[10px]">
                                                {pool.dex || 'Kuru'}
                                            </span>
                                        </div>
                                        <span className="text-xs font-mono text-gray-500">TVL: ${pool.tvl ? pool.tvl.toFixed(0) : '???'}</span>
                                    </div>

                                    {/* Visual Bar */}
                                    <div className="h-20 w-full bg-black/40 rounded-lg relative overflow-hidden flex items-end border border-gray-700">
                                        {/* Water Effect */}
                                        <div
                                            className="absolute bottom-0 left-0 w-full bg-blue-500/20 transition-all duration-1000"
                                            style={{ height: '60%' }}
                                        ></div>

                                        {/* Bars */}
                                        <div className="w-1/2 h-[70%] bg-indigo-500/80 mx-1 rounded-t-sm animate-pulse" title="Token 0"></div>
                                        <div className="w-1/2 h-[50%] bg-purple-500/80 mx-1 rounded-t-sm" title="Token 1"></div>

                                        {/* Threshold Line */}
                                        <div
                                            className="absolute w-full border-t border-dashed border-yellow-500/50"
                                            style={{ bottom: '10%' }}
                                            title="Whale Threshold"
                                        ></div>
                                    </div>
                                    <div className="text-xs text-right text-yellow-600 mt-1">
                                        Alert  ${pool.threshold ? pool.threshold.toFixed(0) : '0'}
                                    </div>
                                </div>
                            ))
                        )}
                        <div className="alert alert-warning text-xs mt-4">
                            <span>Visualization uses estimated TVL from Kuru API.</span>
                        </div>
                    </div>
                </div>


            </div>

            {/* SECTION C: PROFIT GAUGE (Full Width) */}
            <div className="card bg-base-100 shadow-2xl border border-gray-800 h-[400px]">
                <div className="card-header p-4 border-b border-gray-800 bg-black/40">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        🚀 Profit Engine
                        {scanning && <span className="loading loading-spinner loading-sm"></span>}
                    </h2>
                </div>
                <div className="card-body flex flex-row items-center justify-around p-8 bg-gradient-to-br from-black to-gray-900">
                    {/* LEFT: GAUGE */}
                    <div className="flex flex-col items-center">
                        <div className="relative w-full max-w-[250px] aspect-[2/1] overflow-hidden">
                            {/* Arc */}
                            <div className="absolute inset-0 rounded-t-full border-[20px] border-gray-800 border-b-0"></div>
                            <div
                                className={`absolute inset-0 rounded-t-full border-[20px] border-b-0 transition-all duration-700 ${arbitrage?.best?.profit_pct > 0 ? 'border-success' : 'border-gray-700'
                                    }`}
                                style={{
                                    clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0% 100%)',
                                    transformOrigin: 'bottom center',
                                    transform: `rotate(${(Math.min(arbitrage?.best?.profit_pct || 0, 5) / 5) * 180 - 180}deg)`
                                }}
                            ></div>

                            {/* Needle */}
                            <div
                                className="absolute bottom-0 left-1/2 w-1 h-[80%] bg-white origin-bottom transition-transform duration-500 ease-out z-10"
                                style={{
                                    transform: `translateX(-50%) rotate(${(Math.min(arbitrage?.best?.profit_pct || 0, 5) / 5) * 180 - 90}deg)`
                                }}
                            ></div>
                            <div className="absolute bottom-[-10px] left-1/2 w-4 h-4 bg-white rounded-full -translate-x-1/2 z-20"></div>
                        </div>
                        {/* TEXT STATS */}
                        <div className={`text-5xl font-black mt-4 font-mono ${arbitrage?.best?.net_profit_usd > 0 ? 'text-success animate-bounce' : 'text-gray-600'}`}>
                            {arbitrage?.best?.net_profit_usd > 0 ? '+' : ''}${arbitrage?.best?.net_profit_usd?.toFixed(4) || '0.000'}
                        </div>
                        <div className="text-gray-400 font-mono">NET PROFIT EST.</div>
                    </div>

                    {/* RIGHT: LOGS */}
                    <div className="flex-1 max-w-2xl h-full ml-8">
                        <div className="w-full bg-black/50 rounded-xl p-4 h-full overflow-y-auto font-mono text-sm text-gray-300 border border-gray-800">
                            {arbitrage ? (
                                arbitrage.ranking.length > 0 ? (
                                    <div className="space-y-2">
                                        {arbitrage.ranking.map((item: any, i: number) => (
                                            <div key={i}
                                                onClick={() => setExpandedIds(prev => prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i])}
                                                className="flex flex-col py-2 border-b border-gray-800/50 hover:bg-white/5 px-2 rounded cursor-pointer transition-all"
                                            >
                                                <div className="flex justify-between items-center w-full">
                                                    <span className="flex items-center gap-2">
                                                        <span className="badge badge-sm badge-neutral">#{i + 1}</span>
                                                        <span className="font-bold text-white">{item.token_pair || item.token}</span>
                                                    </span>
                                                    <span className={item.net_profit_usd > 0 ? "text-success font-bold" : "text-gray-500"}>
                                                        ${item.net_profit_usd?.toFixed(4)} <span className="text-xs text-gray-600 font-normal">({item.strategy})</span>
                                                    </span>
                                                </div>

                                                {/* Detailed Logs Expansion */}
                                                {expandedIds.includes(i) && (
                                                    <div className="mt-2 pl-8 text-xs text-gray-500 font-mono space-y-1 bg-black/20 p-2 rounded border-l-2 border-teal-900/50">
                                                        {item.logs?.map((log: string, k: number) => (
                                                            <div key={k}>{log}</div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-2 mt-10">
                                        <span>📉 No profitable cross-market paths found.</span>
                                        <span className="text-xs text-gray-600">Identified paths were filtered (Same-DEX / Low Liquidity).</span>
                                    </div>
                                )
                            ) : (
                                <div className="text-center mt-20 text-gray-500">System Idle. Scanning market...</div>
                            )}
                        </div>
                    </div>
                </div>
                {arbitrage?.best?.comparison && (
                    <div className="absolute top-4 right-4 text-xs bg-gray-800 rounded px-2 py-1">
                        🆚 Monad: {arbitrage.best.comparison.profit_a.toFixed(2)}% vs Sim: {arbitrage.best.comparison.profit_b.toFixed(2)}%
                    </div>
                )}
            </div>
        </div>
    );
}
