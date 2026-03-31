// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Escrow {
    address public payer;
    address public payee;
    address public arbiter;
    uint256 public amount;
    bool public payerApproval;
    bool public payeeApproval;

    constructor(address _payee, address _arbiter) payable {
        require(msg.value > 0, "Amount must be greater than zero");
        payer = msg.sender;
        payee = _payee;
        arbiter = _arbiter;
        amount = msg.value;
    }

    modifier onlyPayer() {
        require(msg.sender == payer, "Only payer can call this function");
        _;
    }

    modifier onlyPayee() {
        require(msg.sender == payee, "Only payee can call this function");
        _;
    }

    modifier onlyArbiter() {
        require(msg.sender == arbiter, "Only arbiter can call this function");
        _;
    }

    function approveByPayer() external onlyPayer {
        payerApproval = true;
        releaseFunds();
    }

    function approveByPayee() external onlyPayee {
        payeeApproval = true;
        releaseFunds();
    }

    function releaseFunds() internal {
        if (payerApproval && payeeApproval) {
            payable(payee).transfer(amount);
            resetContract();
        }
    }

    function resetContract() internal {
        payerApproval = false;
        payeeApproval = false;
        amount = 0;
    }

    function refund() external onlyArbiter {
        require(!payerApproval || !payeeApproval, "Cannot refund after approval");
        payable(payer).transfer(amount);
        resetContract();
    }
}