// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Escrow {
    address public payer;
    address public payee;
    address public arbiter;
    uint256 public amount;
    bool public payerApproval;
    bool public payeeApproval;

    enum State { AWAITING_PAYMENT, AWAITING_APPROVAL, COMPLETE }
    State public currentState;

    modifier onlyPayer() {
        require(msg.sender == payer, "Only payer can call this function.");
        _;
    }

    modifier onlyPayee() {
        require(msg.sender == payee, "Only payee can call this function.");
        _;
    }

    modifier onlyArbiter() {
        require(msg.sender == arbiter, "Only arbiter can call this function.");
        _;
    }

    modifier inState(State expectedState) {
        require(currentState == expectedState, "Invalid state.");
        _;
    }

    constructor(address _payee, address _arbiter) payable {
        payer = msg.sender;
        payee = _payee;
        arbiter = _arbiter;
        amount = msg.value;
        currentState = State.AWAITING_PAYMENT;
    }

    function deposit() external payable onlyPayer inState(State.AWAITING_PAYMENT) {
        require(msg.value == amount, "Incorrect deposit amount.");
        currentState = State.AWAITING_APPROVAL;
    }

    function approveByPayer() external onlyPayer inState(State.AWAITING_APPROVAL) {
        payerApproval = true;
        finalizeTransaction();
    }

    function approveByPayee() external onlyPayee inState(State.AWAITING_APPROVAL) {
        payeeApproval = true;
        finalizeTransaction();
    }

    function finalizeTransaction() internal {
        if (payerApproval && payeeApproval) {
            currentState = State.COMPLETE;
            payable(payee).transfer(amount);
        }
    }

    function refund() external onlyArbiter inState(State.AWAITING_APPROVAL) {
        currentState = State.COMPLETE;
        payable(payer).transfer(amount);
    }
}