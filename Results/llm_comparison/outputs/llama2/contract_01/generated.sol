pragma solidity ^0.8.20;

contract RentalNFT {
    // Mapping of NFT IDs to renters
    mapping(address => mapping(uint256 => bool)) public renters;

    // Mapping of rental durations to NFT IDs
    mapping(uint256 => mapping(uint256 => bool)) public rentals;

    // Event emitted when an NFT is rented
    event RentedNFT(address indexed renter, uint256 indexed nftId, uint256 duration);

    // Function to rent an NFT for a fixed duration
    function rentNFT(uint256 nftId, uint256 duration) public {
        require(msg.sender != address(0), "Only validators can rent NFTs");
        require(duration > 0 && duration <= 100, "Invalid rental duration");

        // Check if the NFT is already rented
        require(!renters[nftId][msg.sender], "NFT is already rented");

        // Add the renter to the mapping
        renters[nftId][msg.sender] = true;

        // Add the rental duration to the mapping
        rentals[nftId][duration] = true;

        emit RentedNFT(msg.sender, nftId, duration);
    }

    // Function to unrent an NFT
    function unrentNFT(uint256 nftId) public {
        require(msg.sender != address(0), "Only validators can unrent NFTs");

        // Check if the NFT is rented
        require(renters[nftId][msg.sender], "NFT is not rented");

        // Remove the renter from the mapping
        renters[nftId][msg.sender] = false;

        emit RentedNFT(msg.sender, nftId, 0);
    }
}