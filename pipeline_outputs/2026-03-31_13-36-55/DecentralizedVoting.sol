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
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
    }

    Proposal[] public proposals;
    mapping(uint256 => mapping(address => bool)) private hasVoted;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant VOTER_ROLE = keccak256("VOTER_ROLE");

    error NotAdmin();
    error NotVoter();
    error AlreadyVoted();
    error VotingEnded();
    error InvalidProposalId();

    event ProposalCreated(uint256 proposalId, string description);
    event VoteCast(address voter, uint256 proposalId);
    event VotingEnded(uint256 proposalId, bool success);

    constructor(IVotes token) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    function createProposal(string memory description) public onlyRole(ADMIN_ROLE) returns (uint256 proposalId) {
        proposalId = proposals.length;
        proposals.push(Proposal({
            description: description,
            forVotes: 0,
            againstVotes: 0,
            executed: false
        }));
        emit ProposalCreated(proposalId, description);
    }

    function vote(uint256 proposalId) public onlyRole(VOTER_ROLE) {
        if (proposalId >= proposals.length) revert InvalidProposalId();
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();
        if (proposals[proposalId].executed) revert VotingEnded();

        uint256 weight = getVotes(msg.sender, proposalSnapshot(proposalId));
        hasVoted[proposalId][msg.sender] = true;
        proposals[proposalId].forVotes += weight;

        emit VoteCast(msg.sender, proposalId);

        if (_quorumReached(proposalId) && _majorityReached(proposalId)) {
            _execute(proposalId);
        }
    }

    function endVoting(uint256 proposalId) public onlyRole(ADMIN_ROLE) returns (bool success) {
        if (proposalId >= proposals.length) revert InvalidProposalId();
        if (proposals[proposalId].executed) revert VotingEnded();

        success = _quorumReached(proposalId) && _majorityReached(proposalId);
        proposals[proposalId].executed = true;

        emit VotingEnded(proposalId, success);
    }

    function getProposalResults(uint256 proposalId) public view returns (uint256 votes) {
        if (proposalId >= proposals.length) revert InvalidProposalId();
        return proposals[proposalId].forVotes;
    }

    function _quorumReached(uint256 proposalId) internal view returns (bool) {
        return proposals[proposalId].forVotes >= quorum(proposalSnapshot(proposalId));
    }

    function _majorityReached(uint256 proposalId) internal view returns (bool) {
        return proposals[proposalId].forVotes > proposals[proposalId].againstVotes;
    }

    function _execute(uint256 proposalId) internal {
        proposals[proposalId].executed = true;
        emit VotingEnded(proposalId, true);
    }

    // Override required functions
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