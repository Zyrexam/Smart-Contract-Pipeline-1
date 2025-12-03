// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract TaxToken is ERC20, Ownable, AccessControl, ERC20Burnable {
    using SafeERC20 for IERC20;

    // Custom errors
    error InvalidAddress();
    error TransferAmountTooLow();

    // State variables
    address private treasuryWallet;
    uint256 private taxRate = 3;
    uint256 private minTransferForTimelock = 10000 * 10 ** decimals();

    // Roles
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    // Events
    event TaxCollected(address indexed from, uint256 value);

    // Constructor with proper OpenZeppelin v5 initialization
    constructor(address initialOwner, address _treasuryWallet) ERC20("TaxToken", "TTK") Ownable(initialOwner) {
        if (_treasuryWallet == address(0)) revert InvalidAddress();
        treasuryWallet = _treasuryWallet;
        _grantRole(DEFAULT_ADMIN_ROLE, initialOwner);
        _grantRole(MINTER_ROLE, initialOwner);
    }

    /**
     * @dev Transfers tokens to a specified address, charging a 3% tax and sending it to the treasury wallet.
     * Applies a timelock for transfers over 10000 tokens.
     * @param to The address to transfer to.
     * @param amount The amount to be transferred.
     * @return success A boolean indicating if the transfer was successful.
     */
    function transfer(address to, uint256 amount) public override returns (bool success) {
        _transfer(_msgSender(), to, amount);
        return true;
    }

    /**
     * @dev Mints new tokens to a specified address. Only callable by accounts with the minter role.
     * @param to The address to mint to.
     * @param amount The amount of tokens to mint.
     * @return success A boolean indicating if the mint was successful.
     */
    function mint(address to, uint256 amount) public onlyRole(MINTER_ROLE) returns (bool success) {
        if (to == address(0)) revert InvalidAddress();
        _mint(to, amount);
        return true;
    }

    // Override _update for transfer logic
    function _update(address from, address to, uint256 amount) internal override {
        if (amount == 0) revert TransferAmountTooLow();

        uint256 taxAmount = (amount * taxRate) / 100;
        uint256 transferAmount = amount - taxAmount;

        super._update(from, to, transferAmount);
        if (taxAmount > 0) {
            super._update(from, treasuryWallet, taxAmount);
            emit TaxCollected(from, taxAmount);
        }

        if (amount > minTransferForTimelock) {
            // Implement timelock logic here if needed
        }
    }
}
