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
    event NFTLeased(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @dev Emitted when a rental period ends
    event RentalEnded(uint256 indexed nftId);

    /// @dev Error for unauthorized access
    error Unauthorized();

    /// @dev Error for invalid rental duration
    error InvalidDuration();

    /// @dev Error for active rental
    error RentalActive();

    /// @dev Error for inactive rental
    error RentalInactive();

    /// @dev Modifier to restrict access to the contract owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @dev Modifier to check if the rental period is active
    modifier rentalActive(uint256 nftId) {
        if (block.timestamp > rentalEndTime[nftId]) revert RentalInactive();
        _;
    }

    /// @dev Modifier to check if the rental period is inactive
    modifier rentalInactive(uint256 nftId) {
        if (block.timestamp <= rentalEndTime[nftId]) revert RentalActive();
        _;
    }

    /// @notice Constructor to set the contract owner
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows a user to rent an NFT for a specified duration
    /// @param nftId The ID of the NFT to rent
    /// @param duration The duration of the rental in seconds
    function rentNFT(uint256 nftId, uint256 duration) external rentalInactive(nftId) {
        if (duration == 0) revert InvalidDuration();

        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLeased(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for the specified NFT
    /// @param nftId The ID of the NFT to end the rental for
    function endRental(uint256 nftId) external rentalActive(nftId) {
        if (msg.sender != renter[nftId]) revert Unauthorized();

        rentalEndTime[nftId] = block.timestamp;

        emit RentalEnded(nftId);
    }

    /// @notice Returns the current renter and rental end time for the specified NFT
    /// @param nftId The ID of the NFT to get rental information for
    /// @return The current renter and rental end time
    function getRentalInfo(uint256 nftId) external view returns (address, uint256) {
        return (renter[nftId], rentalEndTime[nftId]);
    }
}