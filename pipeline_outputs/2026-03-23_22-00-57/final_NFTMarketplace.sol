// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract NFTMarketplace is ReentrancyGuard, AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");
    bytes32 public constant USER_ROLE = keccak256("USER_ROLE");

    mapping(uint256 => address) private nfts;
    mapping(uint256 => uint256) private listings;
    mapping(address => uint256) private balances;

    event NFTListed(uint256 indexed tokenId, address indexed seller, uint256 price);
    event NFTSold(uint256 indexed tokenId, address indexed buyer, uint256 price);
    event ListingCancelled(uint256 indexed tokenId, address indexed seller);

    error NotAuthorized();
    error NFTAlreadyListed();
    error NFTNotListed();
    error InsufficientFunds();
    error TransferFailed();

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(OWNER_ROLE, msg.sender);
    }

    /**
     * @dev Allows a user to list an NFT for sale at a specified price.
     * @param tokenId The ID of the NFT to list.
     * @param price The price at which to list the NFT.
     */
    function listNFT(uint256 tokenId, uint256 price) external onlyRole(USER_ROLE) {
        if (listings[tokenId] != 0) revert NFTAlreadyListed();
        listings[tokenId] = price;
        nfts[tokenId] = msg.sender;
        emit NFTListed(tokenId, msg.sender, price);
    }

    /**
     * @dev Allows a user to buy a listed NFT.
     * @param tokenId The ID of the NFT to buy.
     */
    function buyNFT(uint256 tokenId) external payable nonReentrant onlyRole(USER_ROLE) {
        uint256 price = listings[tokenId];
        address seller = nfts[tokenId];
        if (price == 0) revert NFTNotListed();
        if (msg.value < price) revert InsufficientFunds();

        balances[seller] += msg.value;
        delete listings[tokenId];
        delete nfts[tokenId];

        IERC721(nfts[tokenId]).safeTransferFrom(seller, msg.sender, tokenId);

        emit NFTSold(tokenId, msg.sender, price);
    }

    /**
     * @dev Allows a user to withdraw their balance from the marketplace.
     */
    function withdrawFunds() external nonReentrant onlyRole(USER_ROLE) {
        uint256 amount = balances[msg.sender];
        if (amount == 0) revert TransferFailed();

        balances[msg.sender] = 0;
        (bool success, ) = msg.sender.call{value: amount}("");
        if (!success) revert TransferFailed();
    }

    /**
     * @dev Allows a user to cancel their NFT listing.
     * @param tokenId The ID of the NFT listing to cancel.
     */
    function cancelListing(uint256 tokenId) external onlyRole(USER_ROLE) {
        if (nfts[tokenId] != msg.sender) revert NotAuthorized();
        if (listings[tokenId] == 0) revert NFTNotListed();

        delete listings[tokenId];
        delete nfts[tokenId];

        emit ListingCancelled(tokenId, msg.sender);
    }
}