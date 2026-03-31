// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract NFTMarketplace is ReentrancyGuard, Ownable, AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant USER_ROLE = keccak256("USER_ROLE");

    mapping(uint256 => address) private nfts;
    mapping(uint256 => uint256) private listings;

    event NFTListed(uint256 indexed tokenId, uint256 price);
    event NFTSold(uint256 indexed tokenId, address indexed buyer);

    error NotAuthorized();
    error NotListed();
    error AlreadyListed();
    error InvalidPrice();
    error TransferFailed();

    constructor() Ownable(msg.sender) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(USER_ROLE, msg.sender);
    }

    /**
     * @dev Allows a user to list an NFT for sale.
     * @param tokenId The ID of the token to list.
     * @param price The price at which the token is listed.
     */
    function listNFT(uint256 tokenId, uint256 price) external onlyRole(USER_ROLE) {
        if (price == 0) revert InvalidPrice();
        if (listings[tokenId] != 0) revert AlreadyListed();

        listings[tokenId] = price;
        nfts[tokenId] = msg.sender;

        emit NFTListed(tokenId, price);
    }

    /**
     * @dev Allows a user to buy a listed NFT.
     * @param tokenId The ID of the token to buy.
     */
    function buyNFT(uint256 tokenId) external payable nonReentrant onlyRole(USER_ROLE) {
        uint256 price = listings[tokenId];
        address seller = nfts[tokenId];

        if (price == 0) revert NotListed();
        if (msg.value < price) revert InvalidPrice();

        listings[tokenId] = 0;
        nfts[tokenId] = address(0);

        (bool success, ) = seller.call{value: msg.value}("");
        if (!success) revert TransferFailed();

        IERC721(nfts[tokenId]).safeTransferFrom(seller, msg.sender, tokenId);

        emit NFTSold(tokenId, msg.sender);
    }

    /**
     * @dev Allows a user to sell their NFT.
     * @param tokenId The ID of the token to sell.
     */
    function sellNFT(uint256 tokenId) external onlyRole(USER_ROLE) {
        if (nfts[tokenId] != msg.sender) revert NotAuthorized();

        listings[tokenId] = 0;
        nfts[tokenId] = address(0);

        IERC721(nfts[tokenId]).safeTransferFrom(address(this), msg.sender, tokenId);
    }

    /**
     * @dev Allows the owner to withdraw funds from the marketplace.
     */
    function withdrawFunds() external onlyOwner {
        uint256 balance = address(this).balance;
        (bool success, ) = msg.sender.call{value: balance}("");
        if (!success) revert TransferFailed();
    }
}