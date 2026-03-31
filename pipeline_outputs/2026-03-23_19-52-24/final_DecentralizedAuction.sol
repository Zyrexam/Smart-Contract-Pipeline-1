// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract DecentralizedAuction is Ownable {
    using SafeERC20 for IERC20;

    uint256 public highestBid = 0;
    address public highestBidder = address(0);
    uint256 public auctionEndTime = 0;
    bool public auctionStarted = false;

    event AuctionStarted(uint256 endTime);
    event BidPlaced(address indexed bidder, uint256 amount);
    event AuctionEnded(address winner, uint256 amount);

    error NotOwner();
    error AuctionNotActive();
    error BidNotHighEnough(uint256 highestBid);
    error AuctionAlreadyStarted();
    error AuctionNotStarted();
    error AuctionAlreadyEnded();

    modifier auctionActive() {
        if (block.timestamp >= auctionEndTime || !auctionStarted) revert AuctionNotActive();
        _;
    }

    constructor() Ownable() {}

    function startAuction(uint256 duration) public onlyOwner {
        if (auctionStarted) revert AuctionAlreadyStarted();
        auctionEndTime = block.timestamp + duration;
        auctionStarted = true;
        emit AuctionStarted(auctionEndTime);
    }

    function placeBid() public payable auctionActive {
        if (msg.value <= highestBid) revert BidNotHighEnough(highestBid);
        if (highestBidder != address(0)) {
            payable(highestBidder).transfer(highestBid);
        }
        highestBid = msg.value;
        highestBidder = msg.sender;
        emit BidPlaced(msg.sender, msg.value);
    }

    function endAuction() public onlyOwner {
        if (!auctionStarted) revert AuctionNotStarted();
        if (block.timestamp < auctionEndTime) revert AuctionAlreadyEnded();
        auctionStarted = false;
        if (highestBidder != address(0)) {
            payable(owner()).transfer(highestBid);
        }
        emit AuctionEnded(highestBidder, highestBid);
    }
}
