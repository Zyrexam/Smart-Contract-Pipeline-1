// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Crowdfunding Smart Contract
/// @notice This contract allows users to contribute funds towards a funding goal.
/// @dev Implements role-based access control for owner functions.
contract Crowdfunding {
    /// @notice The funding goal for the campaign.
    uint256 public fundingGoal;

    /// @notice The total funds contributed to the campaign.
    uint256 public totalFunds;

    /// @notice Indicates whether the funding goal has been reached.
    bool public isGoalReached;

    /// @notice Address of the contract owner.
    address public owner;

    /// @dev Mapping to track contributions by address.
    mapping(address => uint256) private contributions;

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for insufficient funds.
    error InsufficientFunds();

    /// @dev Custom error for goal already reached.
    error GoalAlreadyReached();

    /// @dev Custom error for invalid goal.
    error InvalidGoal();

    /// @notice Event emitted when a contribution is received.
    /// @param contributor The address of the contributor.
    /// @param amount The amount contributed.
    event ContributionReceived(address indexed contributor, uint256 amount);

    /// @notice Event emitted when the funding goal is reached.
    /// @param totalFunds The total funds collected.
    event GoalReached(uint256 totalFunds);

    /// @dev Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @notice Constructor to set the initial owner of the contract.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows users to contribute funds to the campaign.
    /// @param amount The amount to contribute.
    function contribute(uint256 amount) external payable {
        if (isGoalReached) revert GoalAlreadyReached();
        if (msg.value != amount) revert InsufficientFunds();

        totalFunds += amount;
        contributions[msg.sender] += amount;

        emit ContributionReceived(msg.sender, amount);

        // Check if the funding goal is reached
        if (totalFunds >= fundingGoal) {
            isGoalReached = true;
            emit GoalReached(totalFunds);
        }
    }

    /// @notice Sets the funding goal for the campaign.
    /// @param goal The new funding goal.
    function setGoal(uint256 goal) external onlyOwner {
        if (goal <= 0) revert InvalidGoal();
        fundingGoal = goal;
    }

    /// @notice Allows the owner to withdraw funds if the goal is reached.
    function withdrawFunds() external onlyOwner {
        if (!isGoalReached) revert GoalAlreadyReached();
        payable(owner).transfer(totalFunds);
        totalFunds = 0;
    }

    /// @notice Checks if the funding goal has been reached.
    /// @return goalReached True if the funding goal is reached, false otherwise.
    function checkGoalReached() external view returns (bool goalReached) {
        return isGoalReached;
    }
}