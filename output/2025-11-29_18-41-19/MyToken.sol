// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;


import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title MyToken
/// @dev An ERC20 token with minting and burning capabilities.
contract MyToken is ERC20, ERC20Burnable, Ownable {
    /// @dev Emitted when tokens are minted.
    /// @param to The address receiving the minted tokens.
    /// @param value The amount of tokens minted.
    event Mint(address indexed to, uint256 value);

    /// @dev Emitted when tokens are burned.
    /// @param from The address whose tokens are burned.
    /// @param value The amount of tokens burned.
    event Burn(address indexed from, uint256 value);

    /// @dev Initializes the contract setting the deployer as the initial owner and minting the initial supply.
    constructor() ERC20("MyToken", "MTK") Ownable(msg.sender) {
        _mint(msg.sender, 1000000 * 10 ** decimals());
    }

    /// @notice Allows the owner to mint additional tokens.
    /// @param amount The amount of tokens to mint.
    /// @dev Emits a {Mint} event.
    function mint(uint256 amount) public onlyOwner {
        if (amount == 0) revert InvalidAmount();
        _mint(msg.sender, amount);
        emit Mint(msg.sender, amount);
    }

    /// @notice Allows any token holder to burn their tokens.
    /// @param amount The amount of tokens to burn.
    /// @dev Emits a {Burn} event.
    function burn(uint256 amount) public override {
        if (amount == 0) revert InvalidAmount();
        super.burn(amount);
        emit Burn(msg.sender, amount);
    }

    /// @dev Custom error for invalid amounts.
    error InvalidAmount();
}
