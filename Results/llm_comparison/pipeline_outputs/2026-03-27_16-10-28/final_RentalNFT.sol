// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration.
contract RentalNFT {
    address public owner;
    mapping(uint256 => address) public nftOwner;
    mapping(uint256 => address) public renter;
    mapping(uint256 => uint256) public rentalEndTime;
    mapping(uint256 => uint256) public rentalPrice;

    /// @dev Emitted when an NFT is leased.
    /// @param nftId The ID of the NFT being leased.
    /// @param renter The address of the renter.
    /// @param rentalEndTime The end time of the rental period.
    event NFTLeased(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @dev Emitted when a rental period ends.
    /// @param nftId The ID of the NFT whose rental has ended.
    /// @param renter The address of the renter.
    event RentalEnded(uint256 indexed nftId, address indexed renter);

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for invalid rental duration.
    error InvalidDuration();

    /// @dev Custom error for active rental.
    error ActiveRental();

    /// @dev Custom error for inactive rental.
    error InactiveRental();

    /// @dev Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @dev Constructor sets the contract deployer as the owner.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows a user to rent an NFT for a specified duration.
    /// @param nftId The ID of the NFT to rent.
    /// @param duration The duration for which the NFT is rented.
    function rentNFT(uint256 nftId, uint256 duration) external payable {
        if (duration == 0) revert InvalidDuration();
        if (renter[nftId] != address(0) && block.timestamp < rentalEndTime[nftId]) revert ActiveRental();
        if (msg.value < rentalPrice[nftId]) revert Unauthorized();

        // Update rental information
        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + duration;

        emit NFTLeased(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Ends the rental period for a specific NFT.
    /// @param nftId The ID of the NFT whose rental is to be ended.
    function endRental(uint256 nftId) external {
        if (renter[nftId] == address(0) || block.timestamp < rentalEndTime[nftId]) revert InactiveRental();

        address previousRenter = renter[nftId];
        renter[nftId] = address(0);
        rentalEndTime[nftId] = 0;

        emit RentalEnded(nftId, previousRenter);
    }

    /// @notice Returns the rental information for a specific NFT.
    /// @param nftId The ID of the NFT.
    /// @return owner The owner of the NFT.
    /// @return renter The current renter of the NFT.
    /// @return rentalEndTime The end time of the current rental period.
    function getRentalInfo(uint256 nftId) external view returns (address, address, uint256) {
        return (nftOwner[nftId], renter[nftId], rentalEndTime[nftId]);
    }

    /// @notice Sets the rental price for a specific NFT.
    /// @param nftId The ID of the NFT.
    /// @param price The rental price to set.
    function setRentalPrice(uint256 nftId, uint256 price) external onlyOwner {
        rentalPrice[nftId] = price;
    }

    /// @notice Sets the owner of a specific NFT.
    /// @param nftId The ID of the NFT.
    /// @param newOwner The address of the new owner.
    function setNFTOwner(uint256 nftId, address newOwner) external onlyOwner {
        nftOwner[nftId] = newOwner;
    }
}