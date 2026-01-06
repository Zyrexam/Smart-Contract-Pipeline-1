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

    /// @dev Emitted when an NFT is set for rent.
    /// @param nftId The ID of the NFT.
    /// @param duration The rental duration.
    event NFTSetForRent(uint256 indexed nftId, uint256 duration);

    /// @dev Emitted when an NFT is rented.
    /// @param nftId The ID of the NFT.
    /// @param renter The address of the renter.
    event NFTRented(uint256 indexed nftId, address indexed renter);

    /// @dev Emitted when an NFT is withdrawn by the owner.
    /// @param nftId The ID of the NFT.
    event NFTWithdrawn(uint256 indexed nftId);

    /// @dev Ensures that the function is called by the NFT owner.
    modifier onlyOwner() {
        if (msg.sender != nftOwner) revert NotOwner();
        _;
    }

    /// @dev Ensures that the function is called by the renter.
    modifier onlyRenter() {
        if (msg.sender != renter) revert NotRenter();
        _;
    }

    /// @dev Ensures that the rental period is over.
    modifier rentalPeriodOver() {
        if (block.timestamp < rentalStartTime + rentalDuration) revert RentalPeriodNotOver();
        _;
    }

    /// @dev Custom error for unauthorized access by non-owner.
    error NotOwner();

    /// @dev Custom error for unauthorized access by non-renter.
    error NotRenter();

    /// @dev Custom error for attempting to withdraw before rental period is over.
    error RentalPeriodNotOver();

    /// @notice Allows the owner to set an NFT for rent with a specified duration.
    /// @param _nftId The ID of the NFT to be rented.
    /// @param duration The duration for which the NFT will be rented.
    function setNFTForRent(uint256 _nftId, uint256 duration) external payable onlyOwner {
        nftId = _nftId;
        rentalDuration = duration;
        isRented = false;
        emit NFTSetForRent(_nftId, duration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param _nftId The ID of the NFT to rent.
    function rentNFT(uint256 _nftId) external payable {
        if (isRented) revert AlreadyRented();
        if (_nftId != nftId) revert InvalidNFTId();
        
        renter = msg.sender;
        rentalStartTime = block.timestamp;
        isRented = true;
        emit NFTRented(_nftId, msg.sender);
    }

    /// @notice Allows the owner to withdraw the NFT after the rental period is over.
    /// @param _nftId The ID of the NFT to withdraw.
    function withdrawNFT(uint256 _nftId) external onlyOwner rentalPeriodOver {
        if (_nftId != nftId) revert InvalidNFTId();
        
        isRented = false;
        renter = address(0);
        emit NFTWithdrawn(_nftId);
    }

    /// @dev Custom error for attempting to rent an already rented NFT.
    error AlreadyRented();

    /// @dev Custom error for invalid NFT ID.
    error InvalidNFTId();
}
