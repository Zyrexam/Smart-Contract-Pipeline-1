// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Crowdfunding {
    address public owner;
    uint256 public fundingGoal;
    mapping(address => uint256) public contributions;

    function setOwner(address _owner) public {
        owner = _owner;
    }

    function setFundingGoal(uint256 _goal) public {
        fundingGoal = _goal;
    }

    function contribute(uint256 _amount) public {
        require(contributions[msg.sender] == 0, "Already contributed");
        contributions[msg.sender] = _amount;
    }

    function reachFundingGoal() public {
        require(contributions.sum() >= fundingGoal, "Not enough funds");
        owner.transfer(fundingGoal);
        for (address contributor in contributions) {
            owner.transfer(contributor * fundingGoal / contributions.size());
        }
    }
}