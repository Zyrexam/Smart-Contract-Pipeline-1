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
        bool votingEnded;
    }

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant VOTER_ROLE = keccak256("VOTER_ROLE");

    Proposal[] public proposals;
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    mapping(address => bool) public voters;

    event ProposalCreated(uint256 indexed proposalId, string description);
    event VoteCast(address indexed voter, uint256 indexed proposalId);
    event VotingEnded(uint256 indexed proposalId);

    error NotAdmin();
    error NotVoter();
    error AlreadyVoted();
    error VotingEnded();
    error ProposalNotExecutable();

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
            votingEnded: false
        }));
        emit ProposalCreated(proposals.length - 1, description);
    }

    function vote(uint256 proposalId) public onlyRole(VOTER_ROLE) {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.votingEnded) revert VotingEnded();
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();

        uint256 weight = getVotes(msg.sender, proposalSnapshot(proposalId));
        proposal.forVotes += weight;
        hasVoted[proposalId][msg.sender] = true;

        emit VoteCast(msg.sender, proposalId);

        if (proposal.forVotes > proposal.againstVotes && proposal.forVotes + proposal.againstVotes >= quorum(proposalSnapshot(proposalId))) {
            proposal.executed = true;
            _execute(proposalId);
        }
    }

    function endVoting(uint256 proposalId) public onlyRole(ADMIN_ROLE) {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.votingEnded) revert VotingEnded();

        proposal.votingEnded = true;
        emit VotingEnded(proposalId);

        if (proposal.forVotes > proposal.againstVotes && proposal.forVotes + proposal.againstVotes >= quorum(proposalSnapshot(proposalId))) {
            proposal.executed = true;
            _execute(proposalId);
        }
    }

    function getProposalResults(uint256 proposalId) public view returns (uint256 results) {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.forVotes > proposal.againstVotes && proposal.forVotes + proposal.againstVotes >= quorum(proposalSnapshot(proposalId))) {
            return proposal.forVotes;
        }
        return 0;
    }

    function votingDelay() public pure override returns (uint256) {
        return 1;
    }

    function votingPeriod() public pure override returns (uint256) {
        return 45818;
    }

    function proposalThreshold() public pure override returns (uint256) {
        return 0;
    }

    function quorum(uint256 blockNumber) public view override returns (uint256) {
        return super.quorum(blockNumber);
    }

    function _execute(uint256 proposalId) internal {
        // Custom execution logic
    }
}