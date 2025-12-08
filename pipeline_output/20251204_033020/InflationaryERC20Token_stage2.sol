// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract InflationaryERC20Token is ERC20, AccessControl, Ownable {
    // Custom errors
    error NotTreasury();
    error MintTooSoon();
    error InvalidAddress();

    // State variables
    address public treasury;
    uint256 private lastMintTime;

    // Events
    event MintedInflation(uint256 amount, address to);

    // Role definition
    bytes32 public constant TREASURY_ROLE = keccak256("TREASURY_ROLE");

    /// @notice Constructor to initialize the token with a name, symbol, and treasury address
    /// @param name The name of the token
    /// @param symbol The symbol of the token
    /// @param initialTreasury The address of the treasury
    constructor(string memory name, string memory symbol, address initialTreasury) ERC20(name, symbol) {
        if (initialTreasury == address(0)) revert InvalidAddress();
        treasury = initialTreasury;
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(TREASURY_ROLE, treasury);
        lastMintTime = block.timestamp;
    }

    /// @notice Mints 1% of the total supply to the treasury if a month has passed since the last mint
    function mintMonthlyInflation() external onlyRole(TREASURY_ROLE) {
        if (block.timestamp < lastMintTime + 30 days) revert MintTooSoon();
        
        uint256 mintAmount = totalSupply() / 100;
        _mint(treasury, mintAmount);
        lastMintTime = block.timestamp;

        emit MintedInflation(mintAmount, treasury);
    }
}
