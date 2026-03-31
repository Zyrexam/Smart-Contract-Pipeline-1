// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration.
contract RentalNFT {
    /// @notice Emitted when a new NFT is minted.
    /// @param to The address receiving the minted NFT.
    /// @param tokenId The ID of the minted NFT.
    event NFTMinted(address indexed to, uint256 indexed tokenId);

    /// @notice Emitted when the rental price of an NFT is set.
    /// @param tokenId The ID of the NFT.
    /// @param price The rental price set for the NFT.
    event NFTPriceSet(uint256 indexed tokenId, uint256 price);

    /// @notice Emitted when an NFT is rented.
    /// @param renter The address renting the NFT.
    /// @param tokenId The ID of the rented NFT.
    /// @param rentedUntil The timestamp until which the NFT is rented.
    event NFTRented(address indexed renter, uint256 indexed tokenId, uint256 rentedUntil);

    address public owner;
    uint256 public rentalDuration;
    mapping(uint256 => uint256) public rentalPrice;
    mapping(uint256 => uint256) public rentedUntil;

    error NotOwner();
    error AlreadyRented();
    error InsufficientPayment();
    error NotRenter();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyRenter(uint256 tokenId) {
        if (block.timestamp < rentedUntil[tokenId]) revert AlreadyRented();
        _;
    }

    constructor(uint256 _rentalDuration) {
        owner = msg.sender;
        rentalDuration = _rentalDuration;
    }

    /// @notice Mint a new NFT to a specified address.
    /// @param to The address to receive the minted NFT.
    /// @param tokenId The ID of the NFT to mint.
    function mint(address to, uint256 tokenId) external onlyOwner {
        // Minting logic here (not implemented as this is a custom NFT system)
        emit NFTMinted(to, tokenId);
    }

    /// @notice Set the rental price for a specific NFT.
    /// @param tokenId The ID of the NFT.
    /// @param price The rental price to set.
    function setRentalPrice(uint256 tokenId, uint256 price) external onlyOwner {
        rentalPrice[tokenId] = price;
        emit NFTPriceSet(tokenId, price);
    }

    /// @notice Rent an NFT for the specified duration.
    /// @param tokenId The ID of the NFT to rent.
    function rentNFT(uint256 tokenId) external payable onlyRenter(tokenId) {
        uint256 price = rentalPrice[tokenId];
        if (msg.value < price) revert InsufficientPayment();

        rentedUntil[tokenId] = block.timestamp + rentalDuration;
        emit NFTRented(msg.sender, tokenId, rentedUntil[tokenId]);
    }

    /// @notice Get rental information for a specific NFT.
    /// @param tokenId The ID of the NFT.
    /// @return price The rental price of the NFT.
    /// @return duration The rental duration.
    /// @return rentedUntil The timestamp until which the NFT is rented.
    function getRentalInfo(uint256 tokenId) external view returns (uint256 price, uint256 duration, uint256 rentedUntilTimestamp) {
        price = rentalPrice[tokenId];
        duration = rentalDuration;
        rentedUntilTimestamp = rentedUntil[tokenId];
    }
}