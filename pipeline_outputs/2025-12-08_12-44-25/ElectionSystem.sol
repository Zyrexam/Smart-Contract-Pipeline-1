// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract ElectionSystem is Governor, GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction, AccessControl {
    // Custom errors
    error InvalidAddress();
    error VotingPeriodNotStarted();
    error VotingPeriodEnded();
    error AlreadyVoted();
    error WinnerAlreadyDeclared();
    error NotRegisteredVoter();

    // State variables
    mapping(address => bool) private voterRegistry;
    mapping(address => uint256) private votes;
    address[] public candidates;
    uint256 public votingPeriodEnd;
    bool private winnerDeclared;

    // Roles
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant VOTER_ROLE = keccak256("VOTER_ROLE");

    // Events
    event VoterRegistered(address indexed voterAddress);
    event VoteCast(address indexed voter, address indexed candidate);
    event WinnerDeclared(address indexed winner);

    // Constructor
    constructor(IVotes _token)
        Governor("ElectionSystem")
        GovernorSettings(1 /* voting delay */, 1 /* voting period */, 0 /* proposal threshold */)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(4)
    {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    // Modifiers
    modifier onlyDuringVotingPeriod() {
        if (block.timestamp > votingPeriodEnd) revert VotingPeriodEnded();
        _;
    }

    modifier onlyAfterVotingPeriod() {
        if (block.timestamp <= votingPeriodEnd) revert VotingPeriodNotStarted();
        _;
    }

    modifier onlyOnce() {
        if (winnerDeclared) revert WinnerAlreadyDeclared();
        _;
    }

    /// @notice Registers a voter by adding their address to the voter registry.
    /// @param voterAddress The address of the voter to register.
    function registerVoter(address voterAddress) external onlyRole(ADMIN_ROLE) {
        if (voterAddress == address(0)) revert InvalidAddress();
        voterRegistry[voterAddress] = true;
        _grantRole(VOTER_ROLE, voterAddress);
        emit VoterRegistered(voterAddress);
    }

    /// @notice Starts the voting period by setting the end time based on the provided duration.
    /// @param duration The duration of the voting period in seconds.
    function startVotingPeriod(uint256 duration) external onlyRole(ADMIN_ROLE) {
        votingPeriodEnd = block.timestamp + duration;
    }

    /// @notice Allows a registered voter to cast a vote for a candidate.
    /// @param candidate The address of the candidate to vote for.
    function vote(address candidate) external onlyRole(VOTER_ROLE) onlyDuringVotingPeriod {
        if (!voterRegistry[msg.sender]) revert NotRegisteredVoter();
        if (votes[msg.sender] != 0) revert AlreadyVoted();
        votes[candidate]++;
        emit VoteCast(msg.sender, candidate);
    }

    /// @notice Automatically tabulates votes and declares the winner after the voting period ends.
    /// @return winner The address of the winning candidate.
    function declareWinner() external onlyRole(ADMIN_ROLE) onlyAfterVotingPeriod onlyOnce returns (address winner) {
        uint256 highestVotes = 0;
        for (uint256 i = 0; i < candidates.length; i++) {
            if (votes[candidates[i]] > highestVotes) {
                highestVotes = votes[candidates[i]];
                winner = candidates[i];
            }
        }
        winnerDeclared = true;
        emit WinnerDeclared(winner);
    }

    // Override _update for transfer logic if needed
    function _update(address from, address to, uint256 value) internal override {
        // Custom transfer logic if needed
    }
}
