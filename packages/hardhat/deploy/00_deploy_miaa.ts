import { HardhatRuntimeEnvironment } from "hardhat/types";
import { DeployFunction } from "hardhat-deploy/types";
import { ethers } from "hardhat";

/**
 * Deploys the MIAA Ecosystem (HiveAccount + MockDEXs)
 * 1. Deploy MockDEXs
 * 2. Deploy QuotaModule
 * 3. Deploy HiveAccount (Owner = Deployer/Agent)
 * 4. Set Agent as Executor
 * 5. Transfer Ownership to User Frontend Wallet
 */
const deployMIAA: DeployFunction = async function (hre: HardhatRuntimeEnvironment) {
    const { deployer } = await hre.getNamedAccounts();
    const { deploy } = hre.deployments;

    // Frontend Wallet from User Request
    const USER_WALLET = "0x1CEEec77C4C3d9f9b3baC727F836C27840229694";

    console.log("--------------- DEPLOYING MIAA ---------------");
    console.log("Deploying as Agent:", deployer);

    // 1. Deploy Mock DEXs
    const dex1 = await deploy("MockDEX", {
        from: deployer,
        args: [100], // seed
        log: true,
        autoMine: true,
    });
    console.log("MockDEX Deployed at:", dex1.address);

    // 1.5 Deploy Mock USDC (MockERC20)
    const mUSDC = await deploy("MockERC20", {
        from: deployer,
        args: ["Mock USDC", "mUSDC"],
        log: true,
        autoMine: true,
    });
    console.log("mUSDC Deployed at:", mUSDC.address);

    // 1.1 Fund MockDEX (Liquidity for Reverse Swaps MON->USDC)
    // IMPORTANT: Actually, for MockDEX to sell MON, it needs MON balance.
    // For MockDEX to sell USDC, it needs USDC balance.

    // Fund with MON
    console.log("Funding MockDEX with 10 MON...");
    await (await ethers.provider.getSigner(deployer)).sendTransaction({
        to: dex1.address,
        value: ethers.parseEther("10.0")
    });

    // Fund with mUSDC (User also needs mUSDC really, but let's give DEX some too)
    const musdcContract = await ethers.getContractAt("MockERC20", mUSDC.address);
    // Mint/Transfer to DEX? The deployer has 10M.
    console.log("Funding MockDEX with 500,000 mUSDC...");
    await (await musdcContract.transfer(dex1.address, 500000n * 10n ** 6n)).wait();

    // 2. Deploy Module
    const quotaModule = await deploy("QuotaSessionModule", {
        from: deployer,
        args: [],
        log: true,
        autoMine: true,
    });

    // 3. Deploy HiveAccount
    const hiveAccountDeploy = await deploy("HiveAccount", {
        from: deployer,
        args: [deployer], // Initial Owner must be deployer to config
        log: true,
        autoMine: true,
    });
    const hiveAccount = await ethers.getContractAt("HiveAccount", hiveAccountDeploy.address);
    console.log("HiveAccount Deployed at:", hiveAccountDeploy.address);

    // 3.1 Fund the HiveAccount (Crucial for Swaps!)
    console.log("Funding HiveAccount with 10 MON...");
    const fundTx = await (await ethers.provider.getSigner(deployer)).sendTransaction({
        to: hiveAccountDeploy.address,
        value: ethers.parseEther("10.0")
    });
    await fundTx.wait();
    console.log("Funded HiveAccount with 10 MON");

    // 3.2 Fund HiveAccount with mUSDC (so it can sell USDC for MON)
    console.log("Funding HiveAccount with 10,000 mUSDC...");
    await (await musdcContract.transfer(hiveAccountDeploy.address, 10000n * 10n ** 6n)).wait();

    // 4. Setup Permissions
    // Enable Module
    console.log("Enabling Module...");
    await (await hiveAccount.enableModule(quotaModule.address)).wait();

    // Authorize Executor (Agent/Deployer)
    console.log("Setting Executor...");
    await (await hiveAccount.setExecutor(deployer, true)).wait();
    console.log("Executor Set:", deployer);

    // 5. Transfer Ownership to User
    console.log("Transferring Ownership...");
    await (await hiveAccount.transferOwnership(USER_WALLET)).wait();
    console.log("Ownership Transferred to User:", USER_WALLET);

    console.log("----------------------------------------------");
};

export default deployMIAA;

deployMIAA.tags = ["MIAA"];
