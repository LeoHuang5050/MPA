import { createPublicClient, http, parseAbiItem, defineChain } from 'viem';

const RPC_LIST = [
    "https://testnet-rpc.monad.xyz",
    "https://monad-testnet.drpc.org",
    "https://rpc.ankr.com/monad_testnet",
    "https://10143.rpc.thirdweb.com"
];

const CHAIN_ID = 10143;

// Addresses to Check
const CONTRACTS = {
    "WMON (New)": "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A",
    "WMON (Old)": "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701",
    "Factory (User)": "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
    "Quoter (User)": "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",
    "USDC (User)": "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea",
};

const monadTestnet = defineChain({
    id: CHAIN_ID,
    name: "Monad Testnet",
    nativeCurrency: { name: "Monad", symbol: "MON", decimals: 18 },
    rpcUrls: { default: { http: [RPC_LIST[0]] } },
});

async function main() {
    console.log("1. Testing RPCs & Contracts...");

    let client;
    let successfulRpc = "";

    for (const rpc of RPC_LIST) {
        console.log(`\n--- Trying RPC: ${rpc} ---`);
        try {
            client = createPublicClient({
                chain: { ...monadTestnet, rpcUrls: { default: { http: [rpc] } } },
                transport: http()
            });

            const chainId = await client.getChainId();
            console.log(`Connected! ChainID: ${chainId}`);

            // Validate Quoter (Most important)
            const code = await client.getBytecode({ address: CONTRACTS["Quoter (User)"] });
            if (code && code.length > 2) {
                console.log(`✅ RPC is Good! Quoter has code (${code.length} bytes).`);
                successfulRpc = rpc;
                break;
            } else {
                console.log(`❌ RPC OK but Quoter has NO code.`);
            }
        } catch (e) {
            console.log(`❌ RPC Connection Failed: ${e.shortMessage || "Timeout"}`);
        }
    }

    if (!successfulRpc || !client) {
        console.error("\nCRITICAL: No working RPC found with deployed Quoter.");
        return;
    }

    // Now check other addresses with GOOD client
    console.log("\n2. Checking Token/Factory Status...");
    for (const [name, address] of Object.entries(CONTRACTS)) {
        if (name === "Quoter (User)") continue;
        const code = await client.getBytecode({ address });
        const len = code ? code.length : 0;
        console.log(`${name.padEnd(20)} (${address}): ${len} bytes ${len > 2 ? "✅" : "❌"}`);
    }

    CONTRACTS["Factory (Real)"] = CONTRACTS["Factory (User)"];

    // Try to find Factory via Quoter if User Factory is invalid
    const factoryCode = await client.getBytecode({ address: CONTRACTS["Factory (User)"] });
    if (!factoryCode || factoryCode.length <= 2) {
        try {
            const factory = await client.readContract({
                address: CONTRACTS["Quoter (User)"],
                abi: [parseAbiItem('function factory() view returns (address)')],
                functionName: 'factory'
            });
            console.log(`\nFetched REAL Factory from Quoter: ${factory}`);
            CONTRACTS["Factory (Real)"] = factory;

            const code = await client.getBytecode({ address: factory });
            console.log(`Real Factory Code: ${code ? code.length : 0} bytes`);
        } catch (e) {
            console.log(`\nFailed to read factory from Quoter: ${e.shortMessage}`);
        }
    }

    // Discovery
    const FactoryUsed = CONTRACTS["Factory (Real)"];
    if (await isContract(client, FactoryUsed)) {
        console.log(`\n3. Discovering Pools using Factory: ${FactoryUsed}`);

        // Tokens to mix
        const TOKENS = [
            { name: "WMON (New)", addr: CONTRACTS["WMON (New)"] },
            { name: "WMON (Old)", addr: CONTRACTS["WMON (Old)"] }, // Just in case
            { name: "USDC", addr: CONTRACTS["USDC (User)"] }
        ];

        const FEES = [500, 3000, 10000];

        for (let i = 0; i < TOKENS.length; i++) {
            for (let j = i + 1; j < TOKENS.length; j++) {
                const t0 = TOKENS[i];
                const t1 = TOKENS[j];

                // Skip if both are dummy/0 bytes (optimization)
                // But we don't know for sure until we try.

                for (const fee of FEES) {
                    try {
                        const pool = await client.readContract({
                            address: FactoryUsed,
                            abi: [parseAbiItem('function getPool(address,address,uint24) view returns (address)')],
                            functionName: 'getPool',
                            args: [t0.addr, t1.addr, fee]
                        });

                        if (pool && pool !== "0x0000000000000000000000000000000000000000") {
                            console.log(`FOUND POOL! ${t0.name}/${t1.name} (Fee ${fee}): ${pool}`);
                            try {
                                const slot0 = await client.readContract({
                                    address: pool,
                                    abi: [parseAbiItem('function slot0() view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)')],
                                    functionName: 'slot0'
                                });
                                console.log(`   -> SqrtPrice: ${slot0[0]}`);
                            } catch (e) {
                                console.log(`   -> Pool exists but slot0 read failed.`);
                            }
                        }
                    } catch (e) { }
                }
            }
        }
    }
}

async function isContract(client, addr) {
    if (!addr) return false;
    const code = await client.getBytecode({ address: addr });
    return code && code.length > 2;
}

main();
