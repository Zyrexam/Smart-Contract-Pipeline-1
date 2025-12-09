// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title ElectionSystem - A simple, tamper-proof election system for a small community or club
contract ElectionSystem {
    // State variables
    mapping(address => bool) private voterRegistry;
    mapping(address => bool) public hasVoted;
    mapping(address => uint256) public candidateVotes;
    mapping(address => bool) public isCandidate;
    address[] public candidates;
    uint256 public votingPeriodEnd;
    address public winner;
    address private admin;
    bool private winnerDeclared;

    // Events
    event VoterRegistered(address indexed voter);
    event VoteCast(address indexed voter, address indexed candidate);
    event WinnerDeclared(address indexed winner);

    // Modifiers
    modifier onlyAdmin() {
        if (msg.sender != admin) revert NotAdmin();
        _;
    }

    modifier onlyDuringVotingPeriod() {
        if (block.timestamp > votingPeriodEnd) revert VotingPeriodEnded();
        _;
    }

    modifier onlyAfterVotingPeriod() {
        if (block.timestamp <= votingPeriodEnd) revert VotingPeriodNotEnded();
        _;
    }

    modifier onlyRegisteredVoter() {
        if (!voterRegistry[msg.sender]) revert NotRegisteredVoter();
        _;
    }

    // Custom errors
    error NotAdmin();
    error VotingPeriodEnded();
    error VotingPeriodNotEnded();
    error NotRegisteredVoter();
    error AlreadyVoted();
    error CandidateAlreadyExists();
    error CandidateDoesNotExist();

    /// @notice Constructor to set the admin of the contract
    constructor() {
        admin = msg.sender;
    }

    /// @notice Sets the end time for the voting period
    /// @param endTime The timestamp when the voting period ends
    function setVotingPeriod(uint256 endTime) external onlyAdmin {
        votingPeriodEnd = endTime;
    }

    /// @notice Registers a voter by verifying their identity
    /// @param voter The address of the voter to register
    function registerVoter(address voter) external onlyAdmin {
        voterRegistry[voter] = true;
        emit VoterRegistered(voter);
    }

    /// @notice Adds a candidate to the election
    /// @param candidate The address of the candidate to add
    function addCandidate(address candidate) external onlyAdmin {
        if (isCandidate[candidate]) revert CandidateAlreadyExists();
        isCandidate[candidate] = true;
        candidates.push(candidate);
    }

    /// @notice Allows a registered voter to cast a vote for a candidate
    /// @param candidate The address of the candidate to vote for
    function vote(address candidate) external onlyDuringVotingPeriod onlyRegisteredVoter {
        // Automatically tabulate if voting period has ended
        if (block.timestamp > votingPeriodEnd && !winnerDeclared) {
            _autoTabulate();
        }

        if (hasVoted[msg.sender]) revert AlreadyVoted();
        if (!isCandidate[candidate]) revert CandidateDoesNotExist();

        hasVoted[msg.sender] = true;
        candidateVotes[candidate] += 1;
        emit VoteCast(msg.sender, candidate);
    }

    /// @notice Automatically tabulates votes and declares the winner after the voting period ends
    function declareWinner() external onlyAfterVotingPeriod {
        if (!winnerDeclared) {
            _autoTabulate();
        }
    }

    /// @dev Internal function to tabulate votes and declare the winner
    function _autoTabulate() internal {
        uint256 highestVotes = 0;
        address currentWinner;

        for (uint256 i = 0; i < candidates.length; i++) {
            address candidate = candidates[i];
            uint256 votesCount = candidateVotes[candidate];
            if (votesCount > highestVotes) {
                highestVotes = votesCount;
                currentWinner = candidate;
            }
        }

        winner = currentWinner;
        winnerDeclared = true;
        emit WinnerDeclared(winner);
    }
}
