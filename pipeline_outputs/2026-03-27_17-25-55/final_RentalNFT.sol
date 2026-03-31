// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration.
/// @dev Implements role-based access control for minting and renting functionalities.
contract RentalNFT {
    // State variables
    address public nftOwner;
    uint256 public rentalPrice;
    uint256 public rentalDuration;
    uint256 public rentalEndTime;

    // Roles
    address private owner;
    address private renter;

    // Events
    event NFTMinted(address indexed to);
    event NFTLeased(address indexed renter);
    event NFTReturned(address indexed renter);

    // Custom errors
    error NotOwner();
    error NotRenter();
    error AlreadyRented();
    error RentalPeriodNotEnded();
    error InsufficientPayment();

    /// @dev Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @dev Modifier to restrict access to the renter.
    modifier onlyRenter() {
        if (msg.sender != renter) revert NotRenter();
        _;
    }

    /// @dev Constructor to set the contract deployer as the owner.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Mint a new NFT to the specified address.
    /// @param to The address to mint the NFT to.
    function mint(address to) external onlyOwner {
        nftOwner = to;
        emit NFTMinted(to);
    }

    /// @notice Set the rental price and duration for the NFT.
    /// @param price The rental price.
    /// @param duration The rental duration in seconds.
    function setRentalTerms(uint256 price, uint256 duration) external onlyOwner {
        rentalPrice = price;
        rentalDuration = duration;
    }

    /// @notice Rent the NFT for the specified duration.
    function rentNFT() external payable {
        if (msg.value < rentalPrice) revert InsufficientPayment();
        if (block.timestamp < rentalEndTime) revert AlreadyRented();

        renter = msg.sender;
        rentalEndTime = block.timestamp + rentalDuration;
        emit NFTLeased(msg.sender);
    }

    /// @notice Return the rented NFT after the rental period.
    function returnNFT() external onlyRenter {
        if (block.timestamp < rentalEndTime) revert RentalPeriodNotEnded();

        renter = address(0);
        emit NFTReturned(msg.sender);
    }
}