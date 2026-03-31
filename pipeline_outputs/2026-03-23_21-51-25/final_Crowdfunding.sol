// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Crowdfunding Contract
/// @notice This contract allows users to contribute funds towards a funding goal within a specified deadline.
/// @dev Implements role-based access control for the owner and uses custom errors for gas efficiency.
contract Crowdfunding {
    /// @notice The funding goal for the campaign.
    uint256 public fundingGoal;
    
    /// @notice The total funds contributed to the campaign.
    uint256 public totalFunds;
    
    /// @notice The deadline for the campaign.
    uint256 public deadline;
    
    /// @notice The owner of the contract.
    address public owner;

    /// @dev Mapping to track contributions by address.
    mapping(address => uint256) private contributions;

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for contributions after the deadline.
    error ContributionPeriodEnded();

    /// @dev Custom error for insufficient funds for refund.
    error InsufficientFunds();

    /// @dev Custom error for failed withdrawal.
    error WithdrawalFailed();

    /// @dev Event emitted when a contribution is received.
    event ContributionReceived(address indexed contributor, uint256 amount);

    /// @dev Event emitted when the funding goal is reached.
    event GoalReached();

    /// @dev Event emitted when funds are withdrawn by the owner.
    event FundsWithdrawn(address indexed owner, uint256 amount);

    /// @dev Event emitted when a refund is issued.
    event RefundIssued(address indexed contributor, uint256 amount);

    /// @notice Initializes the crowdfunding contract with a funding goal and deadline.
    /// @param _fundingGoal The funding goal for the campaign.
    /// @param _duration The duration (in seconds) for the campaign.
    constructor(uint256 _fundingGoal, uint256 _duration) {
        owner = msg.sender;
        fundingGoal = _fundingGoal;
        deadline = block.timestamp + _duration;
    }

    /// @notice Allows users to contribute funds to the campaign.
    /// @param amount The amount of funds to contribute.
    function contribute(uint256 amount) external payable {
        if (block.timestamp > deadline) revert ContributionPeriodEnded();
        require(msg.value == amount, "Incorrect amount sent");

        contributions[msg.sender] += amount;
        totalFunds += amount;

        emit ContributionReceived(msg.sender, amount);

        if (totalFunds >= fundingGoal) {
            emit GoalReached();
        }
    }

    /// @notice Checks if the funding goal has been reached.
    /// @return goalReached True if the funding goal is reached, false otherwise.
    function checkGoalReached() external view returns (bool goalReached) {
        return totalFunds >= fundingGoal;
    }

    /// @notice Allows the owner to withdraw funds if the goal is reached.
    function withdrawFunds() external {
        if (msg.sender != owner) revert Unauthorized();
        if (totalFunds < fundingGoal) revert InsufficientFunds();

        uint256 amount = address(this).balance;
        (bool success, ) = owner.call{value: amount}("");
        if (!success) revert WithdrawalFailed();

        emit FundsWithdrawn(owner, amount);
    }

    /// @notice Refunds contributors if the funding goal is not reached by the deadline.
    function refund() external {
        if (block.timestamp <= deadline) revert ContributionPeriodEnded();
        if (totalFunds >= fundingGoal) revert InsufficientFunds();

        uint256 contributedAmount = contributions[msg.sender];
        contributions[msg.sender] = 0;

        (bool success, ) = msg.sender.call{value: contributedAmount}("");
        if (!success) revert WithdrawalFailed();

        emit RefundIssued(msg.sender, contributedAmount);
    }
}