// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A system for renting NFTs for a fixed duration
/// @notice This contract allows users to rent NFTs for a specified duration
contract RentalNFT {
    address public owner;

    /// @notice Mapping from NFT ID to the owner of the NFT
    mapping(uint256 => address) public nftOwner;

    /// @notice Mapping from NFT ID to the current renter
    mapping(uint256 => address) public renter;

    /// @notice Mapping from NFT ID to the rental end time
    mapping(uint256 => uint256) public rentalEndTime;

    /// @notice Event emitted when an NFT is leased
    /// @param nftId The ID of the NFT being leased
    /// @param renter The address of the renter
    /// @param rentalEndTime The end time of the rental period
    event NFTLeased(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @notice Event emitted when a rental period ends
    /// @param nftId The ID of the NFT whose rental period has ended
    event RentalEnded(uint256 indexed nftId);

    /// @notice Error thrown when the caller is not the owner
    error NotOwner();

    /// @notice Error thrown when the NFT is currently rented
    error AlreadyRented();

    /// @notice Error thrown when the rental period has not ended
    error RentalNotEnded();

    /// @notice Modifier to restrict functions to the contract owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @notice Constructor to set the contract owner
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows a user to rent an NFT for a specified duration
    /// @param nftId The ID of the NFT to rent
    /// @param duration The duration of the rental in seconds
    function rentNFT(uint256 nftId, uint256 duration) external {
        if (renter[nftId] != address(0) && block.timestamp < rentalEndTime[nftId]) revert AlreadyRented();

        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLeased(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for the specified NFT
    /// @param nftId The ID of the NFT to end the rental for
    function endRental(uint256 nftId) external {
        if (block.timestamp < rentalEndTime[nftId]) revert RentalNotEnded();

        renter[nftId] = address(0);
        rentalEndTime[nftId] = 0;

        emit RentalEnded(nftId);
    }

    /// @notice Returns the current renter and rental end time for the specified NFT
    /// @param nftId The ID of the NFT to get rental information for
    /// @return The address of the current renter and the rental end time
    function getRentalInfo(uint256 nftId) external view returns (address, uint256) {
        return (renter[nftId], rentalEndTime[nftId]);
    }
}