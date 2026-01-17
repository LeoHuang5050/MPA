import { createPublicClient, http, parseUnits, formatUnits } from 'viem';
import { mainnet } from 'viem/chains'; // We'll override the chain ID

const RPC_URL = "https://testnet-rpc.monad.xyz";
const QUOTER_ADDRESS = "0x661e93cca42afacb172121ef892830ca3b70f08d";

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

const TOKENS = {
    USDT: "0x88b8e2161dedc77ef4ab7585569d2415a1c1055d",
    MON: "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701" // WMON
};

const FEES = [500, 3000, 10000]; // 0.05%, 0.3%, 1%

async function main() {
    const client = createPublicClient({
        chain: { ...mainnet, id: 10143, rpcUrls: { default: { http: [RPC_URL] } } },
        transport: http()
    });

    console.log("1. Checking Contract Code...");
    const code = await client.getBytecode({ address: QUOTER_ADDRESS });
    console.log(`Code length: ${code ? code.length : 0}`);
    if (!code || code.length <= 2) {
        console.error("ERROR: No code at Quoter Address!");
        return;
    }

    console.log("\n2. Testing Quotes (USDT -> MON)...");
    // USDT is usually 6 decimals. Let's try 50 USDT.
    const amountIn = parseUnits("50", 6);
    console.log(`Amount In: 50 USDT (${amountIn})`);

    for (const fee of FEES) {
        console.log(`\n--- Testing Fee Tier: ${fee} ---`);
        try {
            const [amountOut] = await client.readContract({
                address: QUOTER_ADDRESS,
                abi: QUOTER_ABI,
                functionName: 'quoteExactInputSingle',
                args: [{
                    tokenIn: TOKENS.USDT,
                    tokenOut: TOKENS.MON,
                    amountIn: amountIn,
                    fee: fee,
                    sqrtPriceLimitX96: 0n
                }]
            });
            console.log(`SUCCESS! Fee ${fee} works.`);
            console.log(`Quote: ${formatUnits(amountOut, 18)} MON`);
        } catch (e) {
            console.log(`Fee ${fee} Failed: ${e.shortMessage || e.message}`);
        }
    }
}

main();
