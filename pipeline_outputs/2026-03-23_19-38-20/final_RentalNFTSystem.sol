// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFTSystem
/// @notice A smart contract system that allows users to rent NFTs for a fixed duration.
contract RentalNFTSystem {
    address public nftOwner;
    address public renter;
    uint256 public rentalDuration;
    uint256 public rentalStartTime;
    uint256 public nftId;
    bool public isRented;

    /// @dev Ensures that the function is called only by the NFT owner.
    modifier onlyOwner() {
        if (msg.sender != nftOwner) revert NotOwner();
        _;
    }

    /// @dev Ensures that the function is called only by the renter.
    modifier onlyRenter() {
        if (msg.sender != renter) revert NotRenter();
        _;
    }

    /// @dev Ensures that the rental period is still active.
    modifier rentalPeriodActive() {
        if (block.timestamp >= rentalStartTime + rentalDuration) revert RentalPeriodEnded();
        _;
    }

    /// @dev Ensures that the rental period has ended.
    modifier rentalPeriodEnded() {
        if (block.timestamp < rentalStartTime + rentalDuration) revert RentalPeriodActive();
        _;
    }

    /// @notice Emitted when an NFT is listed for rent.
    /// @param nftId The ID of the NFT.
    /// @param owner The address of the owner.
    /// @param duration The rental duration.
    event NFTListed(uint256 indexed nftId, address indexed owner, uint256 duration);

    /// @notice Emitted when an NFT is rented.
    /// @param nftId The ID of the NFT.
    /// @param renter The address of the renter.
    /// @param startTime The start time of the rental.
    event NFTRented(uint256 indexed nftId, address indexed renter, uint256 startTime);

    /// @notice Emitted when an NFT is withdrawn after rental.
    /// @param nftId The ID of the NFT.
    /// @param owner The address of the owner.
    event NFTWithdrawn(uint256 indexed nftId, address indexed owner);

    /// @dev Error thrown when the caller is not the owner.
    error NotOwner();

    /// @dev Error thrown when the caller is not the renter.
    error NotRenter();

    /// @dev Error thrown when the rental period has ended.
    error RentalPeriodEnded();

    /// @dev Error thrown when the rental period is still active.
    error RentalPeriodActive();

    /// @dev Error thrown when the NFT ID is invalid.
    error InvalidNFT();

    /// @notice Allows the owner to list an NFT for rent for a specified duration.
    /// @param _nftId The ID of the NFT to be listed.
    /// @param _duration The duration for which the NFT will be rented.
    function listNFTForRent(uint256 _nftId, uint256 _duration) external onlyOwner payable {
        nftId = _nftId;
        rentalDuration = _duration;
        isRented = false;
        emit NFTListed(_nftId, msg.sender, _duration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param _nftId The ID of the NFT to be rented.
    function rentNFT(uint256 _nftId) external payable {
        if (isRented) revert RentalPeriodActive();
        if (_nftId != nftId) revert InvalidNFT();
        
        renter = msg.sender;
        rentalStartTime = block.timestamp;
        isRented = true;
        emit NFTRented(_nftId, msg.sender, rentalStartTime);
    }

    /// @notice Allows the owner to withdraw the NFT after the rental period has ended.
    /// @param _nftId The ID of the NFT to be withdrawn.
    function withdrawNFT(uint256 _nftId) external onlyOwner rentalPeriodEnded {
        if (_nftId != nftId) revert InvalidNFT();
        
        isRented = false;
        emit NFTWithdrawn(_nftId, msg.sender);
    }
}
