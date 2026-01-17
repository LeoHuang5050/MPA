// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {IModule, UserOp} from "../interfaces/IModule.sol";

import {ECDSA} from "../libraries/ECDSA.sol";

contract QuotaSessionModule is IModule {
    struct Session {
        uint256 maxQuota;
        uint256 spent;
        address signer; // THe actual signing key (e.g. Agent's key)
        bool active;
    }

    // Account -> SessionKeyID (e.g. hash of signer) -> Session Data
    mapping(address => mapping(address => Session)) public sessions;

    event SessionCreated(address indexed account, address indexed signer, uint256 quota);
    event QuotaSpent(address indexed account, address indexed signer, uint256 amount, uint256 totalSpent);

    // Call this from the Account (via execute) to register a new session
    // In a real app, this would be guarded by onlyOwner in the Account
    function createSession(address signer, uint256 quota) external {
        sessions[msg.sender][signer] = Session({maxQuota: quota, spent: 0, signer: signer, active: true});
        emit SessionCreated(msg.sender, signer, quota);
    }

    function validateSession(UserOp calldata userOp, bytes32 userOpHash, bytes calldata moduleSignature)
        external
        override
        returns (uint256)
    {
        // 1. Recover Signer
        // The moduleSignature contains the vanilla ECDSA signature of the session key
        bytes32 hash = ECDSA.toEthSignedMessageHash(userOpHash);
        address recovered = ECDSA.recover(hash, moduleSignature);

        Session storage s = sessions[userOp.sender][recovered];

        // 2. Check if Session exists and matches signer
        if (!s.active || s.signer != recovered) {
            return 1; // SIG_VALIDATION_FAILED
        }

        // 3. Extract Value from CallData (Simplification)
        // In reality, we need to decode userOp.callData to find the value transfer.
        // For HiveMind Demo: We assume UserOp.callData = execute(target, value, data)
        // execute is 4 bytes + 32 bytes (target) + 32 bytes (value) + ...

        uint256 updateValue = 0;
        // execute selector = 0xb61d27f6 (from HiveAccount.execute)
        // We check if it matches
        bytes4 selector = bytes4(userOp.callData[0:4]);
        if (selector == 0xb61d27f6) {
            // Decode value (2nd parameter)
            // calldata layout: selector (4) + target (32) + value (32) + offset (32) + len (32) + data...
            // value is at offset 4 + 32 = 36
            updateValue = uint256(bytes32(userOp.callData[36:68]));
        }

        // 4. Check Quota
        if (s.spent + updateValue > s.maxQuota) {
            return 1; // Quota exceeded
        }

        // 5. Update Spent (Optimistic update - in real AA this might need logic handling reversion,
        // but modules generally don't control state unless called.
        // IMPORTANT: validateUserOp is view-like in standard AA but we are making it stateful for demo simplicity
        // or we rely on the Bundler simulation.
        // Ideally checking quota is done here. Updating it should be done in a pre-exec hook.
        // For Hackathon: We update it here. Note: If tx fails on chain, this state change reverts anyway.)

        // Wait! validateUserOp CANNOT write to storage of other contracts usually.
        // It can only write to the Account's associated storage.
        // However, if we are in a "Shared Module", writing to global storage is allowed but might be throttled (rule of thumb).
        // For a demo, this is fine.
        s.spent += updateValue;
        emit QuotaSpent(userOp.sender, recovered, updateValue, s.spent);

        return 0; // Success
    }
}

