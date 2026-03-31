// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration.
contract RentalNFT {
    /// @notice Owner of the NFT contract
    address public nftOwner;

    /// @notice Mapping from NFT ID to the current renter
    mapping(uint256 => address) public renter;

    /// @notice Mapping from NFT ID to the rental end time
    mapping(uint256 => uint256) public rentalEndTime;

    /// @dev Emitted when an NFT is leased
    /// @param nftId The ID of the NFT being leased
    /// @param renter The address of the renter
    /// @param rentalEndTime The time when the rental ends
    event NFTLeased(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @dev Emitted when a rental period ends
    /// @param nftId The ID of the NFT whose rental has ended
    event RentalEnded(uint256 indexed nftId);

    /// @dev Custom error for unauthorized access
    error Unauthorized();

    /// @dev Custom error for invalid rental duration
    error InvalidDuration();

    /// @dev Custom error for ongoing rental
    error RentalOngoing();

    /// @dev Custom error for rental not found
    error RentalNotFound();

    /// @dev Modifier to restrict access to the contract owner
    modifier onlyOwner() {
        if (msg.sender != nftOwner) revert Unauthorized();
        _;
    }

    /// @notice Constructor to set the owner of the contract
    constructor() {
        nftOwner = msg.sender;
    }

    /// @notice Allows a user to rent an NFT for a specified duration
    /// @param nftId The ID of the NFT to rent
    /// @param duration The duration for which the NFT is rented
    function rentNFT(uint256 nftId, uint256 duration) external {
        if (duration == 0) revert InvalidDuration();
        if (block.timestamp < rentalEndTime[nftId]) revert RentalOngoing();

        // Set the renter and rental end time
        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLeased(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for a specific NFT
    /// @param nftId The ID of the NFT to end the rental for
    function endRental(uint256 nftId) external {
        if (block.timestamp < rentalEndTime[nftId]) revert RentalOngoing();
        if (renter[nftId] == address(0)) revert RentalNotFound();

        // Clear the renter and rental end time
        delete renter[nftId];
        delete rentalEndTime[nftId];

        emit RentalEnded(nftId);
    }

    /// @notice Returns the current renter and rental end time for a specific NFT
    /// @param nftId The ID of the NFT to query
    /// @return The address of the renter and the rental end time
    function getRentalInfo(uint256 nftId) external view returns (address, uint256) {
        return (renter[nftId], rentalEndTime[nftId]);
    }
}