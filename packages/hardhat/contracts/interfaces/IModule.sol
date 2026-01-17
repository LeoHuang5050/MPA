// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {UserOp} from "./IAccount.sol";

interface IModule {
    /**
     * @dev Validates a session key signature and permissions.
     * @return validationData Packed validation data (0 = success, 1 = failure, or timestamps).
     */
    function validateSession(UserOp calldata userOp, bytes32 userOpHash, bytes calldata moduleSignature)
        external
        returns (uint256 validationData);
}
