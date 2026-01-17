
import { createPublicClient, createWalletClient, http, parseEther, encodeFunctionData, Hex, formatEther } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { monadTestnet } from 'viem/chains';
import dotenv from 'dotenv';

dotenv.config();

// Configuration
const RPC_URL = process.env.RPC_URL || "https://testnet-rpc.monad.xyz";
const HIVE_ACCOUNT_ADDRESS = process.env.HIVE_ACCOUNT_ADDRESS as Hex;
const AGENT_KEY = process.env.AGENT_KEY as Hex;

// Mock DEX Addresses (In real app, load from subgraph or config)
const DEX_CLUSTER = (process.env.DEX_CLUSTER || "").split(',').filter(x => x) as Hex[];

if (DEX_CLUSTER.length < 2) {
  console.warn("⚠️  Warning: Need at least 2 DEX addresses in .env (DEX_CLUSTER) to arb. Using mock list for demo.");
  // Fallback Mock Addresses (Placeholders)
  DEX_CLUSTER.push("0x1111111111111111111111111111111111111111");
  DEX_CLUSTER.push("0x2222222222222222222222222222222222222222");
  DEX_CLUSTER.push("0x3333333333333333333333333333333333333333");
}

// ABIs
const MOCK_DEX_ABI = [
  { name: "swapExactEthForTokens", type: "function", stateMutability: "payable", inputs: [], outputs: [] },
  { name: "swapExactTokensForEth", type: "function", stateMutability: "nonpayable", inputs: [{ type: "uint256" }], outputs: [] },
  { name: "getPrice", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] }
];

const HIVE_ACCOUNT_ABI = [
  {
    name: "executeBatch",
    type: "function",
    stateMutability: "nonpayable",
    inputs: [
      { type: "address[]", name: "targets" },
      { type: "uint256[]", name: "values" },
      { type: "bytes[]", name: "data" }
    ],
    outputs: []
  }
];

const monadChain = { ...monadTestnet, rpcUrls: { default: { http: [RPC_URL] } } };

async function main() {
  if (!AGENT_KEY) throw new Error("Missing AGENT_KEY");

  const account = privateKeyToAccount(AGENT_KEY);
  const client = createWalletClient({ account, chain: monadChain, transport: http() });
  const publicClient = createPublicClient({ chain: monadChain, transport: http() });

  console.log(`[Sniper] Agent online: ${account.address}`);
  console.log(`[Sniper] Controlling Hive: ${HIVE_ACCOUNT_ADDRESS}`);
  console.log(`[Scanner] Monitoring ${DEX_CLUSTER.length} pools...`);

  // Loop
  setInterval(async () => {
    try {
      // --- 1. SCANNER LAYER ---
      const prices = await Promise.all(DEX_CLUSTER.map(async (address) => {
        try {
          // For demo, if address is fake, return random mock price
          if (address.startsWith("0x11")) return 100n + BigInt(Math.floor(Math.random() * 5));
          if (address.startsWith("0x22")) return 102n + BigInt(Math.floor(Math.random() * 5));
          if (address.startsWith("0x33")) return 98n + BigInt(Math.floor(Math.random() * 5));

          return await publicClient.readContract({
            address, abi: MOCK_DEX_ABI, functionName: 'getPrice'
          }) as bigint;
        } catch (e) { return 0n; }
      }));

      // Map prices to objects
      const marketState = DEX_CLUSTER.map((addr, i) => ({
        address: addr,
        price: prices[i]
      })).filter(m => m.price > 0n);

      if (marketState.length < 2) return;

      // --- 2. DECISION LAYER ---
      // Strategy: Buy at High Rate (Cheap Tokens), Sell at Low Rate (Expensive Tokens)
      // Price = Tokens per ETH.
      // Max Price = Most Tokens per ETH (Buy Here)
      // Min Price = Least Tokens per ETH (Sell Here)

      marketState.sort((a, b) => Number(b.price - a.price)); // Descending
      const buyDex = marketState[0];                     // Max Price
      const sellDex = marketState[marketState.length - 1]; // Min Price

      const spread = buyDex.price - sellDex.price;
      const profitPerEth = spread; // Simplified (1 ETH -> 105 Tokens -> 1.05 ETH vs 100 Tokens -> 1.0 ETH)

      // Log Status
      const logMsg = `[Scanner] Best Spread: ${spread.toString()} (Buy @ ${buyDex.price} / Sell @ ${sellDex.price})`;
      // Only log sparingly or if spread changes significantly? No, console is fine for demo.
      console.log(logMsg);

      // Trigger Threshold (e.g., > 2 difference)
      if (spread > 2n) {
        console.log(`[Brain] 🧠 Opportunity Detected! Route: ${buyDex.address.slice(0, 6)} -> ${sellDex.address.slice(0, 6)}`);

        // --- 3. EXECUTION LAYER ---
        const betAmount = parseEther("0.1");

        // Calc tokens received: 0.1 * buyPrice
        const tokensReceived = (betAmount * buyDex.price) / 1000000000000000000n; // Scaling handled? 
        // Wait, price is likely just an integer like 100.
        // If price is 100, then 0.1 ETH * 100 = 10 Tokens. 
        // But units: 1 ETH = 1e18 Wei. User sends 0.1e18 Wei.
        // Contract: amountOut = msg.value * price.
        // So if price=100, amountOut = 0.1e18 * 100 = 10e18.

        // Sell logic: amountIn = 10e18.
        // Contract: amountOut = amountIn / price.
        // Sell at price 98. 10e18 / 98 = 0.102 ETH. Profit!

        const expectedTokens = betAmount * buyDex.price; // Wei * Int

        // Encode Calls
        const buyData = encodeFunctionData({
          abi: MOCK_DEX_ABI, functionName: 'swapExactEthForTokens'
        });
        const sellData = encodeFunctionData({
          abi: MOCK_DEX_ABI, functionName: 'swapExactTokensForEth', args: [expectedTokens]
        });

        console.log(`[Sniper] 🔫 Firing Atomic Batch Transaction...`);

        const tx = await client.writeContract({
          address: HIVE_ACCOUNT_ADDRESS,
          abi: HIVE_ACCOUNT_ABI,
          functionName: 'executeBatch',
          args: [
            [buyDex.address, sellDex.address], // Targets
            [betAmount, 0n],                   // Values (Send ETH to Buy, 0 for Sell)
            [buyData, sellData]                // Payloads
          ]
        });

        console.log(`[Sniper] ✅ Confirmed: ${tx}`);
      }

    } catch (e) {
      console.error(`[Sniper] Error loop:`, e);
    }
  }, 1000);
}

main();
