// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title TaxToken - A token that charges a 3% tax on every transfer and sends the tax to the treasury wallet.
/// @dev Implements a custom ERC20 token with a tax mechanism.
contract TaxToken {
    // State variables
    address public treasuryWallet;
    address private _owner;
    uint256 private _totalSupply;
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;

    // Events
    event Transfer(address indexed from, address indexed to, uint256 value);
    event TaxCharged(address indexed from, address indexed treasury, uint256 taxAmount);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // Custom errors
    error InsufficientBalance();
    error InsufficientAllowance();
    error NotOwner();

    // Modifiers
    modifier onlyOwner() {
        if (msg.sender != _owner) revert NotOwner();
        _;
    }

    /// @notice Initializes the contract with the treasury wallet and initial supply.
    /// @param initialTreasuryWallet The address of the treasury wallet.
    /// @param initialSupply The initial supply of tokens.
    constructor(address initialTreasuryWallet, uint256 initialSupply) {
        _owner = msg.sender;
        treasuryWallet = initialTreasuryWallet;
        _totalSupply = initialSupply;
        _balances[msg.sender] = initialSupply;
        emit OwnershipTransferred(address(0), _owner);
    }

    /// @notice Transfers tokens from the caller to the specified address, charging a 3% tax that is sent to the treasury wallet.
    /// @param to The address to transfer tokens to.
    /// @param amount The amount of tokens to transfer.
    /// @return success True if the transfer was successful.
    function transfer(address to, uint256 amount) public returns (bool success) {
        uint256 taxAmount = (amount * 3) / 100;
        uint256 transferAmount = amount - taxAmount;

        if (_balances[msg.sender] < amount) revert InsufficientBalance();

        _balances[msg.sender] -= amount;
        _balances[to] += transferAmount;
        _balances[treasuryWallet] += taxAmount;

        emit Transfer(msg.sender, to, transferAmount);
        emit TaxCharged(msg.sender, treasuryWallet, taxAmount);

        return true;
    }

    /// @notice Transfers ownership of the contract to a new account (`newOwner`).
    /// @param newOwner The address of the new owner.
    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "New owner is the zero address");
        emit OwnershipTransferred(_owner, newOwner);
        _owner = newOwner;
    }

    /// @notice Returns the total supply of tokens.
    /// @return The total supply of tokens.
    function totalSupply() public view returns (uint256) {
        return _totalSupply;
    }

    /// @notice Returns the balance of the specified address.
    /// @param account The address to query the balance of.
    /// @return The balance of the specified address.
    function balanceOf(address account) public view returns (uint256) {
        return _balances[account];
    }

    /// @notice Returns the remaining number of tokens that `spender` will be allowed to spend on behalf of `owner`.
    /// @param owner The address which owns the funds.
    /// @param spender The address which will spend the funds.
    /// @return The remaining number of tokens.
    function allowance(address owner, address spender) public view returns (uint256) {
        return _allowances[owner][spender];
    }

    /// @notice Approves the passed address to spend the specified amount of tokens on behalf of msg.sender.
    /// @param spender The address which will spend the funds.
    /// @param amount The amount of tokens to be spent.
    /// @return success True if the operation was successful.
    function approve(address spender, uint256 amount) public returns (bool success) {
        _allowances[msg.sender][spender] = amount;
        emit Transfer(msg.sender, spender, amount);
        return true;
    }

    /// @notice Transfers tokens from one address to another using the allowance mechanism.
    /// @param from The address to send tokens from.
    /// @param to The address to send tokens to.
    /// @param amount The amount of tokens to send.
    /// @return success True if the operation was successful.
    function transferFrom(address from, address to, uint256 amount) public returns (bool success) {
        if (_balances[from] < amount) revert InsufficientBalance();
        if (_allowances[from][msg.sender] < amount) revert InsufficientAllowance();

        uint256 taxAmount = (amount * 3) / 100;
        uint256 transferAmount = amount - taxAmount;

        _balances[from] -= amount;
        _balances[to] += transferAmount;
        _balances[treasuryWallet] += taxAmount;
        _allowances[from][msg.sender] -= amount;

        emit Transfer(from, to, transferAmount);
        emit TaxCharged(from, treasuryWallet, taxAmount);

        return true;
    }
}
