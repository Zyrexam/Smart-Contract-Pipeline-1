// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract SimpleToken is ERC20, ERC20Burnable, Ownable {
    using SafeERC20 for IERC20;

    error NotOwner();
    error InsufficientBalance();

    event Mint(address indexed to, uint256 amount);
    event Burn(address indexed from, uint256 amount);

    constructor() ERC20("Token", "TKN") {
        // Ownable constructor is automatically called
    }

    /**
     * @dev Mints a specified amount of tokens to a given address.
     * @param to The address to mint tokens to.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
        emit Mint(to, amount);
    }

    /**
     * @dev Burns a specified amount of tokens from a given address.
     * @param from The address to burn tokens from.
     * @param amount The amount of tokens to burn.
     */
    function burn(address from, uint256 amount) public onlyOwner {
        if (balanceOf(from) < amount) revert InsufficientBalance();
        _burn(from, amount);
        emit Burn(from, amount);
    }
}
