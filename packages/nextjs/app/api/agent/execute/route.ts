import { createPublicClient, createWalletClient, http, parseUnits, encodeFunctionData, Hex, formatUnits, defineChain } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { mainnet } from 'viem/chains';
import { NextResponse, NextRequest } from "next/server";
import deployedContracts from "../../../../contracts/deployedContracts";

// Configuration: Mainnet Oracle & Simulated Execution
// Configuration: Monad Local Fork
const RPC_URL = "http://127.0.0.1:8545";
const CHAIN_ID = 31337;

// Monad Mainnet Addresses (Forked)
const QUOTER_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"; // MockDEX

const TOKEN_MAP: Record<string, string> = {
    "MON": "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A", // WMON
    "WMON": "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A",
    "USDC": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0", // MockUSDC
    "USDT": "0xe7cd86e13AC4309349F30B3435a9d337750fC82D",
    "AUSD": "0x00000000eFE302BEAA2b3e6e1b18D08D69a9012a"
};

const QUOTER_ABI = [
    {
        name: "quoteExactInputSingle",
        type: "function",
        stateMutability: "nonpayable",
        inputs: [
            {
                components: [
                    { name: "tokenIn", type: "address" },
                    { name: "tokenOut", type: "address" },
                    { name: "amountIn", type: "uint256" },
                    { name: "fee", type: "uint24" },
                    { name: "sqrtPriceLimitX96", type: "uint160" }
                ],
                name: "params",
                type: "tuple"
            }
        ],
        outputs: [
            { name: "amountOut", type: "uint256" },
            { name: "sqrtPriceX96After", type: "uint160" },
            { name: "initializedTicksCrossed", type: "uint32" },
            { name: "gasEstimate", type: "uint256" }
        ]
    }
];

// Configuration: Python Discovery Service & Simulated Execution
const DISCOVERY_SERVICE_URL = "http://127.0.0.1:5001/find_path";

export async function POST(req: NextRequest) {
    try {
        const { intent, params } = await req.json();
        console.log(`[AGENT] Processing Intent: ${intent}`, params);

        if (intent !== "SWAP" && intent !== "ARBITRAGE") {
            return NextResponse.json({ success: false, message: "Only SWAP/ARBITRAGE supported currently." });
        }

        // 1. Call Python Discovery Service (Web2)
        console.log(`[DISCOVERY] Requesting ${intent} from Python Service...`);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

        let discoveryResult;
        try {
            // Differentiate Endpoint based on Intent
            const endpoint = intent === "ARBITRAGE" ? "find_arbitrage" : "find_path";
            const url = `http://127.0.0.1:5001/${endpoint}`;

            // Robustly check for token parameter (LLM might use tokenIn, token, or asset)
            const targetToken = params.tokenIn || params.token || params.asset || "ALL";
            const targetAmount = params.amount || "1000";

            const payload = intent === "ARBITRAGE"
                ? { token: targetToken, amount: targetAmount, mode: params.mode || "all" }
                : { tokenIn: params.tokenIn || "MON", tokenOut: params.tokenOut || "USDT", amount: params.amount || "1.0" };

            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`Discovery Service Error: ${errText}`);
            }

            discoveryResult = await response.json();

            // Special handling for Arbitrage Response
            if (intent === "ARBITRAGE") {
                const arbData = discoveryResult.data;
                const logs = arbData.logs.join("\n");
                const statusEmoji = arbData.found ? "💰" : "📉";

                let message = `${statusEmoji} **Arbitrage Scan Complete**\n\n`;
                message += `\`\`\`\n${logs}\n\`\`\``;

                if (!arbData.found) {
                    message += `\n\nNo profitable cycle found (>0%). Markets are efficient right now.`;
                } else {
                    message += `\n\n**PROFITABLE PATH FOUND!**\nGross Profit: ${arbData.profit_pct.toFixed(4)}%`;
                }

                return NextResponse.json({
                    success: true, // Always return success to show the logs
                    message: message,
                    data: arbData,
                    txHash: arbData.found ? "0x" + Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join("") : null
                });
            }

        } catch (err: any) {
            console.error(`[DISCOVERY] Failed to connect to Python Service: ${err.message}`);
            return NextResponse.json({
                success: false,
                message: `Discovery Service Unavailable. ensure 'python-discovery/app.py' is running. Error: ${err.message}`
            });
        }

        if (!discoveryResult.success) {
            return NextResponse.json({
                success: false,
                message: `No path found: ${discoveryResult.message}`
            });
        }

        // 2. Prepare Execution (SWAP Logic)
        const { path, raw_path, expectedOutput } = discoveryResult.data;
        const quotes = discoveryResult.data.quotes || [];

        let comparisonTable = `\n| Rank | DEX | Fee | Output | Gas Est | Difference |\n|---|---|---|---|---|---|`;

        // Find best for baseline
        const bestQuote = quotes.find((q: any) => q.isBest) || quotes[0];
        const bestOut = parseFloat(bestQuote.amountOut);

        quotes.forEach((q: any, index: number) => {
            const out = parseFloat(q.amountOut);
            const diff = bestOut - out;
            const rankEmoji = index === 0 ? "🏆" : (index === 1 ? "🥈" : (index === 2 ? "🥉" : ""));

            // Format Fee (e.g. 3000 -> 0.3%, 500 -> 0.05%)
            const feePercent = (q.fee / 10000).toFixed(2).replace(/\.?0+$/, "") + "%";

            comparisonTable += `\n| ${index + 1} ${rankEmoji} | ${q.dex} | ${feePercent} | ${out.toFixed(6)} | ${q.gasEstimate} | -${diff.toFixed(6)} |`;
        });

        console.log(`[DISCOVERY] Best Path Found: ${JSON.stringify(raw_path)} -> Est. Output: ${expectedOutput}`);

        return NextResponse.json({
            success: true,
            message: `✅ Found Optimal Route via **${bestQuote.dex}**!\n\n**Price Comparison:**${comparisonTable}\n\n**Execution Plan:**\n1. Swap on **${bestQuote.dex}** (Fee: ${bestQuote.fee})\n2. Bridge/Execute on Monad (Simulated)`,
            data: {
                path: raw_path,
                expectedOutput: expectedOutput,
                steps: path,
                quotes: quotes
            },
            // return a simulated transaction hash to represent the "Parallel Execution" on Monad
            txHash: "0x" + Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join("")
        });


    } catch (error) {
        console.error("[EXECUTE] Error:", error);
        return NextResponse.json({ success: false, message: String(error) });
    }
}
