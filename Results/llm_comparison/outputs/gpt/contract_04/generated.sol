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

    function contribute() public payable {
        require(!goalReached, "Funding goal has already been reached");
        require(msg.value > 0, "Contribution must be greater than 0");

        contributions[msg.sender] += msg.value;
        totalFunds += msg.value;

        emit ContributionReceived(msg.sender, msg.value);

        if (totalFunds >= fundingGoal) {
            goalReached = true;
            emit GoalReached(totalFunds);
        }
    }

    function withdrawFunds() public onlyOwner {
        require(goalReached, "Funding goal not reached yet");
        payable(owner).transfer(address(this).balance);
    }

    function getContribution(address contributor) public view returns (uint) {
        return contributions[contributor];
    }
}