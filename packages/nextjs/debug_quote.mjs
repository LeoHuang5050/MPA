import { createPublicClient, http, parseUnits, formatUnits } from 'viem';
import { mainnet } from 'viem/chains';

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

    console.log("0. Checking Network...");
    const chainId = await client.getChainId();
    console.log(`Connected Chain ID: ${chainId}`);

    const CONTRACTS = {
        "UniV3 QuoterV2": "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",
        "UniV3 Router": "0x2626664c2603336E57B271c5C0b26F421741e481",
        "WMON": "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701",
        "Ambient Core": "0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D",
        "Nabla Router": "0x4a7b3A83cf4B2fA10f50e27fe88450424B59973d",
        "Pancake V2 Router": "0x4b2ab38dbf28d31d467aa8993f6c2585981d6804"
    };

    console.log("\n1. Checking User Provided Addresses...");

    for (const [name, address] of Object.entries(CONTRACTS)) {
        const code = await client.getBytecode({ address });
        const len = code ? code.length : 0;
        console.log(`${name.padEnd(20)} (${address}): ${len} bytes ${len > 2 ? "✅" : "❌"}`);
    }

    // If Quoter exists, try a quote
    const quoterCode = await client.getBytecode({ address: CONTRACTS["UniV3 QuoterV2"] });
    if (quoterCode && quoterCode.length > 2) {
        console.log("\n2. Testing QuoterV2 (WMON -> Ambient?)...");
        // Using WMON as TokenIn and Ambient/USDT as TokenOut for test?
        // Wait, user said Ambient Core is 0x88b8... but typically that's the vault. 
        // Let's assume 0x88b8... is USDT for a moment (since my previous search said so) or valid token.
        // It's safer to test with WMON -> 0x88b8... (whatever it is).

        const tokenIn = CONTRACTS["WMON"];
        const tokenOut = CONTRACTS["Ambient Core"]; // Potentially USDT?
        const amountIn = parseUnits("0.1", 18); // 0.1 MON

        try {
            // Fees to try
            const fee = 3000;
            console.log(`Trying Quote: 0.1 MON -> 0x88b8... (Fee ${fee})`);

            const result = await client.readContract({
                address: CONTRACTS["UniV3 QuoterV2"],
                abi: QUOTER_ABI,
                functionName: 'quoteExactInputSingle',
                args: [{
                    tokenIn: tokenIn,
                    tokenOut: tokenOut,
                    amountIn: amountIn,
                    fee: fee,
                    sqrtPriceLimitX96: 0n
                }]
            });
            const amountOut = result[0];
            console.log(`SUCCESS! Quote Result: ${formatUnits(amountOut, 6)} (Assuming 6 decimals)`);
        } catch (e) {
            console.log(`Quote Failed: ${e.shortMessage || e.message}`);
            console.log("Note: This might be expected if pool doesn't exist, but Contract check PASSED.");
        }
    }

    console.log("\n2. Testing Quotes (USDT -> MON)...");
    // USDT is usually 6 decimals. Let's try 50 USDT.
    const amountIn = parseUnits("50", 6);

    let success = false;
    for (const fee of FEES) {
        console.log(`\n--- Testing Fee Tier: ${fee} ---`);
        try {
            const result = await client.readContract({
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
            const amountOut = result[0];
            console.log(`SUCCESS! Fee ${fee} works.`);
            console.log(`Quote: ${formatUnits(amountOut, 18)} MON`);
            success = true;
        } catch (e) {
            console.log(`Fee ${fee} Failed: ${e.shortMessage || e.message}`);
        }
    }

    if (!success) {
        console.log("\nAll fees failed. Trying reversed swap (MON->USDT) just in case...");
        const amountInMon = parseUnits("1", 18);
        for (const fee of FEES) {
            console.log(`\n--- Testing Fee Tier: ${fee} (MON -> USDT) ---`);
            try {
                const result = await client.readContract({
                    address: QUOTER_ADDRESS,
                    abi: QUOTER_ABI,
                    functionName: 'quoteExactInputSingle',
                    args: [{
                        tokenIn: TOKENS.MON,
                        tokenOut: TOKENS.USDT,
                        amountIn: amountInMon,
                        fee: fee,
                        sqrtPriceLimitX96: 0n
                    }]
                });
                const amountOut = result[0];
                console.log(`SUCCESS! Fee ${fee} works.`);
                console.log(`Quote: ${formatUnits(amountOut, 6)} USDT`);
                success = true;
            } catch (e) {
                console.log(`Fee ${fee} Failed: ${e.shortMessage || e.message}`);
            }
        }
    }
}

main();
