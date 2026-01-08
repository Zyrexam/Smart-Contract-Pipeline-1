// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Lottery Contract
/// @notice This contract allows participants to enter a lottery and picks a winner using block.timestamp for randomness.
contract Lottery {
    address public owner;
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

    /// @dev Modifier to restrict access to the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    /// @dev Modifier to ensure the lottery has ended.
    modifier lotteryEnded() {
        if (block.timestamp < lotteryEndTime) revert LotteryNotEnded();
        _;
    }

    /// @dev Modifier to ensure the lottery has started.
    modifier lotteryStarted() {
        if (lotteryEndTime == 0) revert LotteryNotStarted();
        _;
    }

    /// @notice Constructor to set the contract deployer as the owner.
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows a participant to enter the lottery.
    /// @param participant The address of the participant.
    function enterLottery(address participant) external lotteryStarted {
        participants.push(participant);
        emit LotteryEntered(participant);
    }

    /// @notice Starts the lottery and sets the end time.
    /// @param duration The duration in seconds for which the lottery will run.
    function startLottery(uint256 duration) external onlyOwner {
        if (lotteryEndTime != 0) revert LotteryAlreadyStarted();
        lotteryEndTime = block.timestamp + duration;
    }

    /// @notice Picks a winner using block.timestamp for randomness.
    /// @return The address of the winner.
    function pickWinner() external onlyOwner lotteryEnded returns (address) {
        require(participants.length > 0, "No participants");
        uint256 randomIndex = uint256(keccak256(abi.encodePacked(block.timestamp, block.difficulty))) % participants.length;
        winner = participants[randomIndex];
        emit WinnerPicked(winner);
        return winner;
    }
}
