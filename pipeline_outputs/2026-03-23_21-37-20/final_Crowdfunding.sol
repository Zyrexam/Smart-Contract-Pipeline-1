// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Crowdfunding Smart Contract
/// @notice This contract allows users to contribute funds towards a funding goal.
/// @dev Implements role-based access control for the owner.
contract Crowdfunding {
    address public owner;
    uint256 public fundingGoal;
    uint256 public totalFunds;
    bool public isGoalReached;

    /// @notice Emitted when a contribution is received.
    /// @param contributor The address of the contributor.
    /// @param amount The amount contributed.
    event ContributionReceived(address indexed contributor, uint256 amount);

    /// @notice Emitted when the funding goal is reached.
    /// @param totalFunds The total funds raised.
    event GoalReached(uint256 totalFunds);

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for invalid operations.
    error InvalidOperation();

    /// @dev Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @notice Initializes the contract setting the deployer as the initial owner.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows users to contribute funds to the campaign.
    /// @param amount The amount to contribute.
    function contribute(uint256 amount) external payable {
        if (msg.value != amount) revert InvalidOperation();

        totalFunds += amount;
        emit ContributionReceived(msg.sender, amount);

        // Automatically check if the funding goal is reached
        if (totalFunds >= fundingGoal && !isGoalReached) {
            isGoalReached = true;
            emit GoalReached(totalFunds);
        }
    }

    /// @notice Sets the funding goal for the campaign.
    /// @param goal The new funding goal.
    /// @dev Only callable by the owner.
    function setGoal(uint256 goal) external onlyOwner {
        fundingGoal = goal;
    }

    /// @notice Allows the owner to withdraw funds if the goal is reached.
    /// @dev Only callable by the owner.
    function withdrawFunds() external onlyOwner {
        if (!isGoalReached) revert InvalidOperation();

        uint256 amount = address(this).balance;
        (bool success, ) = owner.call{value: amount}("");
        if (!success) revert InvalidOperation();
    }

    /// @notice Checks if the funding goal has been reached.
    /// @return goalReached True if the funding goal is reached, false otherwise.
    function checkGoalReached() external view returns (bool goalReached) {
        return isGoalReached;
    }
}