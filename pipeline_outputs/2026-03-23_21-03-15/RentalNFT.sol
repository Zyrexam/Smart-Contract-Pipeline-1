// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration.
contract RentalNFT {
    /// @notice Owner of the NFT contract
    address public owner;

    /// @notice Mapping from NFT ID to the owner of the NFT
    mapping(uint256 => address) public nftOwner;

    /// @notice Mapping from NFT ID to the current renter
    mapping(uint256 => address) public renter;

    /// @notice Mapping from NFT ID to the rental end time
    mapping(uint256 => uint256) public rentalEndTime;

    /// @dev Emitted when an NFT is leased
    /// @param nftId The ID of the NFT being leased
    /// @param renter The address of the renter
    /// @param rentalEndTime The end time of the rental period
    event NFTLeased(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @dev Emitted when a rental period ends
    /// @param nftId The ID of the NFT whose rental has ended
    event RentalEnded(uint256 indexed nftId);

    /// @dev Error thrown when the caller is not the owner
    error NotOwner();

    /// @dev Error thrown when the NFT is already rented
    error AlreadyRented();

    /// @dev Error thrown when the rental period has not ended
    error RentalNotEnded();

    /// @dev Modifier to restrict access to the contract owner
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
    /// @param duration The duration for which the NFT is rented
    function rentNFT(uint256 nftId, uint256 duration) external {
        if (renter[nftId] != address(0) && block.timestamp < rentalEndTime[nftId]) revert AlreadyRented();

        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLeased(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for a specific NFT
    /// @param nftId The ID of the NFT to end the rental for
    function endRental(uint256 nftId) external {
        if (block.timestamp < rentalEndTime[nftId]) revert RentalNotEnded();

        delete renter[nftId];
        delete rentalEndTime[nftId];

        emit RentalEnded(nftId);
    }

    /// @notice Returns the current renter and rental end time for a specific NFT
    /// @param nftId The ID of the NFT to get rental information for
    /// @return The address of the current renter and the rental end time
    function getRentalInfo(uint256 nftId) external view returns (address, uint256) {
        return (renter[nftId], rentalEndTime[nftId]);
    }
}