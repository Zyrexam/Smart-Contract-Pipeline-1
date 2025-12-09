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

    struct Proposal {
        string description;
        uint256 voteCount;
        bool executed;
    }

    Proposal[] private proposals;
    mapping(address => uint256) private votes;
    mapping(address => uint256) public tokenHolders;

    bytes32 public constant TOKEN_HOLDER_ROLE = keccak256("TOKEN_HOLDER_ROLE");

    error NotTokenHolder();
    error AlreadyVoted();
    error InvalidProposal();
    error ProposalAlreadyExecuted();

    event ProposalSubmitted(uint256 proposalId, string description);
    event VoteCast(address indexed voter, uint256 proposalId, uint256 voteWeight);
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

    function submitProposal(string memory proposalDescription) public onlyTokenHolder {
        proposals.push(Proposal({
            description: proposalDescription,
            voteCount: 0,
            executed: false
        }));
        emit ProposalSubmitted(proposals.length - 1, proposalDescription);
    }

    function vote(uint256 proposalId, uint256 voteWeight) public onlyTokenHolder {
        if (proposalId >= proposals.length) revert InvalidProposal();
        if (votes[msg.sender] != 0) revert AlreadyVoted();

        proposals[proposalId].voteCount += voteWeight;
        votes[msg.sender] = voteWeight;

        emit VoteCast(msg.sender, proposalId, voteWeight);
    }

    function calculateResults(uint256 proposalId) private view returns (bool isApproved) {
        if (proposalId >= proposals.length) revert InvalidProposal();
        return proposals[proposalId].voteCount > quorum(proposalSnapshot(proposalId));
    }

    function executeApprovedAction(uint256 proposalId) private {
        if (proposalId >= proposals.length) revert InvalidProposal();
        if (proposals[proposalId].executed) revert ProposalAlreadyExecuted();

        if (calculateResults(proposalId)) {
            proposals[proposalId].executed = true;
            emit ProposalExecuted(proposalId);
        }
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
}
