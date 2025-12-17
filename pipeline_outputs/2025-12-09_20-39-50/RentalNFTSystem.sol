// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract RentalNFTSystem is ERC721, AccessControl, Ownable {
    // Custom errors
    error InvalidAddress();
    error NotNFTOwner();
    error NotRenter();
    error RentalPeriodNotOver();
    error NFTAlreadyRented();
    error NFTNotRented();

    // State variables
    address public nftOwner;
    address public renter;
    uint256 public rentalDuration;
    uint256 public rentalStartTime;
    uint256 public nftId;
    bool public isRented;

    // Roles
    bytes32 public constant USER_ROLE = keccak256("USER_ROLE");

    // Events
    event NFTSetForRent(uint256 indexed nftId, uint256 rentalDuration);
    event NFTRented(uint256 indexed nftId, address indexed renter, uint256 rentalStartTime);
    event NFTWithdrawn(uint256 indexed nftId);

    // Constructor
    constructor() ERC721("NFT", "NFT") Ownable(msg.sender) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /// @notice Allows the owner to set an NFT for rent with a specified duration.
    /// @param _nftId The ID of the NFT to be set for rent.
    /// @param _rentalDuration The duration for which the NFT can be rented.
    function setNFTForRent(uint256 _nftId, uint256 _rentalDuration) external onlyOwner {
        if (isRented) revert NFTAlreadyRented();
        nftId = _nftId;
        rentalDuration = _rentalDuration;
        isRented = false;
        emit NFTSetForRent(_nftId, _rentalDuration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param _nftId The ID of the NFT to rent.
    function rentNFT(uint256 _nftId) external onlyRole(USER_ROLE) {
        if (isRented) revert NFTAlreadyRented();
        if (_nftId != nftId) revert InvalidAddress();
        renter = msg.sender;
        rentalStartTime = block.timestamp;
        isRented = true;
        emit NFTRented(_nftId, msg.sender, rentalStartTime);
    }

    /// @notice Allows the owner to withdraw the NFT after the rental period is over.
    /// @param _nftId The ID of the NFT to withdraw.
    function withdrawNFT(uint256 _nftId) external onlyOwner {
        if (!isRented) revert NFTNotRented();
        if (_nftId != nftId) revert InvalidAddress();
        if (block.timestamp < rentalStartTime + rentalDuration) revert RentalPeriodNotOver();
        isRented = false;
        renter = address(0);
        emit NFTWithdrawn(_nftId);
    }

    // Override _update for transfer logic if needed
    function _update(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        super._update(from, to, tokenId, batchSize);
        // Custom transfer logic if needed
    }
}
