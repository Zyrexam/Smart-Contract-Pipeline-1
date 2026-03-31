// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Crowdfunding {
    uint256 private fundingGoal;
    uint256 private raisedFunds;

    // Event to trigger when funds are contributed
    event FundsContributed(uint256 amount);

    constructor(uint256 _fundingGoal) {
        this.fundingGoal = _fundingGoal;
    }

    function contribute() public payable {
        require(msg.value >= 1, "Minimum contribution amount not met");

        // Increment the raised funds counter
        raisedFunds += msg.value;

        // Emit event to trigger the event listener
        emit FundsContributed(msg.value);

        // Send funds to the contract owner
        payable(address(msg.sender)).transfer(msg.value);
    }
}