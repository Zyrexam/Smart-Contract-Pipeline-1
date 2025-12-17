// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title EtherVault
/// @notice A contract where users can deposit Ether and the owner can withdraw it.
contract EtherVault {
    /// @notice Address of the contract owner
    address private owner;

    /// @notice Mapping to store the balance of each user
    mapping(address => uint256) private balances;

    /// @notice Event emitted when a user deposits Ether
    /// @param user The address of the user who deposited Ether
    /// @param amount The amount of Ether deposited
    event Deposit(address indexed user, uint256 amount);

    /// @notice Event emitted when the owner withdraws Ether
    /// @param owner The address of the owner who withdrew Ether
    /// @param amount The amount of Ether withdrawn
    event Withdrawal(address indexed owner, uint256 amount);

    /// @notice Custom error for unauthorized access
    error Unauthorized();

    /// @notice Custom error for insufficient balance
    error InsufficientBalance();

    /// @dev Sets the deployer as the initial owner
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows users to deposit Ether into the contract
    /// @dev The deposited amount is added to the user's balance
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /// @notice Allows the owner to withdraw a specified amount of Ether from the contract
    /// @param amount The amount of Ether to withdraw
    function withdraw(uint256 amount) external {
        if (msg.sender != owner) revert Unauthorized();
        if (address(this).balance < amount) revert InsufficientBalance();

        // Effects
        emit Withdrawal(owner, amount);

        // Interactions
        payable(owner).transfer(amount);
    }

    /// @notice Returns the balance of the specified user
    /// @param user The address of the user
    /// @return The balance of the user
    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}
