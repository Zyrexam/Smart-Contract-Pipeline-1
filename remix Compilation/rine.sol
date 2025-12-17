// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RateLimitedTokenVault
/// @notice A smart contract that acts as a token vault with rate-limited withdrawals, allowing withdrawals once every 24 hours.
contract RateLimitedTokenVault {
    /// @notice The last time a withdrawal was made
    uint256 private lastWithdrawalTime;

    /// @notice The balance of tokens in the vault
    uint256 public tokenBalance;

    /// @notice The owner of the vault
    address public owner;

    /// @notice Emitted when a withdrawal is made
    /// @param amount The amount withdrawn
    /// @param timestamp The time of withdrawal
    event Withdrawal(uint256 amount, uint256 timestamp);

    /// @notice Custom error for unauthorized access
    error Unauthorized();

    /// @notice Custom error for rate limit violation
    error RateLimitExceeded();

    /// @notice Modifier to restrict access to the owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @notice Modifier to ensure withdrawals can only occur once every 24 hours
    modifier rateLimit() {
        if (block.timestamp < lastWithdrawalTime + 24 hours) revert RateLimitExceeded();
        _;
    }

    /// @notice Constructor to set the initial owner of the vault
    /// @param _owner The address of the owner
    constructor(address _owner) {
        owner = _owner;
    }

    /// @notice Allows the owner to withdraw tokens from the vault, but only once every 24 hours.
    /// @param amount The amount to withdraw
    function withdraw(uint256 amount) external onlyOwner rateLimit {
        require(amount <= tokenBalance, "Insufficient balance");
        tokenBalance -= amount;
        _setWithdrawalTime(block.timestamp);
        emit Withdrawal(amount, block.timestamp);
    }

    /// @notice Sets the last withdrawal time to the current block timestamp.
    /// @param time The current block timestamp
    function _setWithdrawalTime(uint256 time) private {
        lastWithdrawalTime = time;
    }

    /// @notice Function to deposit tokens into the vault
    /// @param amount The amount to deposit
    function deposit(uint256 amount) external onlyOwner {
        tokenBalance += amount;
    }
}
