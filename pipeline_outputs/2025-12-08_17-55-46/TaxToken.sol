// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title TaxToken - A token that charges a 3% tax on every transfer and sends the tax to the treasury wallet.
contract TaxToken {
    // State variables
    address public owner;
    address public treasuryWallet;
    uint256 private taxRate = 3; // 3% tax

    mapping(address => uint256) private balances;
    uint256 private totalSupply;

    // Events
    event Transfer(address indexed from, address indexed to, uint256 value);
    event TaxApplied(address indexed from, address indexed to, uint256 taxAmount);

    // Custom errors
    error InsufficientBalance(uint256 available, uint256 required);
    error Unauthorized();

    /// @dev Modifier to check if the caller is the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @notice Constructor to set the initial treasury wallet and owner.
    /// @param _treasuryWallet The address of the treasury wallet.
    constructor(address _treasuryWallet) {
        owner = msg.sender;
        treasuryWallet = _treasuryWallet;
        totalSupply = 1000000 * 10**18; // Example total supply
        balances[owner] = totalSupply;
    }

    /// @notice Transfers tokens from the caller to the specified address, applying a 3% tax sent to the treasury wallet.
    /// @param to The address to transfer tokens to.
    /// @param amount The amount of tokens to transfer.
    /// @return success A boolean indicating if the transfer was successful.
    function transfer(address to, uint256 amount) public returns (bool success) {
        uint256 balance = balances[msg.sender];
        uint256 taxAmount = (amount * taxRate) / 100;
        uint256 amountAfterTax = amount - taxAmount;

        if (balance < amount) revert InsufficientBalance(balance, amount);

        // Effects
        balances[msg.sender] -= amount;
        balances[to] += amountAfterTax;
        balances[treasuryWallet] += taxAmount;

        // Interactions
        emit Transfer(msg.sender, to, amountAfterTax);
        emit TaxApplied(msg.sender, treasuryWallet, taxAmount);

        return true;
    }

    /// @notice Returns the balance of the specified address.
    /// @param account The address to query the balance of.
    /// @return The balance of the specified address.
    function balanceOf(address account) public view returns (uint256) {
        return balances[account];
    }

    /// @notice Returns the total supply of the token.
    /// @return The total supply of the token.
    function totalSupply() public view returns (uint256) {
        return totalSupply;
    }
}
