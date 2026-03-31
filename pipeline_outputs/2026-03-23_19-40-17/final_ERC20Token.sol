// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract ERC20Token is ERC20, ERC20Burnable, Ownable {
    using SafeERC20 for IERC20;

    error InsufficientAllowance();

    constructor() ERC20("Token", "TKN") {
        // Ownable constructor is automatically called
    }

    /**
     * @dev Mints new tokens to the specified address, increasing the total supply.
     * @param to The address to mint tokens to.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    /**
     * @dev Burns tokens from the specified address, decreasing the total supply.
     * @param from The address to burn tokens from.
     * @param amount The amount of tokens to burn.
     */
    function burn(address from, uint256 amount) public onlyOwner {
        _burn(from, amount);
    }

    /**
     * @dev Transfers tokens from the caller's account to another account.
     * @param to The address to transfer tokens to.
     * @param amount The amount of tokens to transfer.
     * @return success A boolean indicating if the transfer was successful.
     */
    function transfer(address to, uint256 amount) public override returns (bool success) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    /**
     * @dev Approves another address to spend a specified amount of tokens on behalf of the caller.
     * @param spender The address allowed to spend the tokens.
     * @param amount The amount of tokens to approve.
     * @return success A boolean indicating if the approval was successful.
     */
    function approve(address spender, uint256 amount) public override returns (bool success) {
        _approve(msg.sender, spender, amount);
        return true;
    }

    /**
     * @dev Transfers tokens from one address to another using an allowance.
     * @param from The address to transfer tokens from.
     * @param to The address to transfer tokens to.
     * @param amount The amount of tokens to transfer.
     * @return success A boolean indicating if the transfer was successful.
     */
    function transferFrom(address from, address to, uint256 amount) public override returns (bool success) {
        uint256 currentAllowance = allowance(from, msg.sender);
        if (currentAllowance < amount) revert InsufficientAllowance();

        _transfer(from, to, amount);
        _approve(from, msg.sender, currentAllowance - amount);
        return true;
    }
}
