import { createPublicClient, http, parseUnits, formatUnits, defineChain, getAddress } from 'viem';
import { mainnet } from 'viem/chains';

// Configuration
const RPC_URL = "https://rpc.flashbots.net";
const QUOTER_ADDRESS = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"; // QuoterV1
const USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
const WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";

const client = createPublicClient({
    chain: mainnet,
    transport: http(RPC_URL)
});

const QUOTER_ABI = [
    {
        name: "quoteExactInputSingle",
        type: "function",
        stateMutability: "view",
        inputs: [
            { name: "tokenIn", type: "address" },
            { name: "tokenOut", type: "address" },
            { name: "fee", type: "uint24" },
            { name: "amountIn", type: "uint256" },
            { name: "sqrtPriceLimitX96", type: "uint160" }
        ],
        outputs: [
            { name: "amountOut", type: "uint256" }
        ]
    }
];

async function main() {
    console.log(`Connecting to ${RPC_URL}...`);
    try {
        const chainId = await client.getChainId();
        console.log(`Chain ID: ${chainId}`);
    } catch (e) {
        console.error("RPC Connection Failed");
        return;
    }

    console.log("Checking Mainnet Quote (USDC -> WETH)...");
    const amountIn = parseUnits("1000", 6); // 1000 USDC

    const FEES = [500, 3000, 10000];

    for (const fee of FEES) {
        try {
            const amountOut = await client.readContract({
                address: QUOTER_ADDRESS,
                abi: QUOTER_ABI,
                functionName: 'quoteExactInputSingle',
                args: [USDC, WETH, fee, amountIn, 0n]
            });
            console.log(`Fee ${fee}: 1000 USDC = ${formatUnits(amountOut, 18)} WETH ✅`);
        } catch (e) {
            console.log(`Fee ${fee} failed:`);
            console.log(e);
        }
    }
}

main();
