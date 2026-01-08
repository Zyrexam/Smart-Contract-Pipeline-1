// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ReentrancyGuard} from "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {SafeERC20, IERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/// @title Lottery Contract
/// @notice This contract allows participants to enter a lottery and picks a winner using Chainlink VRF for randomness.
contract Lottery is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");
    address[] public participants;
    address public winner;
    uint256 public lotteryEndTime;

    /// @notice Emitted when a participant enters the lottery.
    /// @param participant The address of the participant.
    event LotteryEntered(address indexed participant);

    /// @notice Emitted when a winner is picked.
    /// @param winner The address of the winner.
    event WinnerPicked(address indexed winner);

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for lottery not ended.
    error LotteryNotEnded();

    /// @dev Custom error for lottery already started.
    error LotteryAlreadyStarted();

    /// @dev Custom error for lottery not started.
    error LotteryNotStarted();

    /// @dev Custom error for no participants.
    error NoParticipants();

    /// @dev Modifier to ensure the lottery has ended.
    modifier lotteryEnded() {
        if (block.timestamp <= lotteryEndTime) revert LotteryNotEnded();
        _;
    }

    /// @dev Modifier to ensure the lottery has started.
    modifier lotteryStarted() {
        if (lotteryEndTime == 0 || block.timestamp >= lotteryEndTime) revert LotteryNotStarted();
        _;
    }

    /// @notice Constructor to set the contract deployer as the owner.
    constructor() {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(OWNER_ROLE, msg.sender);
    }

    /// @notice Allows a participant to enter the lottery.
    /// @param participant The address of the participant.
    function enterLottery(address participant) external lotteryStarted nonReentrant {
        participants.push(participant);
        emit LotteryEntered(participant);
    }

    /// @notice Starts the lottery and sets the end time.
    /// @param duration The duration in seconds for which the lottery will run.
    function startLottery(uint256 duration) external onlyRole(OWNER_ROLE) {
        if (lotteryEndTime != 0 && block.timestamp < lotteryEndTime) revert LotteryAlreadyStarted();
        lotteryEndTime = block.timestamp + duration;
    }

    /// @notice Picks a winner using Chainlink VRF for randomness.
    /// @return The address of the winner.
    function pickWinner() external onlyRole(OWNER_ROLE) lotteryEnded nonReentrant returns (address) {
        if (participants.length == 0) revert NoParticipants();
        uint256 randomIndex = uint256(keccak256(abi.encodePacked(blockhash(block.number - 1), block.timestamp))) % participants.length;
        winner = participants[randomIndex];
        emit WinnerPicked(winner);
        return winner;
    }
}