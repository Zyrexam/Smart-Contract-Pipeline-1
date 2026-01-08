// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import { VRFConsumerBase } from "@openzeppelin/contracts/utils/cryptography/VRFConsumerBase.sol";
import { SafeERC20, IERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title SecureLottery
 * @dev Secure contract using Chainlink VRF for randomness
 */
contract SecureLottery is Ownable, ReentrancyGuard, VRFConsumerBase {
    using SafeERC20 for IERC20;

    uint256 public ticketPrice = 0.1 ether;
    address public winner;
    bool public ended;
    address[] public players;

    bytes32 internal keyHash;
    uint256 internal fee;
    uint256 public randomResult;

    error IncorrectTicketPrice();
    error LotteryEnded();
    error NoPlayers();
    error AlreadyEnded();
    error NotEnoughLink();
    error LotteryNotEnded();
    error NoLinkToWithdraw();

    constructor(
        address _vrfCoordinator,
        address _linkToken,
        bytes32 _keyHash,
        uint256 _fee
    ) VRFConsumerBase(_vrfCoordinator, _linkToken) {
        keyHash = _keyHash;
        fee = _fee;
    }

    function enter() external payable nonReentrant {
        if (msg.value != ticketPrice) revert IncorrectTicketPrice();
        if (ended) revert LotteryEnded();
        players.push(msg.sender);
    }

    function pickWinner() external onlyOwner nonReentrant {
        if (ended) revert AlreadyEnded();
        if (players.length == 0) revert NoPlayers();
        if (LINK.balanceOf(address(this)) < fee) revert NotEnoughLink();
        requestRandomness(keyHash, fee);
    }

    function fulfillRandomness(bytes32, uint256 randomness) internal override {
        randomResult = randomness;
        uint256 randomIndex = randomResult % players.length;
        winner = players[randomIndex];
        ended = true;
    }

    function withdraw() external onlyOwner nonReentrant {
        if (!ended) revert LotteryNotEnded();
        payable(owner()).transfer(address(this).balance);
    }

    function withdrawLink() external onlyOwner nonReentrant {
        uint256 linkBalance = LINK.balanceOf(address(this));
        if (linkBalance == 0) revert NoLinkToWithdraw();
        LINK.transfer(owner(), linkBalance);
    }
}