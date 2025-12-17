// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Ether Deposit and Withdrawal Contract
/// @notice This contract allows users to deposit Ether and the owner to withdraw it.
contract EtherVault {
    address private owner;
    mapping(address => uint256) private balances;

    /// @dev Emitted when a user deposits Ether.
    /// @param user The address of the user who deposited Ether.
    /// @param amount The amount of Ether deposited.
    event Deposit(address indexed user, uint256 amount);

    /// @dev Emitted when the owner withdraws Ether.
    /// @param owner The address of the owner who withdrew Ether.
    /// @param amount The amount of Ether withdrawn.
    event Withdrawal(address indexed owner, uint256 amount);

    /// @dev Error for unauthorized access.
    error Unauthorized();

    /// @dev Error for insufficient balance.
    error InsufficientBalance();

    /// @dev Sets the deployer as the owner of the contract.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows users to deposit Ether into the contract.
    /// @dev The deposited amount is added to the user's balance.
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /// @notice Allows the owner to withdraw a specified amount of Ether from the contract.
    /// @param amount The amount of Ether to withdraw.
    /// @dev Only the owner can call this function.
    function withdraw(uint256 amount) external {
        if (msg.sender != owner) revert Unauthorized();
        if (address(this).balance < amount) revert InsufficientBalance();

        // Effects
        balances[owner] += amount;

        // Interactions
        (bool success, ) = owner.call{value: amount}("");
        require(success, "Transfer failed");

        emit Withdrawal(owner, amount);
    }

    /// @notice Returns the balance of the specified user.
    /// @param user The address of the user.
    /// @return The balance of the user.
    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}
