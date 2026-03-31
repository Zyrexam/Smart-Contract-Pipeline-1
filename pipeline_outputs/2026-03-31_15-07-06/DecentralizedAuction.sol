// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract DecentralizedAuction is Ownable {
    using SafeERC20 for IERC20;

    uint public highestBid;
    address public highestBidder;
    uint public auctionEndTime;
    bool public ended;

    mapping(address => uint) pendingReturns;

    event HighestBidIncreased(address indexed bidder, uint amount);
    event AuctionEnded(address indexed winner, uint amount);

    error AuctionAlreadyEnded();
    error BidNotHighEnough(uint highestBid);
    error AuctionNotYetEnded();
    error AuctionEndAlreadyCalled();

    constructor(uint biddingTime) Ownable(msg.sender) {
        auctionEndTime = block.timestamp + biddingTime;
    }

    /// @notice Allows users to place a bid in the auction.
    function bid() public payable {
        if (block.timestamp > auctionEndTime) revert AuctionAlreadyEnded();
        if (msg.value <= highestBid) revert BidNotHighEnough(highestBid);

        if (highestBid != 0) {
            pendingReturns[highestBidder] += highestBid;
        }

        highestBidder = msg.sender;
        highestBid = msg.value;
        emit HighestBidIncreased(msg.sender, msg.value);
    }

    /// @notice Allows users to withdraw their bids if they are not the highest bidder.
    function withdraw() public returns (uint amount) {
        amount = pendingReturns[msg.sender];
        if (amount > 0) {
            pendingReturns[msg.sender] = 0;
            payable(msg.sender).transfer(amount);
        }
    }

    /// @notice Ends the auction and transfers the highest bid to the auction owner.
    function endAuction() public onlyOwner {
        if (block.timestamp < auctionEndTime) revert AuctionNotYetEnded();
        if (ended) revert AuctionEndAlreadyCalled();

        ended = true;
        emit AuctionEnded(highestBidder, highestBid);

        payable(owner()).transfer(highestBid);
    }
}