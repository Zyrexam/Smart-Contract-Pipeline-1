// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Crowdfunding {
    uint256 public goal;
    uint256 public raisedFunds;
    mapping(address => uint256) public contributions;

    constructor(uint256 _goal) {
        goal = _goal;
        raisedFunds = 0;
    }

    function contribute() public payable {
        require(msg.value > 0, "Amount must be greater than zero.");
        contributions[msg.sender] += msg.value;
        raisedFunds += msg.value;
        if (raisedFunds >= goal) {
            emit FundingReached();
        }
    }

    event FundingReached();
}