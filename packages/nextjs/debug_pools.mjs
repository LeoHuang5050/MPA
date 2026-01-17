import { createPublicClient, http, encodeFunctionData, parseAbiItem, defineChain } from 'viem';
// import { defineChain } from 'viem/chains'; // Error: does not provide export

const RPC_URL = "https://testnet-rpc.monad.xyz";
const CHAIN_ID = 10143;

const CONTRACTS = {
    FACTORY: "0x33128a8fC17869897dcE68Ed026d694621f6FDfD", // User provided V3 Factory
    USDT: "0x88b8e2161dedc77ef4ab7585569d2415a1c1055d", // Ambiguous: Token or Ambient Core?
    USDC: "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea",
    WMON: "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
};

const monadTestnet = defineChain({
    id: CHAIN_ID,
    name: "Monad Testnet",
    nativeCurrency: { name: "Monad", symbol: "MON", decimals: 18 },
    rpcUrls: { default: { http: [RPC_URL] } },
});

const client = createPublicClient({ chain: monadTestnet, transport: http() });

// Check Quoter
try {
    const factoryAddress = await client.readContract({
        address: "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a", // Verified Quoter
        abi: [parseAbiItem('function factory() view returns (address)')],
        functionName: 'factory'
    });
    console.log(`REAL Factory Address from Quoter: ${factoryAddress}`);
} catch (e) {
    console.log(`Failed to read factory from Quoter: ${e.shortMessage}`);
}


console.log("\n2. Checking Uniswap V3 Factory for Pools...");
const FEES = [500, 3000, 10000];
const PAIRS = [
    [CONTRACTS.USDT, CONTRACTS.WMON, "USDT/WMON"],
    [CONTRACTS.USDC, CONTRACTS.WMON, "USDC/WMON"]
];

async function main() {
    console.log("1. Checking Token Definitions...");

    // Check USDT
    try {
        const symbol = await client.readContract({
            address: CONTRACTS.USDT,
            abi: [parseAbiItem('function symbol() view returns (string)')],
            functionName: 'symbol'
        });
        const decimals = await client.readContract({
            address: CONTRACTS.USDT,
            abi: [parseAbiItem('function decimals() view returns (uint8)')],
            functionName: 'decimals'
        });
        console.log(`USDT (${CONTRACTS.USDT}): Symbol=${symbol}, Decimals=${decimals} ✅`);
    } catch (e) {
        console.log(`USDT (${CONTRACTS.USDT}): Failed to read symbol/decimals. Might be a contract/vault. ❌`);
    }

    // Check USDC
    try {
        const symbol = await client.readContract({
            address: CONTRACTS.USDC,
            abi: [parseAbiItem('function symbol() view returns (string)')],
            functionName: 'symbol'
        });
        console.log(`USDC (${CONTRACTS.USDC}): Symbol=${symbol} ✅`);
    } catch (e) {
        console.log(`USDC (${CONTRACTS.USDC}): Failed to read symbol. ❌`);
    }


    console.log("\n2. Checking Uniswap V3 Factory for Pools...");
    const FEES = [500, 3000, 10000];
    const PAIRS = [
        [CONTRACTS.USDT, CONTRACTS.WMON, "USDT/WMON"],
        [CONTRACTS.USDC, CONTRACTS.WMON, "USDC/WMON"]
    ];

    for (const [t0, t1, name] of PAIRS) {
        console.log(`\n--- Checking ${name} ---`);
        for (const fee of FEES) {
            try {
                const poolAddress = await client.readContract({
                    address: CONTRACTS.FACTORY,
                    abi: [parseAbiItem('function getPool(address,address,uint24) view returns (address)')],
                    functionName: 'getPool',
                    args: [t0, t1, fee]
                });

                if (poolAddress === "0x0000000000000000000000000000000000000000") {
                    console.log(`Fee ${fee}: No Pool (0x0)`);
                    continue;
                }

                // Check Liquidity
                const liquidity = await client.readContract({
                    address: poolAddress,
                    abi: [parseAbiItem('function liquidity() view returns (uint128)')],
                    functionName: 'liquidity'
                });

                const slot0 = await client.readContract({
                    address: poolAddress,
                    abi: [parseAbiItem('function slot0() view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)')],
                    functionName: 'slot0'
                });

                console.log(`Fee ${fee}: Address=${poolAddress}`);
                console.log(`   Liquidity: ${liquidity}`);
                console.log(`   SqrtPrice: ${slot0[0]}`);

            } catch (e) {
                console.log(`Fee ${fee}: Check Failed (${e.shortMessage})`);
            }
        }
    }
}

main();
