// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract DAOVotingSystem is Governor, GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction, AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant TOKEN_HOLDER_ROLE = keccak256("TOKEN_HOLDER_ROLE");

    struct Proposal {
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
    }

    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) private hasVoted;

    event ProposalSubmitted(uint256 proposalId, string description);
    event VoteCast(address indexed voter, uint256 proposalId, bool vote);
    event ProposalExecuted(uint256 proposalId);

    error NotTokenHolder();
    error AlreadyVoted();
    error ProposalNotExecutable();

    constructor(IVotes _token)
        Governor("DAOVotingSystem")
        GovernorSettings(1 /* 1 block */, 45818 /* 1 week */, 1e18)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(4)
        AccessControl()
    {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(TOKEN_HOLDER_ROLE, msg.sender);
    }

    modifier onlyTokenHolder() {
        if (!hasRole(TOKEN_HOLDER_ROLE, msg.sender)) revert NotTokenHolder();
        _;
    }

    function votingDelay() public view override returns (uint256) {
        return 1;
    }

    function votingPeriod() public view override returns (uint256) {
        return 45818;
    }

    function proposalThreshold() public view override returns (uint256) {
        return 1e18;
    }

    function quorum(uint256 blockNumber) public view override returns (uint256) {
        return super.quorum(blockNumber);
    }

    function submitProposal(string memory description) public onlyTokenHolder returns (uint256 proposalId) {
        proposalId = hashProposal(description);
        proposals[proposalId] = Proposal(description, 0, 0, false);
        emit ProposalSubmitted(proposalId, description);
    }

    function vote(uint256 proposalId, bool vote) public onlyTokenHolder {
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();

        uint256 weight = getVotes(msg.sender, proposalSnapshot(proposalId));
        if (vote) {
            proposals[proposalId].forVotes += weight;
        } else {
            proposals[proposalId].againstVotes += weight;
        }

        hasVoted[proposalId][msg.sender] = true;
        emit VoteCast(msg.sender, proposalId, vote);

        if (calculateResults(proposalId)) {
            executeProposal(proposalId);
        }
    }

    function calculateResults(uint256 proposalId) internal view returns (bool approved) {
        Proposal storage proposal = proposals[proposalId];
        uint256 totalVotes = proposal.forVotes + proposal.againstVotes;
        approved = proposal.forVotes > proposal.againstVotes && totalVotes >= quorum(proposalSnapshot(proposalId));
    }

    function executeProposal(uint256 proposalId) internal {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.executed || !calculateResults(proposalId)) revert ProposalNotExecutable();

        proposal.executed = true;
        emit ProposalExecuted(proposalId);
    }
}
