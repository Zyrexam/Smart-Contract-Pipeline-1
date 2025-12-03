// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DynamicRarityNFT is ERC721, Ownable {
    // Custom errors
    error InvalidAddress();
    error NotOwner();

    // State variables
    mapping(uint256 => uint256) private tokenRarity;
    mapping(address => uint256) private userActivity;

    // Events
    event RarityUpdated(uint256 indexed tokenId, uint256 newRarity);

    // Constructor with proper OpenZeppelin v5 initialization
    constructor() ERC721("NFT", "NFT") Ownable(msg.sender) {}

    /**
     * @notice Mints a new NFT to the specified address.
     * @param to The address to mint the NFT to.
     * @return tokenId The ID of the minted token.
     */
    function mint(address to) public onlyOwner returns (uint256 tokenId) {
        if (to == address(0)) revert InvalidAddress();
        tokenId = totalSupply() + 1;
        _mint(to, tokenId);
    }

    /**
     * @notice Updates the rarity of a token based on user activity.
     * @param tokenId The ID of the token to update.
     * @param activityScore The new activity score to set.
     */
    function updateRarity(uint256 tokenId, uint256 activityScore) public onlyOwner {
        tokenRarity[tokenId] = activityScore;
        emit RarityUpdated(tokenId, activityScore);
    }

    /**
     * @notice Returns the current rarity of the specified token.
     * @param tokenId The ID of the token to query.
     * @return rarity The current rarity of the token.
     */
    function getRarity(uint256 tokenId) public view returns (uint256 rarity) {
        return tokenRarity[tokenId];
    }

    /**
     * @dev Override _update to handle transfer logic if needed.
     */
    function _update(address from, address to, uint256 tokenId, uint256 batchSize) internal override {
        super._update(from, to, tokenId, batchSize);
        // Custom logic can be added here
    }
}
