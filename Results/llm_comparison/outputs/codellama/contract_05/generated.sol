// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Escrow {
    address private beneficiary;
    address private agent;
    uint256 private amount;
    bool private approvedByBeneficiary;
    bool private approvedByAgent;

    constructor(address _beneficiary, address _agent) public {
        beneficiary = _beneficiary;
        agent = _agent;
    }

    function deposit(uint256 _amount) public payable {
        require(msg.sender == beneficiary || msg.sender == agent, "Only the beneficiary or the agent can deposit funds");
        amount += _amount;
    }

    function approveByBeneficiary() public {
        require(msg.sender == beneficiary, "Only the beneficiary can approve the transaction");
        approvedByBeneficiary = true;
    }

    function approveByAgent() public {
        require(msg.sender == agent, "Only the agent can approve the transaction");
        approvedByAgent = true;
    }

    function withdraw() public {
        require(approvedByBeneficiary && approvedByAgent, "Both parties must approve the transaction before it can be withdrawn");
        beneficiary.transfer(amount);
        amount = 0;
    }
}