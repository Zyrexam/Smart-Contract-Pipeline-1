// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Crowdfunding Smart Contract
/// @notice A contract for managing a crowdfunding campaign where users can contribute funds until a funding goal is reached.
contract Crowdfunding {
    /// @notice The funding goal for the crowdfunding campaign
    uint256 public fundingGoal;

    /// @notice The total funds contributed to the campaign
    uint256 public totalFunds;

    /// @notice Indicates if the funding goal has been reached
    bool public isGoalReached;

    /// @notice Event emitted when a contribution is received
    /// @param contributor The address of the contributor
    /// @param amount The amount contributed
    event ContributionReceived(address indexed contributor, uint256 amount);

    /// @notice Event emitted when the funding goal is reached
    event GoalReached();

    /// @dev Custom error for when the funding goal is already reached
    error GoalAlreadyReached();

    /// @dev Custom error for when the contribution amount is zero
    error ZeroContribution();

    /// @dev Modifier to ensure the funding goal is not yet reached
    modifier goalNotReached() {
        if (isGoalReached) revert GoalAlreadyReached();
        _;
    }

    /// @notice Constructor to set the funding goal
    /// @param _fundingGoal The funding goal for the campaign
    constructor(uint256 _fundingGoal) {
        fundingGoal = _fundingGoal;
    }

    /// @notice Allows users to contribute funds to the crowdfunding campaign
    /// @param amount The amount to contribute
    function contribute(uint256 amount) external goalNotReached {
        if (amount == 0) revert ZeroContribution();

        totalFunds += amount;
        emit ContributionReceived(msg.sender, amount);

        // Check if the funding goal has been reached
        if (totalFunds >= fundingGoal) {
            isGoalReached = true;
            emit GoalReached();
        }
    }

    /// @notice Checks if the funding goal has been reached
    /// @return goalReached True if the funding goal is reached, false otherwise
    function checkGoalReached() external view returns (bool goalReached) {
        return isGoalReached;
    }
}
