// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract DecentralizedVoting is Governor, GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction, AccessControl {
    using SafeERC20 for IERC20;

    struct Proposal {
        string description;
        uint forVotes;
        uint againstVotes;
        bool executed;
        bool ended;
    }

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant VOTER_ROLE = keccak256("VOTER_ROLE");

    Proposal[] public proposals;
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    mapping(address => bool) public voters;

    error NotAuthorized();
    error AlreadyVoted();
    error VotingEnded();
    error ProposalNotFound();
    error VotingNotEnded();

    event ProposalCreated(uint proposalId, string description);
    event VoteCast(address voter, uint proposalId);
    event VotingEnded(uint proposalId);

    constructor(IVotes token) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    function createProposal(string memory description) public onlyRole(ADMIN_ROLE) returns (uint proposalId) {
        proposalId = proposals.length;
        proposals.push(Proposal(description, 0, 0, false, false));
        emit ProposalCreated(proposalId, description);
    }

    function vote(uint proposalId) public onlyRole(VOTER_ROLE) {
        if (proposalId >= proposals.length) revert ProposalNotFound();
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();
        if (proposals[proposalId].ended) revert VotingEnded();

        uint256 weight = getVotes(msg.sender, proposalSnapshot(proposalId));
        proposals[proposalId].forVotes += weight;
        hasVoted[proposalId][msg.sender] = true;

        emit VoteCast(msg.sender, proposalId);

        if (_checkQuorumAndMajority(proposalId)) {
            _executeProposal(proposalId);
        }
    }

    function endVoting(uint proposalId) public onlyRole(ADMIN_ROLE) {
        if (proposalId >= proposals.length) revert ProposalNotFound();
        if (proposals[proposalId].ended) revert VotingEnded();

        proposals[proposalId].ended = true;
        emit VotingEnded(proposalId);

        if (_checkQuorumAndMajority(proposalId)) {
            _executeProposal(proposalId);
        }
    }

    function getProposalResults(uint proposalId) public view returns (uint results) {
        if (proposalId >= proposals.length) revert ProposalNotFound();
        Proposal storage proposal = proposals[proposalId];
        if (!proposal.ended) revert VotingNotEnded();

        results = proposal.forVotes;
    }

    function _checkQuorumAndMajority(uint proposalId) internal view returns (bool) {
        Proposal storage proposal = proposals[proposalId];
        uint256 totalVotes = proposal.forVotes + proposal.againstVotes;
        return proposal.forVotes > proposal.againstVotes && totalVotes >= quorum(proposalSnapshot(proposalId));
    }

    function _executeProposal(uint proposalId) internal {
        Proposal storage proposal = proposals[proposalId];
        proposal.executed = true;
        // Add execution logic here
    }

    // Override required functions
    function votingDelay() public view override returns (uint256) {
        return 1; // 1 block
    }

    function votingPeriod() public view override returns (uint256) {
        return 45818; // 1 week
    }

    function proposalThreshold() public view override returns (uint256) {
        return 0;
    }

    function quorum(uint256 blockNumber) public view override returns (uint256) {
        return super.quorum(blockNumber);
    }
}