// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract RentalNFT is ERC721Enumerable, Ownable {
    using SafeMath for uint256;

    struct RentInfo {
        address renter;
        uint256 endTime;
        bool rented;
    }

    RentInfo[] public rentals;
    uint256 public rentalDuration;
    uint256 public rentalFee;

    constructor(uint256 _rentalDuration, uint256 _rentalFee) ERC721("RentalNFT", "RNT") {
        rentalDuration = _rentalDuration;
        rentalFee = _rentalFee;
    }

    function rent(uint256 tokenId) public payable {
        require(!rentersOf(tokenId).isApprovedOrOwner(_msgSender()), "NFT is already rented or owned by the caller");
        RentInfo memory rent = rentals[tokenId];
        require(!rent.rented, "NFT is already rented");

        rent.renter = _msgSender();
        rent.endTime = block.timestamp.add( rentalDuration );
        rent.rented = true;

        _mint(msg.sender, tokenId);
        (bool success, ) = payable(_msgSender()).transfer(rentalFee);
        require(success, "Transfer of rental fee failed");
    }

    function returnRent(uint256 tokenId) public {
        RentInfo memory rent = rentals[tokenId];
        require(rent.renter == msg.sender, "You are not the renter of this NFT");
        require(block.timestamp >= rent.endTime, "NFT rental period has not ended yet");

        _transferFrom(msg.sender, owner(), tokenId);
        rent.rented = false;
    }

    function isRented(uint256 tokenId) public view returns (bool) {
        RentInfo memory rent = rentals[tokenId];
        return rent.rented;
    }
}