// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration
/// @notice This contract allows users to rent NFTs for a specified duration and manage rental agreements.
contract RentalNFT {
    address public owner;
    mapping(uint256 => address) public nftOwner;
    mapping(uint256 => address) public renter;
    mapping(uint256 => uint256) public rentalEndTime;

    /// @dev Emitted when an NFT is leased to a renter.
    /// @param nftId The ID of the NFT being leased.
    /// @param renter The address of the renter.
    /// @param rentalEndTime The timestamp when the rental period ends.
    event NFTLeased(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @dev Emitted when the rental period of an NFT ends.
    /// @param nftId The ID of the NFT whose rental period has ended.
    event RentalEnded(uint256 indexed nftId);

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for invalid rental duration.
    error InvalidDuration();

    /// @dev Custom error for rental period not ended.
    error RentalPeriodNotEnded();

    /// @dev Modifier to restrict access to the contract owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @dev Modifier to check if the rental period has ended.
    modifier rentalPeriodEnded(uint256 nftId) {
        if (block.timestamp < rentalEndTime[nftId]) revert RentalPeriodNotEnded();
        _;
    }

    /// @notice Initializes the contract setting the deployer as the initial owner.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows a user to rent an NFT for a specified duration.
    /// @param nftId The ID of the NFT to rent.
    /// @param duration The duration for which the NFT is rented.
    function rentNFT(uint256 nftId, uint256 duration) external {
        if (duration == 0) revert InvalidDuration();
        if (block.timestamp < rentalEndTime[nftId]) revert RentalPeriodNotEnded();

        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLeased(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for the specified NFT.
    /// @param nftId The ID of the NFT to end the rental for.
    function endRental(uint256 nftId) external rentalPeriodEnded(nftId) {
        delete renter[nftId];
        delete rentalEndTime[nftId];

        emit RentalEnded(nftId);
    }

    /// @notice Returns the current renter and rental end time for the specified NFT.
    /// @param nftId The ID of the NFT to get rental information for.
    /// @return The address of the renter and the rental end time.
    function getRentalInfo(uint256 nftId) external view returns (address, uint256) {
        return (renter[nftId], rentalEndTime[nftId]);
    }
}