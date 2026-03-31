// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A system for renting NFTs for a fixed duration
/// @notice This contract allows users to rent NFTs for a specified period
contract RentalNFT {
    // State variables
    address public owner;
    mapping(uint256 => address) public nftOwner;
    mapping(uint256 => address) public renter;
    mapping(uint256 => uint256) public rentalEndTime;

    // Events
    event NFTLent(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);
    event RentalEnded(uint256 indexed nftId, address indexed renter);

    // Custom errors
    error NotOwner();
    error AlreadyRented();
    error RentalPeriodNotEnded();
    error NotRenter();

    /// @dev Modifier to restrict access to the contract owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @dev Modifier to check if the rental period has ended
    modifier rentalPeriodEnded(uint256 nftId) {
        if (block.timestamp <= rentalEndTime[nftId]) revert RentalPeriodNotEnded();
        _;
    }

    /// @dev Modifier to check if the caller is the renter
    modifier onlyRenter(uint256 nftId) {
        if (msg.sender != renter[nftId]) revert NotRenter();
        _;
    }

    /// @notice Constructor to set the contract owner
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows a user to rent an NFT for a specified duration
    /// @param nftId The ID of the NFT to rent
    /// @param duration The duration for which the NFT is rented
    function rentNFT(uint256 nftId, uint256 duration) external {
        if (renter[nftId] != address(0)) revert AlreadyRented();

        // Set rental details
        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLent(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for a specific NFT
    /// @param nftId The ID of the NFT to end the rental for
    function endRental(uint256 nftId) external onlyRenter(nftId) rentalPeriodEnded(nftId) {
        address currentRenter = renter[nftId];

        // Reset rental details
        renter[nftId] = address(0);
        rentalEndTime[nftId] = 0;

        emit RentalEnded(nftId, currentRenter);
    }

    /// @notice Returns the rental information for a specific NFT
    /// @param nftId The ID of the NFT to get rental information for
    /// @return owner The owner of the NFT
    /// @return renter The current renter of the NFT
    /// @return rentalEndTime The end time of the rental period
    function getRentalInfo(uint256 nftId) external view returns (address, address, uint256) {
        return (nftOwner[nftId], renter[nftId], rentalEndTime[nftId]);
    }
}