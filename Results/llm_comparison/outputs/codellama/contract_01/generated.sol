// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RentalNFT {
    struct NFT {
        address owner;
        uint256 tokenId;
        uint256 duration;
        uint256 startTime;
        bool isRented;
    }

    mapping(address => NFT[]) public nfts;

    function rentNFT(uint256 tokenId, uint256 duration) external {
        require(!nfts[msg.sender][tokenId].isRented, "NFT is already rented");
        require(duration > 0, "Invalid duration");

        nfts[msg.sender][tokenId] = NFT({
            owner: msg.sender,
            tokenId: tokenId,
            duration: duration,
            startTime: block.timestamp,
            isRented: true
        });
    }

    function returnNFT(uint256 tokenId) external {
        require(nfts[msg.sender][tokenId].isRented, "NFT is not rented");

        nfts[msg.sender][tokenId].isRented = false;
    }
}