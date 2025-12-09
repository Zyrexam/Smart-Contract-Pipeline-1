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
    error AlreadyVoted();
    error VotingPeriodNotEnded();
    error WinnerAlreadyDeclared();

    // State variables
    mapping(address => bool) private voters;
    mapping(address => uint256) private votes;
    address[] public candidates;
    uint256 public votingPeriodEnd;
    bool private winnerDeclared;
    address public winner;

    // Roles
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant VOTER_ROLE = keccak256("VOTER_ROLE");

    // Events
    event VoterRegistered(address indexed voterAddress);
    event CandidateAdded(address indexed candidateAddress);
    event VoteCast(address indexed voterAddress, uint256 candidateIndex);
    event WinnerDeclared(address indexed winnerAddress);

    // Constructor
    constructor(IVotes _token)
        Governor("ElectionSystem")
        GovernorSettings(1 /* voting delay */, 1 weeks /* voting period */, 1 /* proposal threshold */)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(4)
    {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    // Modifiers
    modifier onlyDuringVotingPeriod() {
        require(block.timestamp <= votingPeriodEnd, "Voting period has ended");
        _;
    }

    modifier onlyAfterVotingPeriod() {
        require(block.timestamp > votingPeriodEnd, "Voting period not ended");
        _;
    }

    modifier onlyOnce() {
        require(!winnerDeclared, "Winner already declared");
        _;
    }

    /// @notice Registers a voter by adding their address to the list of verified voters.
    /// @param voterAddress The address of the voter to register.
    function registerVoter(address voterAddress) public onlyRole(ADMIN_ROLE) {
        if (voterAddress == address(0)) revert InvalidAddress();
        voters[voterAddress] = true;
        emit VoterRegistered(voterAddress);
    }

    /// @notice Adds a candidate to the election.
    /// @param candidateAddress The address of the candidate to add.
    function addCandidate(address candidateAddress) public onlyRole(ADMIN_ROLE) {
        if (candidateAddress == address(0)) revert InvalidAddress();
        candidates.push(candidateAddress);
        emit CandidateAdded(candidateAddress);
    }

    /// @notice Starts the voting period for a specified duration.
    /// @param duration The duration of the voting period in seconds.
    function startVotingPeriod(uint256 duration) public onlyRole(ADMIN_ROLE) {
        votingPeriodEnd = block.timestamp + duration;
    }

    /// @notice Allows a registered voter to cast a vote for a candidate.
    /// @param candidateIndex The index of the candidate in the candidates array.
    function vote(uint256 candidateIndex) public onlyRole(VOTER_ROLE) onlyDuringVotingPeriod {
        if (!voters[msg.sender]) revert AlreadyVoted();
        voters[msg.sender] = false; // Mark as voted
        votes[candidates[candidateIndex]] += 1;
        emit VoteCast(msg.sender, candidateIndex);
        _autoTabulate();
    }

    /// @notice Automatically tabulates votes and declares the winner after the voting period ends.
    function declareWinner() public onlyRole(ADMIN_ROLE) onlyAfterVotingPeriod onlyOnce returns (address winnerAddress) {
        _autoTabulate();
        return winner;
    }

    // Internal function to automatically tabulate votes
    function _autoTabulate() internal onlyAfterVotingPeriod onlyOnce {
        uint256 highestVotes = 0;
        address currentWinner;
        for (uint256 i = 0; i < candidates.length; i++) {
            if (votes[candidates[i]] > highestVotes) {
                highestVotes = votes[candidates[i]];
                currentWinner = candidates[i];
            }
        }
        winner = currentWinner;
        winnerDeclared = true;
        emit WinnerDeclared(winner);
    }

    // Override required functions
    function votingDelay() public view override returns (uint256) {
        return 1; // 1 block
    }

    function votingPeriod() public view override returns (uint256) {
        return 1 weeks;
    }

    function proposalThreshold() public view override returns (uint256) {
        return 1;
    }

    function quorum(uint256) public view override returns (uint256) {
        return 4;
    }
}
