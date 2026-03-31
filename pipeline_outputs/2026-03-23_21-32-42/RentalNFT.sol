// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration.
/// @notice This contract allows users to rent NFTs and manage rental agreements.
contract RentalNFT {
    /// @notice Emitted when an NFT is rented.
    /// @param nftId The ID of the rented NFT.
    /// @param renter The address of the renter.
    /// @param rentalEndTime The timestamp when the rental period ends.
    event NFTLent(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @notice Emitted when a rental period ends.
    /// @param nftId The ID of the NFT whose rental period has ended.
    event RentalEnded(uint256 indexed nftId);

    /// @notice Owner of the NFT.
    mapping(uint256 => address) public nftOwner;

    /// @notice Current renter of the NFT.
    mapping(uint256 => address) public renter;

    /// @notice Rental end time for the NFT.
    mapping(uint256 => uint256) public rentalEndTime;

    /// @notice Address of the contract owner.
    address public owner;

    /// @notice Custom error for unauthorized access.
    error Unauthorized();

    /// @notice Custom error for invalid rental duration.
    error InvalidDuration();

    /// @notice Custom error for ongoing rental.
    error RentalOngoing();

    /// @notice Custom error for rental not found.
    error RentalNotFound();

    /// @notice Modifier to restrict access to the contract owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @notice Initializes the contract setting the deployer as the owner.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows a user to rent an NFT for a specified duration.
    /// @param nftId The ID of the NFT to rent.
    /// @param duration The duration for which the NFT is rented.
    function rentNFT(uint256 nftId, uint256 duration) external {
        if (duration == 0) revert InvalidDuration();
        if (rentalEndTime[nftId] > block.timestamp) revert RentalOngoing();

        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLent(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for a specific NFT.
    /// @param nftId The ID of the NFT to end the rental for.
    function endRental(uint256 nftId) external {
        if (rentalEndTime[nftId] == 0 || rentalEndTime[nftId] > block.timestamp) revert RentalNotFound();

        delete renter[nftId];
        delete rentalEndTime[nftId];

        emit RentalEnded(nftId);
    }

    /// @notice Returns the rental information for a specific NFT.
    /// @param nftId The ID of the NFT to get rental information for.
    /// @return owner The owner of the NFT.
    /// @return renter The current renter of the NFT.
    /// @return rentalEndTime The timestamp when the rental period ends.
    function getRentalInfo(uint256 nftId) external view returns (address owner, address renter, uint256 rentalEndTime) {
        return (nftOwner[nftId], renter[nftId], rentalEndTime[nftId]);
    }
}