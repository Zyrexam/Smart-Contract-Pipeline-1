// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Crowdfunding {
    address public owner;
    uint public fundingGoal;
    uint public totalFunds;
    bool public goalReached;
    mapping(address => uint) public contributions;

    event ContributionReceived(address contributor, uint amount);
    event GoalReached(uint totalFunds);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor(uint _fundingGoal) {
        owner = msg.sender;
        fundingGoal = _fundingGoal;
        totalFunds = 0;
        goalReached = false;
    }

    function contribute() external payable {
        require(!goalReached, "Funding goal already reached");
        require(msg.value > 0, "Contribution must be greater than zero");

        contributions[msg.sender] += msg.value;
        totalFunds += msg.value;

        emit ContributionReceived(msg.sender, msg.value);

        if (totalFunds >= fundingGoal) {
            goalReached = true;
            emit GoalReached(totalFunds);
        }
    }

    function withdrawFunds() external onlyOwner {
        require(goalReached, "Funding goal not reached yet");
        payable(owner).transfer(totalFunds);
    }

    function refund() external {
        require(!goalReached, "Cannot refund after goal is reached");
        uint contributedAmount = contributions[msg.sender];
        require(contributedAmount > 0, "No contributions to refund");

        contributions[msg.sender] = 0;
        payable(msg.sender).transfer(contributedAmount);
    }
}