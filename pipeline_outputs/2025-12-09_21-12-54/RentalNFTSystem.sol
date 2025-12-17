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
    error RentalPeriodNotEnded();
    error NFTAlreadyRented();
    error NFTNotRented();

    // State variables
    struct Rental {
        address originalOwner;
        address renter;
        uint256 startTime;
        uint256 duration;
    }

    mapping(uint256 => Rental) public rentals;

    bytes32 public constant RENTER_ROLE = keccak256("RENTER_ROLE");

    // Events
    event NFTListed(uint256 indexed nftId, uint256 rentalDuration);
    event NFTRented(uint256 indexed nftId, address indexed renter, uint256 rentalStartTime);
    event NFTWithdrawn(uint256 indexed nftId);

    // Constructor with proper OpenZeppelin v5 initialization
    constructor(address initialOwner) ERC721("NFT", "NFT") Ownable(initialOwner) {
        _grantRole(DEFAULT_ADMIN_ROLE, initialOwner);
    }

    /// @notice Mints a new NFT to the specified address.
    /// @param to The address to mint the NFT to.
    /// @param tokenId The ID of the NFT to mint.
    function safeMint(address to, uint256 tokenId) public onlyOwner {
        _safeMint(to, tokenId);
    }

    /// @notice Allows the owner to list an NFT for rent with a specified duration.
    /// @param nftId The ID of the NFT to list for rent.
    /// @param rentalDuration The duration for which the NFT can be rented.
    function listNFTForRent(uint256 nftId, uint256 rentalDuration) public payable onlyOwner {
        if (ownerOf(nftId) != msg.sender) revert NotNFTOwner();
        if (rentals[nftId].renter != address(0)) revert NFTAlreadyRented();

        rentals[nftId] = Rental({
            originalOwner: msg.sender,
            renter: address(0),
            startTime: 0,
            duration: rentalDuration
        });

        emit NFTListed(nftId, rentalDuration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param nftId The ID of the NFT to rent.
    function rentNFT(uint256 nftId) public payable onlyRole(RENTER_ROLE) {
        Rental storage rental = rentals[nftId];
        if (rental.originalOwner == address(0)) revert NFTNotRented();
        if (rental.renter != address(0)) revert NFTAlreadyRented();

        rental.renter = msg.sender;
        rental.startTime = block.timestamp;

        _transfer(rental.originalOwner, msg.sender, nftId);

        emit NFTRented(nftId, msg.sender, block.timestamp);
    }

    /// @notice Allows the owner to withdraw the NFT after the rental period has ended.
    /// @param nftId The ID of the NFT to withdraw.
    function withdrawNFT(uint256 nftId) public {
        Rental storage rental = rentals[nftId];
        if (rental.originalOwner != msg.sender) revert NotNFTOwner();
        if (block.timestamp < rental.startTime + rental.duration) revert RentalPeriodNotEnded();

        address renter = rental.renter;
        rental.renter = address(0);
        rental.startTime = 0;

        _transfer(renter, rental.originalOwner, nftId);

        emit NFTWithdrawn(nftId);
    }

    // Override _update for transfer logic if needed
    function _update(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        super._update(from, to, tokenId, batchSize);
    }
}
