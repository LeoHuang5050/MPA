// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract MockDEX {
    event Swapped(address indexed sender, address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut, uint256 price);

    uint256 public immutable SEED;

    constructor(uint256 _seed) {
        SEED = _seed;
    }

    // Simulated "price" of MON in USD (e.g., 100 USD/MON)
    // We vary it based on block.timestamp AND our unique seed
    function getPrice() public view returns (uint256) {
        // Create unique oscillation for this DEX
        uint256 timeShift = block.timestamp + SEED;
        uint256 oscillation = (timeShift % 20);

    // Base price also varies by seed (100, 101, 99, etc)
        uint256 base = 100 + (SEED % 5);

        if (oscillation > 10) {
            return base - (oscillation - 10);
        } else {
            return base + oscillation;
        }
    }

    // Allow contract to receive ETH (Liquidity)
    receive() external payable {}

    // Swap MON for Token
    function swapExactEthForTokens(address tokenOut) external payable {
        uint256 price = getPrice();
        uint256 amountOut = msg.value * price;
        // tokenIn is Address(0) to represent Native MON
        emit Swapped(msg.sender, address(0), tokenOut, msg.value, amountOut, price);
    }

    // Swap Token for MON (Arbitrage Sell)
    function swapExactTokensForEth(address tokenIn, uint256 amountIn) external {
        uint256 price = getPrice();
        // rate = tokens / eth.  eth = tokens / rate.
        // We simulate a slightly worse price for selling to mimic spread if we wanted,
        // but for now let's just use the inverse.
        uint256 amountOut = amountIn / price; // amountIn (1e18) / price (100) = 0.01 ETH

        require(address(this).balance >= amountOut, "MockDEX: Insufficient liquidity");
        
        // Actually transfer ETH to user
        payable(msg.sender).transfer(amountOut);

        // In simulation, we just give them ETH back (Mock)
        // Note: Contract needs ETH to send back.
        // For demo, we might just emit event or mint ETH if it was a real chain.
        // We'll just emit event for the "Logic Demo".
        // tokenOut is Address(0) to represent Native MON
        emit Swapped(msg.sender, tokenIn, address(0), amountIn, amountOut, price);
    }

    // Uniswap V3 Quoter Interface Support
    struct QuoteParams {
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        uint24 fee;
        uint160 sqrtPriceLimitX96;
    }

    // Imitate QuoterV2.quoteExactInputSingle logic for demonstration
    function quoteExactInputSingle(QuoteParams calldata params) external view returns (uint256 amountOut, uint160 sqrtPriceX96After, uint32 initializedTicksCrossed, uint256 gasEstimate) {
        
        // Mock Pricing Logic for Demo
        // 1 MON = ~35 Tokens (e.g. USDT)
        // 1 Token = ~0.028 MON
        
        uint256 rate = 35; 
        
        // Detect direction
        // If tokenIn is WMON (or address 0/Native placeholder) -> Buy Token
        // Using a heuristic: if amount is small (like 1.0), it's MON. If amount is large (like 35), it's Token.
        // Better: Use specific address checks. Since we don't know exact addresses deploy-time easily here without config,
        // we'll use the 'rate' simply.
        
        // Scenario 1: User selling Tokens (High amount) getting MON (Low amount)
        // Scenario 2: User selling MON (Low amount) getting Tokens (High amount)
        
        // Just for our specific demo "50 USDC -> MON"
        // 50 / 35 = 1.42 MON
        
        if (params.amountIn > 100 * 1e6 && params.amountIn < 10000 * 1e18) {
           // Assume Token -> MON (Amount is like 50 * 1e6)
           // But wait, 50 * 1e6 is small number compared to 1e18.
           // Let's just return a standard mock calc.
        }
        
        // Simplified Logic:
        // Always return Input / 35 (Token -> MON)
        // This fits the "Swap 50 USDC for MON" use case.
        amountOut = params.amountIn / rate; 
        
        // But if user asks "Swap 1 MON for USDT", we need Input * 35.
        // Let's assume input > 1e15 (0.001 ETH) means it's 18 decimals?
        // And if input is 50 * 1e6 (50000000), it's USDC?
        
        // Heuristic: If amountIn is relatively "small" integer value (like 50e6), treats as Token (6 decimals).
        // 1 MON = 1e18.
        
        // Let's just hardcode a rate that looks "real" for the demo: 1 MON = $35.
        // Input 50 USDC (50e6) -> Output 1.42 MON (1.42e18).
        
        // Calculation: 50e6 * 1e12 (to 1e18) / 35 = 1.42e18
        // amountOut = (params.amountIn * 1e12) / 35;
        
        // Safety check for decimals
        if (params.amountIn < 1e15) { // Likely 6 decimals input (e.g. 50,000,000)
             amountOut = (params.amountIn * 1e12) / rate;
        } else {
             // 18 decimals input (Selling MON)
             amountOut = params.amountIn * rate;
        }

        return (amountOut, 0, 0, 0);
    }
}
