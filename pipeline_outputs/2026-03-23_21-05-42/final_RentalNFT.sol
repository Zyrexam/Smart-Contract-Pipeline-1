// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration.
contract RentalNFT {
    // State variables
    mapping(uint256 => address) public nftOwner;
    mapping(uint256 => uint256) public rentalDuration;
    mapping(uint256 => uint256) public rentalPrice;
    mapping(uint256 => address) public renter;
    mapping(uint256 => uint256) public rentalEndTime;

    // Role-based access control
    address public owner;
    mapping(address => bool) public isRenter;

    // Events
    event NFTMinted(uint256 indexed nftId, address indexed to);
    event NFTLeased(uint256 indexed nftId, address indexed renter, uint256 endTime);
    event NFTReturned(uint256 indexed nftId, address indexed renter);

    // Custom errors
    error NotOwner();
    error NotRenter();
    error AlreadyRented();
    error RentalPeriodNotEnded();
    error InsufficientPayment();

    /// @dev Modifier to restrict access to the contract owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @dev Modifier to restrict access to registered renters.
    modifier onlyRenter() {
        if (!isRenter[msg.sender]) revert NotRenter();
        _;
    }

    /// @notice Constructor to set the contract owner.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Mint a new NFT to a specified address.
    /// @param to The address to mint the NFT to.
    function mint(address to) external onlyOwner {
        uint256 nftId = uint256(keccak256(abi.encodePacked(block.timestamp, to)));
        nftOwner[nftId] = to;
        emit NFTMinted(nftId, to);
    }

    /// @notice Set the rental terms for a specific NFT.
    /// @param nftId The ID of the NFT.
    /// @param duration The rental duration in seconds.
    /// @param price The rental price in wei.
    function setRentalTerms(uint256 nftId, uint256 duration, uint256 price) external onlyOwner {
        rentalDuration[nftId] = duration;
        rentalPrice[nftId] = price;
    }

    /// @notice Rent an NFT for the specified duration.
    /// @param nftId The ID of the NFT to rent.
    function rentNFT(uint256 nftId) external payable onlyRenter {
        if (renter[nftId] != address(0)) revert AlreadyRented();
        if (msg.value < rentalPrice[nftId]) revert InsufficientPayment();

        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + rentalDuration[nftId];
        emit NFTLeased(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Return the rented NFT after the rental period.
    /// @param nftId The ID of the NFT to return.
    function returnNFT(uint256 nftId) external onlyRenter {
        if (block.timestamp < rentalEndTime[nftId]) revert RentalPeriodNotEnded();
        if (renter[nftId] != msg.sender) revert NotRenter();

        renter[nftId] = address(0);
        rentalEndTime[nftId] = 0;
        emit NFTReturned(nftId, msg.sender);
    }

    /// @notice Get rental information for a specific NFT.
    /// @param nftId The ID of the NFT.
    /// @return owner The owner of the NFT.
    /// @return renter The current renter of the NFT.
    /// @return endTime The rental end time.
    function getRentalInfo(uint256 nftId) external view returns (address owner, address renter, uint256 endTime) {
        return (nftOwner[nftId], renter[nftId], rentalEndTime[nftId]);
    }
}