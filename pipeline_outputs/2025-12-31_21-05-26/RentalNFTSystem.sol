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

    /// @notice Emitted when an NFT is listed for rent.
    /// @param nftId The ID of the NFT.
    /// @param rentalDuration The duration for which the NFT is available for rent.
    event NFTListed(uint256 indexed nftId, uint256 rentalDuration);

    /// @notice Emitted when an NFT is rented.
    /// @param nftId The ID of the NFT.
    /// @param renter The address of the renter.
    event NFTRented(uint256 indexed nftId, address indexed renter);

    /// @notice Emitted when an NFT is withdrawn by the owner.
    /// @param nftId The ID of the NFT.
    event NFTWithdrawn(uint256 indexed nftId);

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for invalid operation.
    error InvalidOperation();

    /// @dev Modifier to restrict access to the NFT owner.
    modifier onlyOwner() {
        if (msg.sender != nftOwner) revert Unauthorized();
        _;
    }

    /// @dev Modifier to restrict access to the renter.
    modifier onlyRenter() {
        if (msg.sender != renter) revert Unauthorized();
        _;
    }

    /// @dev Modifier to ensure the rental period has ended.
    modifier rentalPeriodEnded() {
        if (block.timestamp < rentalStartTime + rentalDuration) revert InvalidOperation();
        _;
    }

    /// @notice Allows the owner to list an NFT for rent with a specified duration.
    /// @param _nftId The ID of the NFT to be listed.
    /// @param _rentalDuration The duration for which the NFT will be rented.
    function listNFTForRent(uint256 _nftId, uint256 _rentalDuration) external payable onlyOwner {
        if (isRented) revert InvalidOperation();
        nftId = _nftId;
        rentalDuration = _rentalDuration;
        isRented = false;
        emit NFTListed(_nftId, _rentalDuration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param _nftId The ID of the NFT to be rented.
    function rentNFT(uint256 _nftId) external payable {
        if (isRented || _nftId != nftId) revert InvalidOperation();
        renter = msg.sender;
        rentalStartTime = block.timestamp;
        isRented = true;
        emit NFTRented(_nftId, msg.sender);
    }

    /// @notice Allows the owner to withdraw the NFT after the rental period has ended.
    /// @param _nftId The ID of the NFT to be withdrawn.
    function withdrawNFT(uint256 _nftId) external onlyOwner rentalPeriodEnded {
        if (_nftId != nftId) revert InvalidOperation();
        isRented = false;
        renter = address(0);
        emit NFTWithdrawn(_nftId);
    }
}
