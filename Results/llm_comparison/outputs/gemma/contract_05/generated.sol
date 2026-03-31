pragma solidity ^0.8.20;

contract Escrow {
    // Escrow contract holds the funds until both parties approve the transaction
    // using a flag to indicate that the transaction is approved
    bool public approved = false;

    // Address of the first party
    address payable public recipient;

    // Address of the second party
    address payable public beneficiary;

    // Amount of funds to be transferred
    uint256 public amount;

    // Flag to indicate that the transaction is approved
    bool public approvedTransaction = false;

    // Event emitted when the transaction is approved
    event ApprovalEvent();

    constructor(address payable _recipient, address payable _beneficiary, uint256 _amount) {
        recipient = _recipient;
        beneficiary = _beneficiary;
        amount = _amount;
    }

    // Function to set the approved flag to true
    function approve() public {
        require(msg.sender == recipient, "Only the first party can approve the transaction.");
        approved = true;
        emit ApprovalEvent();
    }

    // Function to set the approved flag to false
    function reject() public {
        require(msg.sender == beneficiary, "Only the second party can reject the transaction.");
        approved = false;
    }

    // Function to transfer the funds to the beneficiary
    function transfer() public {
        require(approvedTransaction, "The transaction is not approved.");
        (recipient).transfer(amount);
        // Reset the approved flag to false
        approvedTransaction = false;
        emit ApprovalEvent();
    }
}