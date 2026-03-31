// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Crowdfunding Contract
/// @notice A contract for managing a crowdfunding campaign where users can contribute funds until a funding goal is reached.
contract Crowdfunding {
    /// @notice The funding goal for the campaign
    uint256 public fundingGoal;
    
    /// @notice The total funds raised in the campaign
    uint256 public totalFunds;
    
    /// @notice The deadline for the campaign
    uint256 public deadline;
    
    /// @notice The owner of the contract
    address public owner;
    
    /// @dev Mapping to track contributions of each address
    mapping(address => uint256) private contributions;
    
    /// @dev Custom error for when the caller is not the owner
    error NotOwner();
    
    /// @dev Custom error for when the funding goal is not reached
    error GoalNotReached();
    
    /// @dev Custom error for when the deadline has not passed
    error DeadlineNotPassed();
    
    /// @dev Custom error for when the contribution amount is zero
    error ZeroContribution();
    
    /// @dev Custom error for when the refund is not possible
    error RefundNotPossible();
    
    /// @notice Event emitted when a contribution is received
    /// @param contributor The address of the contributor
    /// @param amount The amount contributed
    event ContributionReceived(address indexed contributor, uint256 amount);
    
    /// @notice Event emitted when the funding goal is reached
    /// @param totalFunds The total funds raised
    event GoalReached(uint256 totalFunds);
    
    /// @notice Event emitted when funds are withdrawn by the owner
    /// @param amount The amount withdrawn
    event FundsWithdrawn(uint256 amount);
    
    /// @notice Event emitted when a refund is issued to a contributor
    /// @param contributor The address of the contributor
    /// @param amount The amount refunded
    event RefundIssued(address indexed contributor, uint256 amount);
    
    /// @notice Modifier to restrict functions to the owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }
    
    /// @notice Constructor to initialize the crowdfunding contract
    /// @param _fundingGoal The funding goal for the campaign
    /// @param _duration The duration of the campaign in seconds
    constructor(uint256 _fundingGoal, uint256 _duration) {
        owner = msg.sender;
        fundingGoal = _fundingGoal;
        deadline = block.timestamp + _duration;
    }
    
    /// @notice Allows users to contribute funds to the campaign
    function contribute() external payable {
        if (msg.value == 0) revert ZeroContribution();
        if (block.timestamp > deadline) revert DeadlineNotPassed();
        
        contributions[msg.sender] += msg.value;
        totalFunds += msg.value;
        
        emit ContributionReceived(msg.sender, msg.value);
        
        if (totalFunds >= fundingGoal) {
            emit GoalReached(totalFunds);
        }
    }
    
    /// @notice Checks if the funding goal has been reached
    /// @return goalReached True if the funding goal is reached, false otherwise
    function checkGoalReached() external view returns (bool goalReached) {
        return totalFunds >= fundingGoal;
    }
    
    /// @notice Allows the owner to withdraw funds if the goal is reached
    function withdrawFunds() external onlyOwner {
        if (totalFunds < fundingGoal) revert GoalNotReached();
        
        uint256 amount = address(this).balance;
        payable(owner).transfer(amount);
        
        emit FundsWithdrawn(amount);
    }
    
    /// @notice Refunds contributors if the funding goal is not reached by the deadline
    function refund() external {
        if (block.timestamp <= deadline) revert DeadlineNotPassed();
        if (totalFunds >= fundingGoal) revert RefundNotPossible();
        
        uint256 contributedAmount = contributions[msg.sender];
        if (contributedAmount == 0) revert RefundNotPossible();
        
        contributions[msg.sender] = 0;
        payable(msg.sender).transfer(contributedAmount);
        
        emit RefundIssued(msg.sender, contributedAmount);
    }
}