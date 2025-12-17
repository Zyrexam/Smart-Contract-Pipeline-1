// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title TaxToken - A token that charges a 3% tax on every transfer and sends the tax to the treasury wallet.
/// @dev This contract implements a custom ERC20 token with a tax mechanism.
contract TaxToken {
    string public name = "TaxToken";
    string public symbol = "TAX";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    address private owner;
    address private treasuryWallet;
    uint256 private taxRate = 3;

    mapping(address => uint256) private balances;
    mapping(address => mapping(address => uint256)) private allowances;

    /// @dev Emitted when a tax is charged on a transfer.
    /// @param from The address from which the tokens are transferred.
    /// @param to The address to which the tokens are transferred.
    /// @param taxAmount The amount of tax charged.
    event TaxCharged(address indexed from, address indexed to, uint256 taxAmount);

    /// @dev Emitted when tokens are transferred.
    /// @param from The address from which the tokens are transferred.
    /// @param to The address to which the tokens are transferred.
    /// @param value The amount of tokens transferred.
    event Transfer(address indexed from, address indexed to, uint256 value);

    /// @dev Emitted when an approval is made.
    /// @param owner The address which owns the tokens.
    /// @param spender The address which is allowed to spend the tokens.
    /// @param value The amount of tokens approved for spending.
    event Approval(address indexed owner, address indexed spender, uint256 value);

    /// @dev Custom error for insufficient balance.
    error InsufficientBalance();

    /// @dev Custom error for insufficient allowance.
    error InsufficientAllowance();

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @dev Constructor to set the initial supply and treasury wallet.
    /// @param _initialSupply The initial supply of tokens.
    /// @param _treasuryWallet The address of the treasury wallet.
    constructor(uint256 _initialSupply, address _treasuryWallet) {
        owner = msg.sender;
        treasuryWallet = _treasuryWallet;
        totalSupply = _initialSupply * 10 ** uint256(decimals);
        balances[msg.sender] = totalSupply;
        emit Transfer(address(0), msg.sender, totalSupply);
    }

    /// @dev Transfers tokens from the caller to the specified address, deducting a 3% tax and sending it to the treasury wallet.
    /// @param to The address to which the tokens are transferred.
    /// @param amount The amount of tokens to transfer.
    /// @return success A boolean indicating the success of the transfer.
    function transfer(address to, uint256 amount) external returns (bool success) {
        uint256 taxAmount = (amount * taxRate) / 100;
        uint256 netAmount = amount - taxAmount;

        if (balances[msg.sender] < amount) revert InsufficientBalance();

        balances[msg.sender] -= amount;
        balances[to] += netAmount;
        balances[treasuryWallet] += taxAmount;

        emit Transfer(msg.sender, to, netAmount);
        emit TaxCharged(msg.sender, to, taxAmount);

        return true;
    }

    /// @dev Returns the balance of the specified address.
    /// @param account The address to query the balance of.
    /// @return The balance of the specified address.
    function balanceOf(address account) external view returns (uint256) {
        return balances[account];
    }

    /// @dev Approves the specified address to spend a certain amount of tokens on behalf of the caller.
    /// @param spender The address which is allowed to spend the tokens.
    /// @param amount The amount of tokens to approve.
    /// @return success A boolean indicating the success of the approval.
    function approve(address spender, uint256 amount) external returns (bool success) {
        allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    /// @dev Transfers tokens from one address to another using an allowance.
    /// @param from The address from which the tokens are transferred.
    /// @param to The address to which the tokens are transferred.
    /// @param amount The amount of tokens to transfer.
    /// @return success A boolean indicating the success of the transfer.
    function transferFrom(address from, address to, uint256 amount) external returns (bool success) {
        uint256 taxAmount = (amount * taxRate) / 100;
        uint256 netAmount = amount - taxAmount;

        if (balances[from] < amount) revert InsufficientBalance();
        if (allowances[from][msg.sender] < amount) revert InsufficientAllowance();

        balances[from] -= amount;
        balances[to] += netAmount;
        balances[treasuryWallet] += taxAmount;
        allowances[from][msg.sender] -= amount;

        emit Transfer(from, to, netAmount);
        emit TaxCharged(from, to, taxAmount);

        return true;
    }

    /// @dev Returns the remaining number of tokens that the spender is allowed to spend on behalf of the owner.
    /// @param owner The address which owns the tokens.
    /// @param spender The address which is allowed to spend the tokens.
    /// @return The remaining number of tokens.
    function allowance(address owner, address spender) external view returns (uint256) {
        return allowances[owner][spender];
    }
}
