// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MyToken is ERC20, ERC20Burnable, Ownable {
    using SafeERC20 for IERC20;

    error NotOwner();
    error InsufficientBalance();

    mapping(address => uint256) private balances;

    event Mint(address indexed to, uint256 amount);
    event Burn(address indexed from, uint256 amount);

    constructor() ERC20("MyToken", "TKN") Ownable(msg.sender) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Mints new tokens to the specified address.
     * @param to The address to mint tokens to.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
        emit Mint(to, amount);
    }

    /**
     * @dev Burns tokens from the specified address.
     * @param from The address to burn tokens from.
     * @param amount The amount of tokens to burn.
     */
    function burn(address from, uint256 amount) public onlyOwner {
        if (balanceOf(from) < amount) revert InsufficientBalance();
        _burn(from, amount);
        emit Burn(from, amount);
    }

    /**
     * @dev Transfers tokens to a specified address.
     * @param to The address to transfer tokens to.
     * @param amount The amount of tokens to transfer.
     * @return success A boolean indicating if the transfer was successful.
     */

    /**
     * @dev Returns the balance of the specified address.
     * @param account The address to query the balance of.
     * @return balance The balance of the specified address.
     */

}