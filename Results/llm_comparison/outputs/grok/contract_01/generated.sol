// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.7.3/contracts/token/ERC721/ERC721.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.7.3/contracts/utils/Counters.sol";

contract RentalNFT {
    // Mapping of NFTs to their rental status
    mapping(address => mapping(uint256 => RentalStatus)) public rentals;

    // Mapping of NFTs to their rental duration
    mapping(address => mapping(uint256 => uint256)) public rentalDurations;

    // Mapping of NFTs to their rental start time
    mapping(address => mapping(uint256 => uint256)) public rentalStartTimes;

    // Mapping of NFTs to their rental end time
    mapping(address => mapping(uint256 => uint256)) public rentalEndTimes;

    // Mapping of NFTs to their rental status
    enum RentalStatus {
        AVAILABLE,
        RENTED
    }

    // Mapping of NFTs to their owners
    mapping(uint256 => address) public nftOwners;

    // Mapping of NFTs to their rental prices
    mapping(uint256 => uint256) public nftRentalPrices;

    // Mapping of NFTs to their rental durations
    mapping(uint256 => uint256) public nftRentalDurations;

    // Counter for NFT IDs
    using Counters for Counters.Counter;
    Counters.Counter public nftIdCounter;

    // Mapping of NFTs to their rental status
    mapping(uint256 => RentalStatus) public nftRentalStatuses;

    // Mapping of NFTs to their rental start time
    mapping(uint256 => uint256) public nftRentalStartTimes;

    // Mapping of NFTs to their rental end time
    mapping(uint256 => uint256) public nftRentalEndTimes;

    // Event emitted when an NFT is rented
    event NFTRented(address indexed owner, uint256 indexed nftId, uint256 rentalDuration, uint256 rentalPrice);

    // Event emitted when an NFT is returned
    event NFTReturned(address indexed owner, uint256 indexed nftId);

    // Event emitted when an NFT is created
    event NFTCreated(address indexed owner, uint256 indexed nftId);

    // Function to create a new NFT
    function createNFT(address _owner, uint256 _rentalPrice, uint256 _rentalDuration) public {
        nftIdCounter.increment();
        uint256 nftId = nftIdCounter.current();

        nftOwners[nftId] = _owner;
        nftRentalPrices[nftId] = _rentalPrice;
        nftRentalDurations[nftId] = _rentalDuration;
        nftRentalStatuses[nftId] = RentalStatus.AVAILABLE;

        emit NFTCreated(_owner, nftId);
    }

    // Function to rent an NFT
    function rentNFT(uint256 _nftId, uint256 _rentalDuration) public {
        require(nftRentalStatuses[_nftId] == RentalStatus.AVAILABLE, "NFT is not available for rent");
        require(msg.sender != nftOwners[_nftId], "You cannot rent your own NFT");

        nftRentalStatuses[_nftId] = RentalStatus.RENTED;
        rentalDurations[msg.sender][_nftId] = _rentalDuration;
        rentalStartTimes[msg.sender][_nftId] = block.timestamp;
        rentalEndTimes[msg.sender][_nftId] = block.timestamp + _rentalDuration;

        emit NFTRented(msg.sender, _nftId, _rentalDuration, nftRentalPrices[_nftId]);
    }

    // Function to return an NFT
    function returnNFT(uint256 _nftId) public {
        require(nftRentalStatuses[_nftId] == RentalStatus.RENTED, "NFT is not rented");
        require(msg.sender == nftOwners[_nftId], "You are not the owner of this NFT");

        nftRentalStatuses[_nftId] = RentalStatus.AVAILABLE;

        emit NFTReturned(msg.sender, _nftId);
    }
}