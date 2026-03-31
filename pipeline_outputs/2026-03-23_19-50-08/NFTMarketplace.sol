// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract NFTMarketplace is ReentrancyGuard, AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant USER_ROLE = keccak256("USER_ROLE");

    mapping(uint256 => address) private nfts;
    mapping(uint256 => uint256) private nftPrices;
    mapping(uint256 => address) private nftOwners;

    event NFTListed(uint256 indexed nftId, address indexed seller, uint256 price);
    event NFTSold(uint256 indexed nftId, address indexed buyer, uint256 price);

    error NotAuthorized();
    error NFTAlreadyListed();
    error NFTNotListed();
    error IncorrectPrice();
    error TransferFailed();

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(USER_ROLE, msg.sender);
    }

    /**
     * @dev Allows a user to list an NFT for sale at a specified price.
     * @param nftId The ID of the NFT to list.
     * @param price The price at which the NFT is listed.
     */
    function listNFT(uint256 nftId, uint256 price) external onlyRole(USER_ROLE) {
        if (nfts[nftId] != address(0)) revert NFTAlreadyListed();
        nfts[nftId] = msg.sender;
        nftPrices[nftId] = price;
        nftOwners[nftId] = msg.sender;
        emit NFTListed(nftId, msg.sender, price);
    }

    /**
     * @dev Allows a user to buy a listed NFT by paying the specified price.
     * @param nftId The ID of the NFT to buy.
     */
    function buyNFT(uint256 nftId) external payable nonReentrant onlyRole(USER_ROLE) {
        address seller = nfts[nftId];
        uint256 price = nftPrices[nftId];
        if (seller == address(0)) revert NFTNotListed();
        if (msg.value != price) revert IncorrectPrice();

        nfts[nftId] = address(0);
        nftPrices[nftId] = 0;
        nftOwners[nftId] = msg.sender;

        (bool success, ) = seller.call{value: msg.value}("");
        if (!success) revert TransferFailed();

        emit NFTSold(nftId, msg.sender, price);
    }

    /**
     * @dev Allows a user to sell their NFT, transferring ownership to the buyer.
     * @param nftId The ID of the NFT to sell.
     */
    function sellNFT(uint256 nftId) external onlyRole(USER_ROLE) {
        if (nftOwners[nftId] != msg.sender) revert NotAuthorized();
        nfts[nftId] = address(0);
        nftPrices[nftId] = 0;
        nftOwners[nftId] = address(0);
    }
}
