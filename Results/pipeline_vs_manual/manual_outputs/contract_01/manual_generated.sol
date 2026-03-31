// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract RentalNFT is ERC721, ERC721Enumerable, ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    struct RentalInfo {
        address renter;
        uint256 rentalEndTime;
    }

    mapping(uint256 => RentalInfo) private _rentalInfo;
    mapping(uint256 => uint256) private _rentalPrices;

    event NFTMinted(uint256 tokenId, address owner);
    event NFTRented(uint256 tokenId, address renter, uint256 duration);

    constructor() ERC721("RentalNFT", "RNFT") {}

    function safeMint(address to, string memory uri, uint256 rentalPrice) public onlyOwner {
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
        _rentalPrices[tokenId] = rentalPrice;
        emit NFTMinted(tokenId, to);
    }

    function rentNFT(uint256 tokenId, uint256 duration) public payable {
        require(_exists(tokenId), "Token does not exist");
        require(ownerOf(tokenId) != msg.sender, "Owner cannot rent their own NFT");
        require(_rentalInfo[tokenId].renter == address(0) || block.timestamp > _rentalInfo[tokenId].rentalEndTime, "NFT is currently rented");
        require(msg.value >= _rentalPrices[tokenId] * duration, "Insufficient payment");

        _rentalInfo[tokenId] = RentalInfo({
            renter: msg.sender,
            rentalEndTime: block.timestamp + duration
        });

        payable(ownerOf(tokenId)).transfer(msg.value);
        emit NFTRented(tokenId, msg.sender, duration);
    }

    function getRentalInfo(uint256 tokenId) public view returns (address renter, uint256 rentalEndTime) {
        require(_exists(tokenId), "Token does not exist");
        RentalInfo memory info = _rentalInfo[tokenId];
        return (info.renter, info.rentalEndTime);
    }

    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize) internal override(ERC721, ERC721Enumerable) {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        require(_rentalInfo[tokenId].renter == address(0) || block.timestamp > _rentalInfo[tokenId].rentalEndTime, "NFT is currently rented");
    }

    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721Enumerable) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}