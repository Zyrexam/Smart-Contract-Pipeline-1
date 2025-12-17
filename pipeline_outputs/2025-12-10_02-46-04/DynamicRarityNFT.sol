// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title DynamicRarityNFT
 * @dev This smart contract creates an NFT with dynamic rarity, where the rarity changes based on user activity.
 */
contract DynamicRarityNFT is ERC721, Ownable {
    uint256 public rarity;
    mapping(address => uint256) private userActivity;
    uint256 private _tokenIdCounter;

    event RarityUpdated(uint256 indexed tokenId, uint256 newRarity);

    /**
     * @dev Initializes the contract by setting a `name` and a `symbol` to the token collection.
     */
    constructor() ERC721("DynamicRarityNFT", "DRNFT") Ownable(msg.sender) {
        rarity = 0;
    }

    /**
     * @dev Mints a new NFT to the specified address.
     * @param to The address to mint the NFT to.
     * @return tokenId The ID of the newly minted token.
     */
    function mint(address to) external onlyOwner returns (uint256 tokenId) {
        _tokenIdCounter++;
        tokenId = _tokenIdCounter;
        _mint(to, tokenId);
    }

    /**
     * @dev Allows a user to interact with the NFT, potentially affecting its rarity.
     * @param tokenId The ID of the token to interact with.
     */
    function interact(uint256 tokenId) external {
        if (ownerOf(tokenId) != msg.sender) revert NotTokenOwner();
        userActivity[msg.sender]++;
        _updateRarity(tokenId);
    }

    /**
     * @dev Updates the rarity of the NFT based on user activity.
     * @param tokenId The ID of the token whose rarity is to be updated.
     */
    function _updateRarity(uint256 tokenId) private {
        uint256 newRarity = userActivity[msg.sender] * 10; // Example logic for updating rarity
        rarity = newRarity;
        emit RarityUpdated(tokenId, newRarity);
    }

    error NotTokenOwner();
}
