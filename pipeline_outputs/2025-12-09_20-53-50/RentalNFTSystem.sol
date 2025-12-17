// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract RentalNFTSystem is ERC721, AccessControl, Ownable {
    // Custom errors
    error InvalidAddress();
    error NotAuthorized();
    error RentalPeriodNotOver();
    error NFTAlreadyRented();
    error NFTNotRented();

    // State variables
    uint256 public rentalDuration;
    uint256 public rentalStartTime;
    uint256 public nftId;
    bool public isRented;

    // Roles
    bytes32 public constant RENTER_ROLE = keccak256("RENTER_ROLE");

    // Events
    event NFTSetForRent(uint256 indexed nftId, uint256 duration);
    event NFTRented(uint256 indexed nftId, address indexed renter);
    event NFTWithdrawn(uint256 indexed nftId);

    // Constructor
    constructor(string memory name, string memory symbol, address initialOwner) ERC721(name, symbol) Ownable(initialOwner) {
        _grantRole(DEFAULT_ADMIN_ROLE, initialOwner);
    }

    /// @notice Mints a new NFT to the specified address.
    /// @param to The address to mint the NFT to.
    /// @param tokenId The ID of the NFT to mint.
    function safeMint(address to, uint256 tokenId) public onlyOwner {
        _safeMint(to, tokenId);
    }

    /// @notice Allows the owner to set an NFT for rent with a specified duration.
    /// @param _nftId The ID of the NFT to set for rent.
    /// @param duration The duration for which the NFT can be rented.
    function setNFTForRent(uint256 _nftId, uint256 duration) public onlyOwner {
        if (isRented) revert NFTAlreadyRented();
        if (ownerOf(_nftId) != msg.sender) revert NotAuthorized();
        nftId = _nftId;
        rentalDuration = duration;
        emit NFTSetForRent(_nftId, duration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param _nftId The ID of the NFT to rent.
    function rentNFT(uint256 _nftId) public onlyRole(RENTER_ROLE) {
        if (isRented) revert NFTAlreadyRented();
        if (_nftId != nftId) revert NotAuthorized();
        address owner = ownerOf(_nftId);
        _transfer(owner, msg.sender, _nftId);
        rentalStartTime = block.timestamp;
        isRented = true;
        emit NFTRented(_nftId, msg.sender);
    }

    /// @notice Allows the owner to withdraw the NFT after the rental period is over.
    /// @param _nftId The ID of the NFT to withdraw.
    function withdrawNFT(uint256 _nftId) public {
        if (!isRented) revert NFTNotRented();
        if (block.timestamp < rentalStartTime + rentalDuration) revert RentalPeriodNotOver();
        if (_nftId != nftId) revert NotAuthorized();
        address renter = ownerOf(_nftId);
        _transfer(renter, msg.sender, _nftId);
        isRented = false;
        emit NFTWithdrawn(_nftId);
    }

    // Override _update for transfer logic if needed
    function _update(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        super._update(from, to, tokenId, batchSize);
        // Custom transfer logic here if needed
    }
}
