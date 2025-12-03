// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract CarbonCreditNFT is ERC721Burnable, AccessControl, Ownable {
    // Custom errors
    error InvalidAddress();
    error AlreadyRedeemed();
    error NotOwner();

    // State variables
    uint256 public tokenId;
    mapping(uint256 => bool) private isRedeemed;

    // Events
    event Minted(address indexed to, uint256 indexed tokenId);
    event Redeemed(uint256 indexed tokenId);
    event Burned(uint256 indexed tokenId);

    // Role definitions
    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

    // Constructor with proper OpenZeppelin v5 initialization
    constructor() ERC721("CarbonCreditNFT", "CCNFT") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(OWNER_ROLE, msg.sender);
    }

    /**
     * @notice Mints a new carbon-credit NFT to the specified address.
     * @dev Restricted to owner.
     * @param to The address to mint the NFT to.
     * @return tokenId The ID of the minted NFT.
     */
    function mint(address to) external onlyRole(OWNER_ROLE) returns (uint256) {
        if (to == address(0)) revert InvalidAddress();
        uint256 newTokenId = tokenId;
        _mint(to, newTokenId);
        emit Minted(to, newTokenId);
        tokenId++;
        return newTokenId;
    }

    /**
     * @notice Redeems the NFT for carbon offsets and marks it as redeemed.
     * @dev Restricted to owner.
     * @param _tokenId The ID of the NFT to redeem.
     */
    function redeem(uint256 _tokenId) external onlyRole(OWNER_ROLE) {
        if (ownerOf(_tokenId) != msg.sender) revert NotOwner();
        if (isRedeemed[_tokenId]) revert AlreadyRedeemed();
        isRedeemed[_tokenId] = true;
        emit Redeemed(_tokenId);
        _burn(_tokenId);
    }

    /**
     * @notice Burns the NFT after it has been redeemed.
     * @dev Restricted to owner.
     * @param _tokenId The ID of the NFT to burn.
     */
    function burn(uint256 _tokenId) internal override {
        if (!isRedeemed[_tokenId]) revert AlreadyRedeemed();
        super.burn(_tokenId);
        emit Burned(_tokenId);
    }
}
