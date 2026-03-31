// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Escrow {
    address payable buyer;
    address payable seller;
    uint256 itemPrice;
    bool isClosed = false;

    constructor(address _buyer, address _seller, uint256 _itemPrice) public {
        buyer = _buyer;
        seller = _seller;
        itemPrice = _itemPrice;
    }

    function deposit() public payable {
        require(!isClosed, "Transaction is already closed.");
        require(msg.value == itemPrice, "Incorrect amount sent.");
        buyer.transfer(msg.value);
    }

    function approveDelivery() public {
        require(msg.sender == buyer, "Only the buyer can approve delivery.");
        require(!isClosed, "Transaction is already closed.");
        require(balanceOf(buyer) >= itemPrice, "Buyer does not have sufficient funds.");
        seller.transfer(itemPrice);
        isClosed = true;
    }

    function deliverItem() public {
        require(msg.sender == seller, "Only the seller can deliver the item.");
        require(isClosed, "Transaction has not been approved yet.");
        buyer.transfer(itemPrice);
        isClosed = true;
    }
}