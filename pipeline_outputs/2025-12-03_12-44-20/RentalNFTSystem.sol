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
    address private nftOwner;
    address private renter;
    uint256 private rentalDuration;
    uint256 private rentalStartTime;
    uint256 private nftTokenId;
    bool private isRented;

    // Roles
    bytes32 public constant RENTER_ROLE = keccak256("RENTER_ROLE");

    // Events
    event NFTListed(address indexed owner, uint256 indexed tokenId, uint256 duration);
    event NFTRented(address indexed renter, uint256 indexed tokenId, uint256 startTime);
    event RentalEnded(address indexed owner, uint256 indexed tokenId);

    // Constructor
    constructor() ERC721("NFT", "NFT") Ownable(msg.sender) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /// @notice Allows the owner to list an NFT for rent with a specified duration.
    /// @param tokenId The ID of the NFT to be listed.
    /// @param duration The duration for which the NFT can be rented.
    function listNFT(uint256 tokenId, uint256 duration) public onlyOwner {
        if (isRented) revert AlreadyRented();
        nftOwner = msg.sender;
        nftTokenId = tokenId;
        rentalDuration = duration;
        emit NFTListed(nftOwner, nftTokenId, rentalDuration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param tokenId The ID of the NFT to be rented.
    function rentNFT(uint256 tokenId) public onlyRole(RENTER_ROLE) {
        if (isRented) revert AlreadyRented();
        if (tokenId != nftTokenId) revert NotRented();
        renter = msg.sender;
        rentalStartTime = block.timestamp;
        isRented = true;
        emit NFTRented(renter, nftTokenId, rentalStartTime);
    }

    /// @notice Allows the owner to end the rental period and reclaim the NFT.
    /// @param tokenId The ID of the NFT to end the rental for.
    function endRental(uint256 tokenId) public onlyOwner {
        if (!isRented) revert NotRented();
        if (block.timestamp < rentalStartTime + rentalDuration) revert RentalPeriodNotOver();
        if (tokenId != nftTokenId) revert NotRented();
        isRented = false;
        renter = address(0);
        emit RentalEnded(nftOwner, nftTokenId);
    }

    // Override _update for transfer logic
    function _update(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        if (isRented && tokenId == nftTokenId) revert AlreadyRented();
        super._update(from, to, tokenId, batchSize);
    }
}
