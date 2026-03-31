// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Crowdfunding Contract
/// @notice This contract allows users to contribute funds towards a funding goal.
/// @dev Implements a basic crowdfunding mechanism with contribution, withdrawal, and refund functionalities.
contract Crowdfunding {
    /// @notice The funding goal for the campaign.
    uint256 public fundingGoal;

    /// @notice The total funds contributed to the campaign.
    uint256 public totalFunds;

    /// @notice The deadline for the campaign.
    uint256 public deadline;

    /// @notice The address of the campaign owner.
    address public owner;

    /// @dev Mapping to track contributions by address.
    mapping(address => uint256) private contributions;

    /// @dev Custom error for when the funding goal is not reached.
    error FundingGoalNotReached();

    /// @dev Custom error for when the deadline has passed.
    error DeadlinePassed();

    /// @dev Custom error for when the caller is not the owner.
    error NotOwner();

    /// @dev Custom error for when there are no funds to withdraw.
    error NoFundsToWithdraw();

    /// @dev Custom error for when there are no funds to refund.
    error NoFundsToRefund();

    /// @notice Event emitted when a contribution is received.
    /// @param contributor The address of the contributor.
    /// @param amount The amount contributed.
    event ContributionReceived(address indexed contributor, uint256 amount);

    /// @notice Event emitted when funds are withdrawn by the owner.
    /// @param owner The address of the owner.
    /// @param amount The amount withdrawn.
    event FundsWithdrawn(address indexed owner, uint256 amount);

    /// @notice Event emitted when a refund is issued to a contributor.
    /// @param contributor The address of the contributor.
    /// @param amount The amount refunded.
    event RefundIssued(address indexed contributor, uint256 amount);

    /// @notice Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @notice Constructor to initialize the crowdfunding campaign.
    /// @param _fundingGoal The funding goal for the campaign.
    /// @param _duration The duration of the campaign in seconds.
    constructor(uint256 _fundingGoal, uint256 _duration) {
        owner = msg.sender;
        fundingGoal = _fundingGoal;
        deadline = block.timestamp + _duration;
    }

    /// @notice Allows users to contribute funds to the campaign.
    /// @param amount The amount to contribute.
    function contribute(uint256 amount) external payable {
        if (block.timestamp > deadline) revert DeadlinePassed();
        require(msg.value == amount, "Incorrect amount sent");

        contributions[msg.sender] += amount;
        totalFunds += amount;

        emit ContributionReceived(msg.sender, amount);
    }

    /// @notice Allows the owner to withdraw funds if the funding goal is reached.
    function withdrawFunds() external onlyOwner {
        if (totalFunds < fundingGoal) revert FundingGoalNotReached();
        if (totalFunds == 0) revert NoFundsToWithdraw();

        uint256 amount = totalFunds;
        totalFunds = 0;

        (bool success, ) = owner.call{value: amount}("");
        require(success, "Transfer failed");

        emit FundsWithdrawn(owner, amount);
    }

    /// @notice Allows contributors to get a refund if the funding goal is not reached by the deadline.
    function refund() external {
        if (block.timestamp <= deadline) revert DeadlinePassed();
        uint256 contributedAmount = contributions[msg.sender];
        if (contributedAmount == 0) revert NoFundsToRefund();

        contributions[msg.sender] = 0;
        totalFunds -= contributedAmount;

        (bool success, ) = msg.sender.call{value: contributedAmount}("");
        require(success, "Refund failed");

        emit RefundIssued(msg.sender, contributedAmount);
    }

    /// @notice Checks if the funding goal has been reached.
    /// @return goalReached True if the funding goal is reached, false otherwise.
    function checkGoalReached() external view returns (bool goalReached) {
        return totalFunds >= fundingGoal;
    }
}