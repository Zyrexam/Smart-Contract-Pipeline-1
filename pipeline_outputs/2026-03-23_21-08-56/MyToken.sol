// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MyToken is ERC20, ERC20Burnable, Ownable {
    using SafeERC20 for IERC20;

    mapping(address => uint256) private balances;

    /// @notice Emitted when tokens are minted
    /// @param to The address receiving the minted tokens
    /// @param value The amount of tokens minted
    event Mint(address indexed to, uint256 value);

    /// @notice Emitted when tokens are burned
    /// @param from The address whose tokens are burned
    /// @param value The amount of tokens burned
    event Burn(address indexed from, uint256 value);

    /// @notice Error for unauthorized access
    error Unauthorized();

    /// @notice Error for invalid address
    error InvalidAddress();

    /// @notice Error for insufficient balance
    error InsufficientBalance();

    constructor() ERC20("MyToken", "TKN") Ownable(msg.sender) {}

    /// @notice Mints new tokens to the specified address
    /// @param to The address to mint tokens to
    /// @param amount The amount of tokens to mint
    function mint(address to, uint256 amount) public onlyOwner {
        if (to == address(0)) revert InvalidAddress();
        _mint(to, amount);
        emit Mint(to, amount);
    }

    /// @notice Burns tokens from the specified address
    /// @param from The address to burn tokens from
    /// @param amount The amount of tokens to burn
    function burn(address from, uint256 amount) public {
        if (from == address(0)) revert InvalidAddress();
        if (balanceOf(from) < amount) revert InsufficientBalance();
        _burn(from, amount);
        emit Burn(from, amount);
    }

    /// @notice Transfers tokens to the specified address
    /// @param to The address to transfer tokens to
    /// @param amount The amount of tokens to transfer
    /// @return success True if the transfer was successful

    /// @notice Returns the balance of the specified address
    /// @param account The address to query the balance of
    /// @return balance The balance of the specified address

}