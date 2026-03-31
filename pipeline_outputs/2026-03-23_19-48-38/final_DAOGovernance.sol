// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract DAOGovernance is Governor, GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction, AccessControl {
    using SafeERC20 for IERC20;

    struct Proposal {
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
    }

    Proposal[] private proposals;
    mapping(uint256 => mapping(address => bool)) private hasVoted;

    bytes32 public constant TOKEN_HOLDER_ROLE = keccak256("TOKEN_HOLDER_ROLE");

    event ProposalCreated(uint256 proposalId, string description);
    event VoteCast(address indexed voter, uint256 proposalId, bool support);

    error NotTokenHolder();
    error AlreadyVoted();
    error InvalidProposalId();
    error ProposalAlreadyExecuted();

    constructor(IVotes token)
        Governor("DAOGovernance")
        GovernorSettings(1 /* 1 block */, 45818 /* 1 week */, 1)
        GovernorVotes(token)
        GovernorVotesQuorumFraction(4)
    {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    function propose(string memory proposalDescription) public onlyRole(TOKEN_HOLDER_ROLE) returns (uint256 proposalId) {
        proposalId = proposals.length;
        proposals.push(Proposal({
            description: proposalDescription,
            forVotes: 0,
            againstVotes: 0,
            executed: false
        }));
        emit ProposalCreated(proposalId, proposalDescription);
    }

    function vote(uint256 proposalId, bool support) public onlyRole(TOKEN_HOLDER_ROLE) {
        if (proposalId >= proposals.length) revert InvalidProposalId();
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();

        Proposal storage proposal = proposals[proposalId];
        uint256 weight = getVotes(msg.sender, proposalSnapshot(proposalId));

        if (support) {
            proposal.forVotes += weight;
        } else {
            proposal.againstVotes += weight;
        }

        hasVoted[proposalId][msg.sender] = true;
        emit VoteCast(msg.sender, proposalId, support);

        if (proposal.forVotes > proposal.againstVotes && proposal.forVotes + proposal.againstVotes >= quorum(proposalSnapshot(proposalId))) {
            _execute(proposalId);
        }
    }

    function _execute(uint256 proposalId) internal {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.executed) revert ProposalAlreadyExecuted();

        proposal.executed = true;
        // Execute proposal logic here
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
