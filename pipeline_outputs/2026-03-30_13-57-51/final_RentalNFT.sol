// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration
/// @notice This contract allows users to rent NFTs for a specified duration and manages the rental state
contract RentalNFT {
    /// @dev Owner of the contract
    address public owner;

    /// @dev Mapping from NFT ID to the owner of the NFT
    mapping(uint256 => address) public nftOwner;

    /// @dev Mapping from NFT ID to the current renter
    mapping(uint256 => address) public renter;

    /// @dev Mapping from NFT ID to the rental end time
    mapping(uint256 => uint256) public rentalEndTime;

    /// @dev Event emitted when an NFT is leased
    event NFTLeased(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @dev Event emitted when a rental period ends
    event RentalEnded(uint256 indexed nftId);

    /// @dev Custom error for unauthorized access
    error Unauthorized();

    /// @dev Custom error for invalid rental duration
    error InvalidDuration();

    /// @dev Custom error for ongoing rental
    error RentalOngoing();

    /// @dev Modifier to restrict access to the owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @notice Constructor to set the initial owner of the contract
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows a user to rent an NFT for a specified duration
    /// @param nftId The ID of the NFT to rent
    /// @param duration The duration for which the NFT is rented
    function rentNFT(uint256 nftId, uint256 duration) external {
        if (duration == 0) revert InvalidDuration();
        if (block.timestamp < rentalEndTime[nftId]) revert RentalOngoing();

        // Update rental state
        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLeased(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for the specified NFT
    /// @param nftId The ID of the NFT to end the rental for
    function endRental(uint256 nftId) external {
        if (block.timestamp < rentalEndTime[nftId]) revert RentalOngoing();

        // Reset rental state
        renter[nftId] = address(0);
        rentalEndTime[nftId] = 0;

        emit RentalEnded(nftId);
    }

    /// @notice Returns the current renter and rental end time for the specified NFT
    /// @param nftId The ID of the NFT to get rental information for
    /// @return The current renter and rental end time
    function getRentalInfo(uint256 nftId) external view returns (address, uint256) {
        return (renter[nftId], rentalEndTime[nftId]);
    }
}