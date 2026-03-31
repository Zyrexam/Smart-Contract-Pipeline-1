// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract RentalNFT is ERC721, ERC721Enumerable, ERC721Burnable, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    struct RentalInfo {
        address renter;
        uint256 rentalEndTime;
    }

    mapping(uint256 => RentalInfo) private _rentalInfo;

    event NFTMinted(uint256 tokenId, address owner);
    event NFTRented(uint256 tokenId, address renter, uint256 duration);
    event NFTReturned(uint256 tokenId, address renter);

    constructor() ERC721("RentalNFT", "RNFT") {}

    function _baseURI() internal pure override returns (string memory) {
        return "https://api.example.com/metadata/";
    }

    function safeMint(address to) public onlyOwner {
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        _safeMint(to, tokenId);
        emit NFTMinted(tokenId, to);
    }

    function rentNFT(uint256 tokenId, uint256 duration) external {
        require(_exists(tokenId), "Token does not exist");
        require(ownerOf(tokenId) != msg.sender, "Owner cannot rent their own NFT");
        require(_rentalInfo[tokenId].renter == address(0), "NFT is already rented");
        
        _rentalInfo[tokenId] = RentalInfo({
            renter: msg.sender,
            rentalEndTime: block.timestamp + duration
        });

        emit NFTRented(tokenId, msg.sender, duration);
    }

    function returnNFT(uint256 tokenId) external {
        require(_exists(tokenId), "Token does not exist");
        require(_rentalInfo[tokenId].renter == msg.sender, "Only the renter can return the NFT");
        require(block.timestamp >= _rentalInfo[tokenId].rentalEndTime, "Rental period has not ended");

        delete _rentalInfo[tokenId];
        emit NFTReturned(tokenId, msg.sender);
    }

    function isRented(uint256 tokenId) public view returns (bool) {
        return _rentalInfo[tokenId].renter != address(0);
    }

    function rentalEndTime(uint256 tokenId) public view returns (uint256) {
        require(isRented(tokenId), "NFT is not rented");
        return _rentalInfo[tokenId].rentalEndTime;
    }

    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize)
        internal
        override(ERC721, ERC721Enumerable)
    {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        require(_rentalInfo[tokenId].renter == address(0), "Rented NFT cannot be transferred");
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}