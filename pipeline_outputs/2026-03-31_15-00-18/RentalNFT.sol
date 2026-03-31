// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RentalNFT - A rental NFT system where users can rent NFTs for a fixed duration.
/// @dev Implements role-based access control and rental logic for NFTs.
contract RentalNFT {
    /// @notice Address of the contract owner
    address public owner;

    /// @notice Mapping from NFT ID to its owner
    mapping(uint256 => address) public nftOwner;

    /// @notice Mapping from NFT ID to its current renter
    mapping(uint256 => address) public renter;

    /// @notice Mapping from NFT ID to the rental end time
    mapping(uint256 => uint256) public rentalEndTime;

    /// @notice Event emitted when a new NFT is minted
    event NFTMinted(uint256 indexed nftId, address indexed to);

    /// @notice Event emitted when an NFT is rented
    event NFTRented(uint256 indexed nftId, address indexed renter, uint256 rentalEndTime);

    /// @notice Event emitted when an NFT is returned
    event NFTReturned(uint256 indexed nftId, address indexed renter);

    /// @dev Error for unauthorized access
    error Unauthorized();

    /// @dev Error for invalid operation
    error InvalidOperation();

    /// @dev Error for rental period not ended
    error RentalPeriodNotEnded();

    /// @dev Modifier to restrict access to the owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @dev Modifier to restrict access to the renter of a specific NFT
    modifier onlyRenter(uint256 nftId) {
        if (msg.sender != renter[nftId]) revert Unauthorized();
        _;
    }

    /// @notice Constructor to set the contract owner
    constructor() {
        owner = msg.sender;
    }

    /// @notice Mints a new NFT to the specified address
    /// @param to The address to mint the NFT to
    function mint(address to) external onlyOwner {
        uint256 nftId = uint256(keccak256(abi.encodePacked(block.timestamp, to)));
        nftOwner[nftId] = to;
        emit NFTMinted(nftId, to);
    }

    /// @notice Sets the rental terms for a specific NFT
    /// @param nftId The ID of the NFT
    /// @param duration The rental duration in seconds
    function setRentalTerms(uint256 nftId, uint256 duration) external onlyOwner {
        if (nftOwner[nftId] == address(0)) revert InvalidOperation();
        rentalEndTime[nftId] = block.timestamp + duration;
    }

    /// @notice Allows a user to rent an NFT for a fixed duration
    /// @param nftId The ID of the NFT to rent
    function rentNFT(uint256 nftId) external {
        if (nftOwner[nftId] == address(0) || renter[nftId] != address(0)) revert InvalidOperation();
        renter[nftId] = msg.sender;
        rentalEndTime[nftId] = block.timestamp + rentalEndTime[nftId];
        emit NFTRented(nftId, msg.sender, rentalEndTime[nftId]);
    }

    /// @notice Allows the renter to return the NFT after the rental period
    /// @param nftId The ID of the NFT to return
    function returnNFT(uint256 nftId) external onlyRenter(nftId) {
        if (block.timestamp < rentalEndTime[nftId]) revert RentalPeriodNotEnded();
        renter[nftId] = address(0);
        emit NFTReturned(nftId, msg.sender);
    }
}