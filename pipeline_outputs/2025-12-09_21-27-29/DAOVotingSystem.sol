// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract DAOVotingSystem is Governor, GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction, AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant TOKEN_HOLDER_ROLE = keccak256("TOKEN_HOLDER_ROLE");

    struct Proposal {
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
    }

    mapping(uint256 => Proposal) private proposals;
    mapping(uint256 => mapping(address => bool)) private hasVoted;
    uint256 private proposalCount;

    error NotTokenHolder();
    error AlreadyVoted();
    error ProposalNotFound();
    error ProposalAlreadyExecuted();

    event ProposalSubmitted(uint256 proposalId, string description);
    event VoteCast(address indexed voter, uint256 proposalId, bool vote);
    event ProposalExecuted(uint256 proposalId);

    constructor(IVotes _token)
        Governor("DAOVotingSystem")
        GovernorSettings(1 /* 1 block */, 45818 /* 1 week */, 1)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(4)
        AccessControl()
    {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    modifier onlyTokenHolder() {
        if (!hasRole(TOKEN_HOLDER_ROLE, msg.sender)) revert NotTokenHolder();
        _;
    }

    function submitProposal(string memory description) public onlyTokenHolder returns (uint256 proposalId) {
        proposalId = proposalCount++;
        proposals[proposalId] = Proposal(description, 0, 0, false);
        emit ProposalSubmitted(proposalId, description);
    }

    function vote(uint256 proposalId, bool support) public onlyTokenHolder {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.executed) revert ProposalAlreadyExecuted();
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();

        uint256 weight = getVotes(msg.sender, proposalSnapshot(proposalId));
        if (support) {
            proposal.forVotes += weight;
        } else {
            proposal.againstVotes += weight;
        }
        hasVoted[proposalId][msg.sender] = true;
        emit VoteCast(msg.sender, proposalId, support);

        if (_calculateResults(proposalId)) {
            _executeProposal(proposalId);
        }
    }

    function _calculateResults(uint256 proposalId) private view returns (bool approved) {
        Proposal storage proposal = proposals[proposalId];
        uint256 totalVotes = proposal.forVotes + proposal.againstVotes;
        approved = proposal.forVotes > proposal.againstVotes && totalVotes >= quorum(proposalSnapshot(proposalId));
    }

    function _executeProposal(uint256 proposalId) private {
        Proposal storage proposal = proposals[proposalId];
        proposal.executed = true;
        emit ProposalExecuted(proposalId);
    }

    function votingDelay() public view override returns (uint256) {
        return 1;
    }

    function votingPeriod() public view override returns (uint256) {
        return 45818;
    }

    function proposalThreshold() public view override returns (uint256) {
        return 1;
    }

    function quorum(uint256 blockNumber) public view override returns (uint256) {
        return super.quorum(blockNumber);
    }
}
