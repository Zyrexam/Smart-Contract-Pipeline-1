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
    mapping(address => bool) private voters;
    mapping(uint256 => uint256) public votes;
    mapping(uint256 => mapping(address => bool)) private hasVoted;

    bytes32 public constant USER_ROLE = keccak256("USER_ROLE");

    error AlreadyVoted();
    error NotEnoughVotes();
    error ProposalAlreadyExecuted();

    event VoteCast(address indexed voter, uint256 indexed proposalId);
    event ProposalAdded(uint256 indexed proposalId, string description);

    constructor(IVotes token)
        Governor("DecentralizedVoting")
        GovernorSettings(1 /* 1 block */, 45818 /* 1 week */, 1)
        GovernorVotes(token)
        GovernorVotesQuorumFraction(4)
    {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    function votingDelay() public view override returns (uint256) {
        return 1; // 1 block
    }

    function votingPeriod() public view override returns (uint256) {
        return 45818; // 1 week
    }

    function proposalThreshold() public view override returns (uint256) {
        return 1;
    }

    function quorum(uint256 blockNumber) public view override returns (uint256) {
        return super.quorum(blockNumber);
    }

    function vote(uint256 proposalId) public onlyRole(USER_ROLE) {
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();
        uint256 weight = getVotes(msg.sender, proposalSnapshot(proposalId));
        if (weight == 0) revert NotEnoughVotes();

        proposals[proposalId].forVotes += weight;
        hasVoted[proposalId][msg.sender] = true;

        emit VoteCast(msg.sender, proposalId);

        if (proposals[proposalId].forVotes > proposals[proposalId].againstVotes &&
            proposals[proposalId].forVotes + proposals[proposalId].againstVotes >= quorum(proposalSnapshot(proposalId))) {
            _execute(proposalId);
        }
    }

    function addProposal(string memory description) public returns (uint256 proposalId) {
        proposalId = proposals.length;
        proposals.push(Proposal({
            description: description,
            forVotes: 0,
            againstVotes: 0,
            executed: false
        }));

        emit ProposalAdded(proposalId, description);
    }

    function _execute(uint256 proposalId) internal {
        if (proposals[proposalId].executed) revert ProposalAlreadyExecuted();
        proposals[proposalId].executed = true;
        // Execute proposal logic here
    }
}
