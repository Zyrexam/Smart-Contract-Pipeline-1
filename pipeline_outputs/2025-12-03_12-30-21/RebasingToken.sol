// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract RebasingToken is ERC20, Ownable, AccessControl {
    // Custom errors
    error NotOwner();
    error RebaseCooldown();
    error InvalidTargetPrice();

    // State variables
    uint256 private lastRebaseTimestamp = block.timestamp;
    uint256 public targetPrice = 1 ether;

    // Events
    event Rebase(uint256 newTotalSupply);
    event TargetPriceUpdated(uint256 newTargetPrice);

    // Roles
    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

    // Constructor with proper OpenZeppelin v5 initialization
    constructor(address initialOwner) ERC20("RebasingToken", "RBT") Ownable(initialOwner) {
        _grantRole(DEFAULT_ADMIN_ROLE, initialOwner);
        _grantRole(OWNER_ROLE, initialOwner);
    }

    /**
     * @notice Adjusts the total supply of the token to maintain price stability. Can be called every 24 hours.
     */
    function rebase() external onlyRole(OWNER_ROLE) {
        if (block.timestamp < lastRebaseTimestamp + 24 hours) revert RebaseCooldown();
        // Rebase logic here (e.g., adjust total supply)
        lastRebaseTimestamp = block.timestamp;
        emit Rebase(totalSupply());
    }

    /**
     * @notice Sets a new target price for the token.
     * @param newTargetPrice The new target price to set.
     */
    function setTargetPrice(uint256 newTargetPrice) external onlyRole(OWNER_ROLE) {
        if (newTargetPrice == 0) revert InvalidTargetPrice();
        targetPrice = newTargetPrice;
        emit TargetPriceUpdated(newTargetPrice);
    }

    // Override _update for custom transfer logic if needed
    function _update(address from, address to, uint256 value) internal override {
        super._update(from, to, value);
        // Custom transfer logic here
    }
}
