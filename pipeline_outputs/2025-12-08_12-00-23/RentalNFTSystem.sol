// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract RentalNFTSystem is ERC721, AccessControl, Ownable {
    // Custom errors
    error InvalidAddress();
    error NotOwner();
    error NotRenter();
    error AlreadyRented();
    error NotRented();
    error RentalPeriodNotOver();

    // State variables
    address private renter;
    uint256 private rentalDuration;
    uint256 private rentalStartTime;
    uint256 private nftTokenId;
    bool private isRented;

    // Roles
    bytes32 public constant RENTER_ROLE = keccak256("RENTER_ROLE");

    // Events
    event NFTSetForRent(address indexed owner, uint256 indexed tokenId, uint256 duration);
    event NFTRented(address indexed renter, uint256 indexed tokenId, uint256 startTime);
    event NFTReturned(address indexed renter, uint256 indexed tokenId);
    event NFTWithdrawn(address indexed owner, uint256 indexed tokenId);

    // Constructor
    constructor(string memory name, string memory symbol) ERC721(name, symbol) Ownable(msg.sender) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /// @notice Allows the owner to set an NFT for rent with a specified duration.
    /// @param tokenId The ID of the NFT to set for rent.
    /// @param duration The rental duration in seconds.
    function setNFTForRent(uint256 tokenId, uint256 duration) public onlyOwner {
        if (isRented) revert AlreadyRented();
        nftTokenId = tokenId;
        rentalDuration = duration;
        isRented = false;
        emit NFTSetForRent(msg.sender, tokenId, duration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param tokenId The ID of the NFT to rent.
    function rentNFT(uint256 tokenId) public onlyRole(RENTER_ROLE) {
        if (isRented) revert AlreadyRented();
        if (nftTokenId != tokenId) revert NotOwner();
        renter = msg.sender;
        rentalStartTime = block.timestamp;
        isRented = true;
        emit NFTRented(msg.sender, tokenId, rentalStartTime);
    }

    /// @notice Allows the renter to return the NFT after the rental period is over.
    /// @param tokenId The ID of the NFT to return.
    function returnNFT(uint256 tokenId) public onlyRole(RENTER_ROLE) {
        if (!isRented) revert NotRented();
        if (nftTokenId != tokenId || msg.sender != renter) revert NotRenter();
        if (block.timestamp < rentalStartTime + rentalDuration) revert RentalPeriodNotOver();
        isRented = false;
        renter = address(0);
        emit NFTReturned(msg.sender, tokenId);
    }

    /// @notice Allows the owner to withdraw the NFT from the rental system.
    /// @param tokenId The ID of the NFT to withdraw.
    function withdrawNFT(uint256 tokenId) public onlyOwner {
        if (isRented) revert AlreadyRented();
        if (nftTokenId != tokenId) revert NotOwner();
        nftTokenId = 0;
        rentalDuration = 0;
        emit NFTWithdrawn(msg.sender, tokenId);
    }

    // Override _update for transfer logic if needed
    function _update(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        super._update(from, to, tokenId, batchSize);
        // Custom transfer logic
    }
}
