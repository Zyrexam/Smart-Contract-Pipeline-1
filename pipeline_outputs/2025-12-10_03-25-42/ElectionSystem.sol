// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title ElectionSystem - A simple, tamper-proof election system for a small community or club
contract ElectionSystem {
    address public admin;
    address[] public candidates;
    uint256 public votingPeriodEnd;
    address public winner;

    mapping(address => bool) private voters;
    mapping(address => bool) public hasVoted;
    mapping(address => uint256) public candidateVotes;
    mapping(address => bool) public isCandidate;

    /// @notice Emitted when a voter is registered
    /// @param voterAddress The address of the registered voter
    event VoterRegistered(address indexed voterAddress);

    /// @notice Emitted when a vote is cast
    /// @param voter The address of the voter
    /// @param candidate The address of the candidate voted for
    event VoteCast(address indexed voter, address indexed candidate);

    /// @notice Emitted when a winner is declared
    /// @param winner The address of the winning candidate
    event WinnerDeclared(address indexed winner);

    /// @dev Ensures that the function can only be called during the voting period
    modifier onlyDuringVoting() {
        require(block.timestamp <= votingPeriodEnd, "Voting period has ended");
        _;
    }

    /// @dev Ensures that the function can only be called after the voting period has ended
    modifier onlyAfterVoting() {
        require(block.timestamp > votingPeriodEnd, "Voting period is still active");
        _;
    }

    /// @dev Restricts access to admin-only functions
    modifier onlyAdmin() {
        require(msg.sender == admin, "Caller is not the admin");
        _;
    }

    /// @dev Restricts access to functions for registered voters only
    modifier onlyVoter() {
        require(voters[msg.sender], "Caller is not a registered voter");
        _;
    }

    /// @notice Initializes the contract setting the deployer as the initial admin
    constructor() {
        admin = msg.sender;
    }

    /// @notice Registers a voter by verifying their identity and allowing them to vote
    /// @param voterAddress The address of the voter to register
    function registerVoter(address voterAddress) external onlyAdmin {
        if (voters[voterAddress]) revert("Voter already registered");
        voters[voterAddress] = true;
        emit VoterRegistered(voterAddress);
    }

    /// @notice Starts the voting period for a specified duration
    /// @param duration The duration of the voting period in seconds
    function startVoting(uint256 duration) external onlyAdmin {
        require(votingPeriodEnd == 0, "Voting already started");
        votingPeriodEnd = block.timestamp + duration;
    }

    /// @notice Allows a registered voter to cast a vote for a candidate
    /// @param candidate The address of the candidate to vote for
    function vote(address candidate) external onlyVoter onlyDuringVoting {
        // Automatically tabulate if voting period has ended
        if (block.timestamp > votingPeriodEnd && winner == address(0)) {
            _autoTabulate();
        }

        if (hasVoted[msg.sender]) revert("Already voted");
        if (!isCandidate[candidate]) revert("Invalid candidate");

        hasVoted[msg.sender] = true;
        candidateVotes[candidate] += 1;
        emit VoteCast(msg.sender, candidate);
    }

    /// @notice Ends the voting period, tabulates votes, and declares the winner
    function endVoting() external onlyAdmin onlyAfterVoting {
        _autoTabulate();
    }

    /// @dev Internal function to automatically tabulate votes and declare the winner
    function _autoTabulate() internal {
        uint256 highestVotes = 0;
        address currentWinner = address(0);

        for (uint256 i = 0; i < candidates.length; i++) {
            address candidate = candidates[i];
            uint256 votesForCandidate = candidateVotes[candidate];
            if (votesForCandidate > highestVotes) {
                highestVotes = votesForCandidate;
                currentWinner = candidate;
            }
        }

        winner = currentWinner;
        emit WinnerDeclared(winner);
    }
}
