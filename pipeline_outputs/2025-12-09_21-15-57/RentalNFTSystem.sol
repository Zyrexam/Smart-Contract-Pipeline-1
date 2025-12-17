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

    // State variables
    struct Rental {
        address originalOwner;
        address renter;
        uint256 startTime;
        uint256 duration;
    }

    mapping(uint256 => Rental) private _rentals;

    bytes32 public constant RENTER_ROLE = keccak256("RENTER_ROLE");

    // Events
    event NFTSetForRent(uint256 indexed nftId, uint256 duration);
    event NFTRented(uint256 indexed nftId, address indexed renter);
    event NFTWithdrawn(uint256 indexed nftId);

    // Constructor with proper OpenZeppelin v5 initialization
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
    /// @param duration The duration for which the NFT is available for rent.
    function setNFTForRent(uint256 nftId, uint256 duration) external payable onlyOwner {
        if (_rentals[nftId].renter != address(0)) revert NFTAlreadyRented();
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
        if (rental.renter != address(0)) revert NFTAlreadyRented();
        rental.renter = msg.sender;
        rental.startTime = block.timestamp;
        _transfer(rental.originalOwner, msg.sender, nftId);
        emit NFTRented(nftId, msg.sender);
    }

    /// @notice Allows the owner to withdraw the NFT after the rental period is over.
    /// @param nftId The ID of the NFT to withdraw.
    function withdrawNFT(uint256 nftId) external {
        Rental storage rental = _rentals[nftId];
        if (msg.sender != rental.originalOwner) revert NotAuthorized();
        if (block.timestamp < rental.startTime + rental.duration) revert RentalPeriodNotOver();
        _transfer(rental.renter, rental.originalOwner, nftId);
        delete _rentals[nftId];
        emit NFTWithdrawn(nftId);
    }

    // Override _update for transfer logic
    function _update(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        super._update(from, to, tokenId, batchSize);
        // Custom logic for rental transfers can be added here
    }
}
