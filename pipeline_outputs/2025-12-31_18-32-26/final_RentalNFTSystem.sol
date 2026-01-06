// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract RentalNFTSystem is ERC721, AccessControl, Ownable {
    // Custom errors
    error InvalidAddress();
    error NotRenter();
    error NotOwner();
    error AlreadyRented();
    error RentalPeriodNotOver();

    // State variables
    struct Rental {
        address originalOwner;
        address renter;
        uint256 startTime;
        uint256 duration;
    }

    mapping(uint256 => Rental) private _rentals;

    // Events
    event NFTSetForRent(uint256 indexed nftId, uint256 duration);
    event NFTRented(uint256 indexed nftId, address indexed renter);
    event NFTReturned(uint256 indexed nftId, address indexed renter);
    event NFTWithdrawn(uint256 indexed nftId);

    // Roles
    bytes32 public constant RENTER_ROLE = keccak256("RENTER_ROLE");

    // Constructor
    constructor() ERC721("NFT", "NFT") Ownable(msg.sender) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /// @notice Mints a new NFT to the specified address.
    /// @param to The address to mint the NFT to.
    /// @param tokenId The ID of the NFT to mint.
    function safeMint(address to, uint256 tokenId) public onlyOwner {
        _safeMint(to, tokenId);
    }

    /// @notice Allows the owner to set an NFT for rent with a specified duration.
    /// @param nftId The ID of the NFT to set for rent.
    /// @param duration The duration for which the NFT can be rented.
    function setNFTForRent(uint256 nftId, uint256 duration) external payable onlyOwner {
        if (ownerOf(nftId) != msg.sender) revert NotOwner();
        if (_rentals[nftId].renter != address(0)) revert AlreadyRented();

        _rentals[nftId] = Rental({
            originalOwner: msg.sender,
            renter: address(0),
            startTime: 0,
            duration: duration
        });

        emit NFTSetForRent(nftId, duration);
    }

    /// @notice Allows a user to rent an NFT for the specified duration.
    /// @param nftId The ID of the NFT to rent.
    function rentNFT(uint256 nftId) external payable onlyRole(RENTER_ROLE) {
        Rental storage rental = _rentals[nftId];
        if (rental.originalOwner == address(0)) revert InvalidAddress();
        if (rental.renter != address(0)) revert AlreadyRented();

        rental.renter = msg.sender;
        rental.startTime = block.timestamp;

        _transfer(rental.originalOwner, msg.sender, nftId);

        emit NFTRented(nftId, msg.sender);
    }

    /// @notice Allows the renter to return the NFT after the rental period.
    /// @param nftId The ID of the NFT to return.
    function returnNFT(uint256 nftId) external onlyRole(RENTER_ROLE) {
        Rental storage rental = _rentals[nftId];
        if (rental.renter != msg.sender) revert NotRenter();
        if (block.timestamp < rental.startTime + rental.duration) revert RentalPeriodNotOver();

        address originalOwner = rental.originalOwner;
        rental.renter = address(0);
        rental.startTime = 0;

        _transfer(msg.sender, originalOwner, nftId);

        emit NFTReturned(nftId, msg.sender);
    }

    /// @notice Allows the owner to withdraw the NFT if it is not rented.
    /// @param nftId The ID of the NFT to withdraw.
    function withdrawNFT(uint256 nftId) external onlyOwner {
        Rental storage rental = _rentals[nftId];
        if (rental.renter != address(0)) revert AlreadyRented();

        address originalOwner = rental.originalOwner;
        rental.originalOwner = address(0);

        _transfer(address(this), originalOwner, nftId);

        emit NFTWithdrawn(nftId);
    }

    // Override _update for custom transfer logic
    function _update(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        super._update(from, to, tokenId, batchSize);
        // Custom transfer logic if needed
    }
}
