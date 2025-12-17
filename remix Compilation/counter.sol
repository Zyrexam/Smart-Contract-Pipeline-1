// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Counter - A simple Counter smart contract with increment, decrement, and reset functions.
/// @dev This contract allows incrementing, decrementing, and resetting a counter. Only the owner can perform these actions.
contract Counter {
    /// @notice The current count value.
    uint256 private count;

    /// @notice The address of the contract owner.
    address private owner;

    /// @dev Emitted when the count is incremented.
    /// @param newCount The new count value after increment.
    event Incremented(uint256 newCount);

    /// @dev Emitted when the count is decremented.
    /// @param newCount The new count value after decrement.
    event Decremented(uint256 newCount);

    /// @dev Emitted when the count is reset.
    /// @param newCount The new count value after reset.
    event Reset(uint256 newCount);

    /// @dev Custom error for unauthorized access.
    error NotOwner();

    /// @dev Custom error for underflow when decrementing.
    error Underflow();

    /// @dev Sets the deployer as the initial owner.
    constructor() {
        owner = msg.sender;
    }

    /// @dev Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @notice Increases the count by 1.
    /// @dev Emits an Incremented event.
    function increment() external onlyOwner {
        count += 1;
        emit Incremented(count);
    }

    /// @notice Decreases the count by 1.
    /// @dev Emits a Decremented event. Reverts if count is 0.
    function decrement() external onlyOwner {
        if (count == 0) revert Underflow();
        count -= 1;
        emit Decremented(count);
    }

    /// @notice Resets the count to 0.
    /// @dev Emits a Reset event.
    function reset() external onlyOwner {
        count = 0;
        emit Reset(count);
    }

    /// @notice Returns the current count value.
    /// @return The current count.
    function getCount() external view returns (uint256) {
        return count;
    }
}
