// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {IAccount, UserOp} from "./interfaces/IAccount.sol";
import {IModule} from "./interfaces/IModule.sol";

import {ECDSA} from "./libraries/ECDSA.sol";

contract HiveAccount is IAccount {
    address public owner;
    uint256 public constant MAX_QUOTA = 1000 ether; // Safety cap

    using ECDSA for bytes32;

    // Module -> Enabled
    mapping(address => bool) public modules;

    uint256 private _nonce;

    event ModuleEnabled(address module);
    event ModuleDisabled(address module);
    event OwnerChanged(address oldOwner, address newOwner);

    modifier onlyOwner() {
        _onlyOwner();
        _;
    }

    function _onlyOwner() internal view {
        require(msg.sender == owner || msg.sender == address(this), "Only owner");
    }

    constructor(address _owner) {
        owner = _owner;
    }

    function enableModule(address module) external onlyOwner {
        modules[module] = true;
        emit ModuleEnabled(module);
    }

    function disableModule(address module) external onlyOwner {
        modules[module] = false;
        emit ModuleDisabled(module);
    }

    // ERC-4337 Validation
    function validateUserOp(UserOp calldata userOp, bytes32 userOpHash, uint256 missingAccountFunds)
        external
        override
        returns (uint256 validationData)
    {
        // 1. Pay prefund
        if (missingAccountFunds > 0) {
            (bool success,) = payable(msg.sender).call{value: missingAccountFunds}("");
            require(success, "Prefund failed");
        }

        // 2. Check Signature
        // Format: [ModuleAddress (20 bytes)] + [ModuleSignature (dynamic)]
        // If signature length == 65, assume owner signature

        if (userOp.signature.length == 65) {
            // Owner Mode
            bytes32 hash = userOpHash.toEthSignedMessageHash();
            address signer = hash.recover(userOp.signature);
            if (signer != owner) return 1; // SIG_VALIDATION_FAILED
            return 0;
        } else {
            // Module Mode
            address module = address(bytes20(userOp.signature[0:20]));
            if (!modules[module]) return 1; // Invalid module

            bytes memory moduleSignature = userOp.signature[20:];
            return IModule(module).validateSession(userOp, userOpHash, moduleSignature);
        }
    }

    // --------------------------------------------------------
    // NEW: Executor Role & Ownership Transfer
    // --------------------------------------------------------
    mapping(address => bool) public executors;

    function setExecutor(address _executor, bool _active) external onlyOwner {
        executors[_executor] = _active;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Zero addr");
        emit OwnerChanged(owner, newOwner);
        owner = newOwner;
    }

    // --------------------------------------------------------
    // EXECUTION
    // --------------------------------------------------------
    function execute(address target, uint256 value, bytes calldata data) external {
        require(
            msg.sender == address(0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789) || 
            msg.sender == owner || 
            executors[msg.sender],
            "Only EntryPoint, Owner or Executor"
        );
        (bool success,) = target.call{value: value}(data);
        require(success, "Exec failed");
    }

    function executeBatch(address[] calldata targets, uint256[] calldata values, bytes[] calldata data) external {
        require(
            msg.sender == address(0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789) || 
            msg.sender == owner || 
            executors[msg.sender],
            "Only EntryPoint, Owner or Executor"
        );
        require(targets.length == values.length && values.length == data.length, "Len mismatch");

        for (uint256 i = 0; i < targets.length; i++) {
            (bool success,) = targets[i].call{value: values[i]}(data[i]);
            require(success, "Batch Exec failed");
        }
    }

    fallback() external payable {}
    receive() external payable {}
}
