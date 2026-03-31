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
    error InvalidProposal();

    event ProposalCreated(uint proposalId, string description);
    event VoteCast(address voter, uint proposalId);
    event VotingEnded(uint proposalId);

    constructor(IVotes token) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    function createProposal(string memory description) public onlyRole(ADMIN_ROLE) {
        proposals.push(Proposal({
            description: description,
            forVotes: 0,
            againstVotes: 0,
            executed: false,
            ended: false
        }));
        emit ProposalCreated(proposals.length - 1, description);
    }

    function vote(uint proposalId) public onlyRole(VOTER_ROLE) {
        if (proposalId >= proposals.length) revert InvalidProposal();
        Proposal storage proposal = proposals[proposalId];
        if (proposal.ended) revert VotingEnded();
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();

        uint256 weight = getVotes(msg.sender, proposalSnapshot(proposalId));
        if (weight == 0) revert NotAuthorized();

        proposal.forVotes += weight;
        hasVoted[proposalId][msg.sender] = true;
        emit VoteCast(msg.sender, proposalId);

        if (proposal.forVotes > proposal.againstVotes && proposal.forVotes >= quorum(proposalSnapshot(proposalId))) {
            proposal.executed = true;
            proposal.ended = true;
            emit VotingEnded(proposalId);
        }
    }

    function endVoting(uint proposalId) public onlyRole(ADMIN_ROLE) {
        if (proposalId >= proposals.length) revert InvalidProposal();
        Proposal storage proposal = proposals[proposalId];
        if (proposal.ended) revert VotingEnded();

        proposal.ended = true;
        emit VotingEnded(proposalId);
    }

    function getProposalResults(uint proposalId) public view returns (uint results) {
        if (proposalId >= proposals.length) revert InvalidProposal();
        Proposal storage proposal = proposals[proposalId];
        return proposal.forVotes;
    }

    function votingDelay() public view override returns (uint256) {
        return super.votingDelay();
    }

    function votingPeriod() public view override returns (uint256) {
        return super.votingPeriod();
    }

    function proposalThreshold() public view override returns (uint256) {
        return super.proposalThreshold();
    }

    function quorum(uint256 blockNumber) public view override returns (uint256) {
        return super.quorum(blockNumber);
    }
}