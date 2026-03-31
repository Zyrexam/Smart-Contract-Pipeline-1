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
        uint256 id;
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
    }

    bytes32 public constant TOKEN_HOLDER_ROLE = keccak256("TOKEN_HOLDER_ROLE");

    Proposal[] public proposals;
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    address public token;

    event ProposalCreated(uint256 proposalId, string description);
    event VoteCast(address voter, uint256 proposalId, bool support);

    error NotTokenHolder();
    error AlreadyVoted();
    error ProposalNotFound();
    error QuorumNotReached();
    error MajorityNotReached();

    constructor(
        IVotes tokenAddress
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        token = address(tokenAddress);
    }

    function propose(string memory description) public onlyRole(TOKEN_HOLDER_ROLE) returns (uint256 proposalId) {
        proposalId = proposals.length;
        proposals.push(Proposal(proposalId, description, 0, 0, false));
        emit ProposalCreated(proposalId, description);
    }

    function vote(uint256 proposalId, bool support) public onlyRole(TOKEN_HOLDER_ROLE) {
        if (proposalId >= proposals.length) revert ProposalNotFound();
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

    function getProposal(uint256 proposalId) public view returns (Proposal memory proposal) {
        if (proposalId >= proposals.length) revert ProposalNotFound();
        return proposals[proposalId];
    }

    function countVotes(uint256 proposalId) public view returns (uint256 voteCount) {
        if (proposalId >= proposals.length) revert ProposalNotFound();
        Proposal storage proposal = proposals[proposalId];
        return proposal.forVotes + proposal.againstVotes;
    }

    function _execute(uint256 proposalId) internal {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.executed) return;
        proposal.executed = true;
        // Execute proposal actions here
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