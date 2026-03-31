// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Crowdfunding {
    address private owner;
    uint256 private fundingGoal;
    uint256 private totalContributions;
    mapping(address => uint256) private contributions;

    constructor(uint256 _fundingGoal) public {
        owner = msg.sender;
        fundingGoal = _fundingGoal;
    }

    function contribute() public payable {
        require(msg.value > 0, "Invalid contribution");
        contributions[msg.sender] += msg.value;
        totalContributions += msg.value;
    }

    function checkFundingGoalReached() public view returns (bool) {
        return totalContributions >= fundingGoal;
    }

    function getTotalContributions() public view returns (uint256) {
        return totalContributions;
    }

    function getContributions(address _contributor) public view returns (uint256) {
        return contributions[_contributor];
    }
}