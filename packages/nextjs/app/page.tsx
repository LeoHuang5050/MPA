"use client";

import { useState, useEffect, useRef } from "react";
import { useAccount, useConnect, useDisconnect, useBalance, useReadContracts } from "wagmi";
import { ChatBubbleLeftRightIcon, CpuChipIcon, CommandLineIcon, PlayIcon, PauseIcon, TrashIcon, WalletIcon, ChartBarIcon } from "@heroicons/react/24/outline";
import { formatEther, formatUnits, erc20Abi } from "viem";
import deployedContracts from "../contracts/deployedContracts";
import Dashboard from "../components/Dashboard";
import { AddressCopyIcon } from "../components/scaffold-eth"; // Fixed Import
import { knownTokens } from "~~/utils/knownTokens";

const CHAIN_ID = 31337;
const HIVE_ACCOUNT = deployedContracts[CHAIN_ID].HiveAccount.address;

export default function Home() {
  const { address, isConnected } = useAccount();
  const [viewMode, setViewMode] = useState<'agent' | 'dashboard'>('dashboard');

  // -- STATES --
  const { data: balanceMON } = useBalance({ address: HIVE_ACCOUNT });
  const [agents, setAgents] = useState([
    { id: 1, name: "Sniper Alpha", status: "空闲", mode: "IDLE", quota: "50 MON", spent: "0.20", profits: "0.00" },
  ]);
  const [logs, setLogs] = useState<string[]>([]);
  const [aiInput, setAiInput] = useState("");
  const [aiProcessing, setAiProcessing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // -- DYNAMIC TOKEN DISCOVERY --
  // 1. Prepare contract calls for all known tokens
  const filteredTokens = knownTokens.filter(t => t.chainId === CHAIN_ID);
  const tokenContractCalls = filteredTokens.map((t) => ({
    address: t.address as `0x${string}`,
    abi: erc20Abi,
    functionName: 'balanceOf',
    args: [HIVE_ACCOUNT]
  }));

  const { data: tokenBalancesData } = useReadContracts({
    contracts: tokenContractCalls,
    query: { refetchInterval: 10000 }
  });

  // 2. Process results into a display list
  // Always include MON, WMON, and USDC first
  const displayTokens = [
    {
      symbol: "MON",
      balance: balanceMON ? parseFloat(formatEther(balanceMON.value)).toFixed(2) : "0.00",
      decimals: 18
    },
    {
      symbol: "WMON",
      balance: "0.00",
      decimals: 18
    },
    {
      symbol: "USDC",
      balance: "0.00",
      decimals: 6
    }
  ];

  if (tokenBalancesData) {
    tokenBalancesData.forEach((result, index) => {
      if (result.status === "success" && result.result) {
        const balance = result.result as bigint;
        const token = filteredTokens[index];
        const balanceFormatted = parseFloat(formatUnits(balance, token.decimals)).toFixed(2);

        // Update existing if present (WMON/USDC), otherwise push new
        const existing = displayTokens.find(t => t.symbol === token.symbol);
        if (existing) {
          existing.balance = balanceFormatted;
        } else if (balance > 0n) {
          displayTokens.push({
            symbol: token.symbol,
            balance: balanceFormatted,
            decimals: token.decimals
          });
        }
      }
    });
  }

  // -- SIMULATION LOOP --
  useEffect(() => {
    const activeAgent = agents.find(a => a.status === "运行中");
    if (activeAgent && !aiProcessing && activeAgent.mode !== "SWAP_COMPLETED") {
      const interval = setInterval(() => {
        const time = new Date().toLocaleTimeString();
        let actions = ["Scanning mempool...", "Found arbitrage: +0.02 MON", "Executing atomic tx...", "Checking reserves..."];
        if (activeAgent.mode === "SWAP_EXECUTION") {
          actions = ["Monitoring price impact...", "Calculating optimal gas...", "Simulating execution..."];
        }
        const randomAction = actions[Math.floor(Math.random() * actions.length)];
        const newLog = `[${time}] ${randomAction}`;
        setLogs(prev => [newLog, ...prev].slice(0, 50));
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [agents, aiProcessing]);

  // -- HANDLERS --
  const toggleAgent = (id: number) => {
    setAgents(prev => prev.map(a => {
      if (a.id !== id) return a;
      const newStatus = a.status === "空闲" ? "运行中" : "空闲";
      const newMode = (newStatus === "运行中" && a.mode === "IDLE") ? "ARBITRAGE" : a.mode;
      return { ...a, status: newStatus, mode: newMode };
    }));
  };

  const spawnAgent = () => {
    const newId = agents.length + 1;
    setAgents(prev => [...prev, { id: newId, name: `Agent ${newId}`, status: "空闲", mode: "IDLE", quota: "10 MON", spent: "0.00", profits: "0.00" }]);
  };

  const handleAiSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiInput.trim()) return;

    setAiProcessing(true);
    setLogs(prev => [`[SYSTEM] Sending instructions to Gemini Brain...`, ...prev]);

    try {
      const response = await fetch("/api/agent/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction: aiInput }),
      });

      const data = await response.json();

      if (data.error) {
        setLogs(prev => [`[ERROR] ${data.error}`, ...prev]);
        setAiProcessing(false);
        return;
      }

      // Handle AI Response
      const { intent, params, thought } = data;
      setLogs(prev => [
        `[BRAIN] 🧠 "${thought}"`,
        `[SYSTEM] Parsed Intent: ${intent} (${(data.confidence * 100).toFixed(0)}%)`,
        ...prev
      ]);
      setAiInput("");

      setAgents(prev => prev.map(a => ({ ...a, status: "运行中", mode: "SWAP_EXECUTION" })));

      if (intent === "SWAP") {
        setLogs(prev => [`[AGENT] 🔍 Checking Monad Prices...`, ...prev]);
        await new Promise(r => setTimeout(r, 1000));

        const execRes = await fetch("/api/agent/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ intent, params }),
        });
        const execData = await execRes.json();

        if (execData.success) {
          setLogs(prev => [
            `[ORACLE] 🔮 ${execData.message}`,
            `[AGENT] 💡 Price check complete. Waiting for user approval to execute.`,
            ...prev
          ]);
          setAgents(prev => prev.map(a => ({ ...a, status: "空闲", mode: "SWAP_QUOTED" })));
        } else {
          setLogs(prev => [`[ERROR] Quote failed: ${execData.details || execData.message}`, ...prev]);
          setAgents(prev => prev.map(a => ({ ...a, status: "空闲", mode: "ERROR" })));
        }

      } else if (intent === "ARBITRAGE") {
        setLogs(prev => [`[AGENT] 🚀 Starting Arbitrage Scan...`, ...prev]);

        const execRes = await fetch("/api/agent/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ intent, params }),
        });
        const execData = await execRes.json();

        if (execData.success) {
          setLogs(prev => [`[ORACLE] ${execData.message}`, ...prev]);
          setAgents(prev => prev.map(a => ({ ...a, status: "空闲", mode: "ARBITRAGE_COMPLETED" })));
        } else {
          setLogs(prev => [`[ERROR] Arb Scan failed: ${execData.message}`, ...prev]);
          setAgents(prev => prev.map(a => ({ ...a, status: "空闲", mode: "ERROR" })));
        }
      }

    } catch (err) {
      setLogs(prev => [`[ERROR] Network failed.`, ...prev]);
    } finally {
      setAiProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#418F8F] font-sans text-white">

      <nav className="flex justify-between items-center px-8 py-5">
        <div className="flex items-center gap-6">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CpuChipIcon className="w-8 h-8" />
            <span>Monad Pulse Arbitrage (MPA)</span>
          </h1>
          <div className="hidden md:flex gap-4 text-sm font-medium text-teal-100">
            <span
              className={`opacity-90 hover:opacity-100 cursor-pointer ${viewMode === 'dashboard' ? 'underline decoration-white underline-offset-4' : ''}`}
              onClick={() => setViewMode('dashboard')}
            >
              Dashboard
            </span>
            <span
              className={`opacity-70 hover:opacity-100 cursor-pointer ${viewMode === 'agent' ? 'underline decoration-white underline-offset-4' : ''}`}
              onClick={() => setViewMode('agent')}
            >
              Agent Control
            </span>
            <span className="opacity-70 hover:opacity-100 cursor-pointer">Debug Contracts</span>
          </div>
        </div>
      </nav>

      <div className="flex flex-col items-center justify-start pt-12 px-4 pb-20">

        {viewMode === 'dashboard' ? (
          <div className="w-full max-w-6xl">
            <Dashboard />
          </div>
        ) : (
          <div className="bg-[#5CB6B6] rounded-3xl shadow-2xl p-8 w-full max-w-2xl border border-[#78D1D1] relative">

            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-2">Agent Control Center</h2>
              <div className="flex justify-center items-center gap-2 text-teal-100/90 font-mono text-sm bg-black/10 mx-auto w-fit px-3 py-1 rounded-md">
                <WalletIcon className="w-4 h-4" />
                <span>HiveAccount: {HIVE_ACCOUNT.slice(0, 6)}...{HIVE_ACCOUNT.slice(-4)}</span>
                <AddressCopyIcon className="h-4 w-4 ml-1 cursor-pointer text-teal-200 hover:text-white" address={HIVE_ACCOUNT} />
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-teal-100 font-bold mb-3 uppercase tracking-wider text-xs text-center">Portfolio Holdings</h3>

              {displayTokens.length > 0 ? (
                <div className={`grid gap-4 text-center bg-black/10 rounded-xl p-4 ${displayTokens.length === 1 ? 'grid-cols-1' :
                  displayTokens.length === 2 ? 'grid-cols-2' :
                    displayTokens.length === 3 ? 'grid-cols-3' : 'grid-cols-2 md:grid-cols-4'
                  }`}>
                  {displayTokens.map((t, i) => (
                    <div key={i} className="flex flex-col p-2 hover:bg-white/5 rounded transition-colors">
                      <span className="text-xs opacity-70">{t.symbol}</span>
                      <span className="font-mono font-bold text-lg">{t.balance}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center opacity-50 text-sm">No assets found</div>
              )}
            </div>

            <div className="mb-10 text-center">
              <div className="text-teal-100 font-bold mb-2 uppercase tracking-wider text-sm">System Quota Usage</div>
              <div className="w-full bg-[#418F8F] rounded-full h-4 mb-2 overflow-hidden relative">
                <div
                  className="bg-white h-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (agents.reduce((acc, c) => acc + parseFloat(c.spent), 0) / 100) * 100)}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-xs font-mono opacity-80 px-1">
                <span>0 MON</span>
                <span>100 MON Limit</span>
              </div>
            </div>

            {isConnected && (
              <div className="grid grid-cols-2 gap-4 mb-8">
                <button
                  onClick={spawnAgent}
                  className="bg-[#2C6E6E] hover:bg-[#205555] text-white py-3 rounded-xl font-bold uppercase tracking-wide transition-colors shadow-lg border-b-4 border-[#1e4d4d] active:border-b-0 active:translate-y-1"
                >
                  Spawn Agent
                </button>
                <button
                  onClick={() => agents.length > 0 && toggleAgent(agents[0].id)}
                  className="bg-[#2C6E6E] hover:bg-[#205555] text-white py-3 rounded-xl font-bold uppercase tracking-wide transition-colors shadow-lg border-b-4 border-[#1e4d4d] active:border-b-0 active:translate-y-1"
                >
                  {agents[0]?.status === '运行中' ? 'Pause All' : 'Activate All'}
                </button>
              </div>
            )}

            <div className="relative">
              <form onSubmit={handleAiSubmit}>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Type intent (e.g. 'Swap 10 MON')..."
                    className="w-full bg-[#418F8F] placeholder-teal-200/50 text-white px-4 py-4 rounded-xl font-bold border-2 border-transparent focus:border-white/50 focus:outline-none pr-32 shadow-inner"
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                  />
                  <button
                    type="submit"
                    disabled={aiProcessing}
                    className="absolute right-2 top-2 bottom-2 bg-white/20 hover:bg-white/30 text-white px-4 rounded-lg font-bold text-sm transition-colors uppercase"
                  >
                    {aiProcessing ? "..." : (isConnected ? "Execute" : "Connect")}
                  </button>
                </div>
              </form>
            </div>

          </div>
        )}

        {logs.length > 0 && viewMode === 'agent' && (
          <div className="mt-8 w-full max-w-2xl bg-black/40 backdrop-blur-md rounded-xl p-4 border border-white/10 font-mono text-xs max-h-64 overflow-y-auto" ref={scrollRef}>
            <div className="text-teal-200 font-bold mb-2 sticky top-0 bg-transparent flex justify-between">
              <span>_ SYSTEM LOGS</span>
              <button onClick={() => setLogs([])} className="hover:text-white">CLEAR</button>
            </div>
            {logs.map((log, i) => (
              <div key={i} className="text-teal-50/80 mb-1 border-l-2 border-teal-500/50 pl-2 whitespace-pre-wrap">
                {log}
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
