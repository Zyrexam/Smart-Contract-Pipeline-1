// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFTSystem
/// @notice A system where users can rent NFTs for a fixed duration.
contract RentalNFTSystem {
    address private nftOwner;
    address private renter;
    uint256 private rentalDuration;
    uint256 private rentalStartTime;
    uint256 private nftTokenId;
    bool private isRented;

    /// @notice Emitted when an NFT is set for rent.
    /// @param tokenId The ID of the NFT.
    /// @param duration The duration for which the NFT is available for rent.
    event NFTSetForRent(uint256 indexed tokenId, uint256 duration);

    /// @notice Emitted when an NFT is rented.
    /// @param tokenId The ID of the rented NFT.
    /// @param renter The address of the renter.
    event NFTRented(uint256 indexed tokenId, address indexed renter);

    /// @notice Emitted when an NFT is returned.
    /// @param tokenId The ID of the returned NFT.
    event NFTReturned(uint256 indexed tokenId);

    /// @notice Emitted when an NFT is withdrawn by the owner.
    /// @param tokenId The ID of the withdrawn NFT.
    event NFTWithdrawn(uint256 indexed tokenId);

    /// @dev Ensures that the function is called by the NFT owner.
    modifier onlyOwner() {
        if (msg.sender != nftOwner) revert NotOwner();
        _;
    }

    /// @dev Ensures that the function is called by the current renter.
    modifier onlyRenter() {
        if (msg.sender != renter) revert NotRenter();
        _;
    }

    /// @dev Ensures that the NFT is not currently rented.
    modifier notRented() {
        if (isRented) revert AlreadyRented();
        _;
    }

    /// @dev Ensures that the rental period is over.
    modifier rentalPeriodOver() {
        if (block.timestamp < rentalStartTime + rentalDuration) revert RentalPeriodNotOver();
        _;
    }

    /// @notice Allows the owner to set an NFT for rent with a specified duration.
    /// @param tokenId The ID of the NFT to be rented.
    /// @param duration The duration for which the NFT will be rented.
    function setNFTForRent(uint256 tokenId, uint256 duration) external payable onlyOwner notRented {
        nftTokenId = tokenId;
        rentalDuration = duration;
        emit NFTSetForRent(tokenId, duration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param tokenId The ID of the NFT to rent.
    function rentNFT(uint256 tokenId) external payable notRented {
        if (tokenId != nftTokenId) revert InvalidTokenId();
        renter = msg.sender;
        rentalStartTime = block.timestamp;
        isRented = true;
        emit NFTRented(tokenId, msg.sender);
    }

    /// @notice Allows the renter to return the NFT after the rental period.
    /// @param tokenId The ID of the NFT to return.
    function returnNFT(uint256 tokenId) external onlyRenter rentalPeriodOver {
        if (tokenId != nftTokenId) revert InvalidTokenId();
        isRented = false;
        renter = address(0);
        emit NFTReturned(tokenId);
    }

    /// @notice Allows the owner to withdraw the NFT if it is not rented.
    /// @param tokenId The ID of the NFT to withdraw.
    function withdrawNFT(uint256 tokenId) external onlyOwner notRented {
        if (tokenId != nftTokenId) revert InvalidTokenId();
        emit NFTWithdrawn(tokenId);
    }

    /// @dev Custom error for non-owner access.
    error NotOwner();

    /// @dev Custom error for non-renter access.
    error NotRenter();

    /// @dev Custom error for already rented NFT.
    error AlreadyRented();

    /// @dev Custom error for rental period not over.
    error RentalPeriodNotOver();

    /// @dev Custom error for invalid token ID.
    error InvalidTokenId();
}
