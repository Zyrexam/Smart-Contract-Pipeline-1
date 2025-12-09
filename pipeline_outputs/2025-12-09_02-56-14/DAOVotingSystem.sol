// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DAOVotingSystem is Governor, GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction, Ownable {
    using SafeERC20 for IERC20;

    struct Proposal {
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
    }

    mapping(uint256 => Proposal) private proposals;
    mapping(address => mapping(uint256 => bool)) private votes;
    mapping(address => uint256) public tokenBalance;
    uint256 private proposalCount;

    error NotTokenHolder();
    error AlreadyVoted();
    error ProposalNotFound();
    error ProposalAlreadyExecuted();

    event ProposalSubmitted(uint256 proposalId, string description);
    event VoteCast(address voter, uint256 proposalId, bool support);
    event ProposalExecuted(uint256 proposalId);

    constructor(IVotes _token)
        Governor("DAOVotingSystem")
        GovernorSettings(1 /* 1 block */, 45818 /* 1 week */, 1)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(4) // Example quorum fraction
    {}

    modifier onlyTokenHolder() {
        if (tokenBalance[msg.sender] == 0) revert NotTokenHolder();
        _;
    }

    function submitProposal(string memory description) public onlyTokenHolder returns (uint256 proposalId) {
        proposalId = proposalCount++;
        proposals[proposalId] = Proposal({
            description: description,
            forVotes: 0,
            againstVotes: 0,
            executed: false
        });
        emit ProposalSubmitted(proposalId, description);
    }

    function vote(uint256 proposalId, bool support) public onlyTokenHolder {
        if (votes[msg.sender][proposalId]) revert AlreadyVoted();
        Proposal storage proposal = proposals[proposalId];
        if (bytes(proposal.description).length == 0) revert ProposalNotFound();

        votes[msg.sender][proposalId] = true;
        uint256 weight = getVotes(msg.sender, block.number - 1);

        if (support) {
            proposal.forVotes += weight;
        } else {
            proposal.againstVotes += weight;
        }

        emit VoteCast(msg.sender, proposalId, support);

        if (calculateResults(proposalId)) {
            executeProposal(proposalId);
        }
    }

    function calculateResults(uint256 proposalId) private view returns (bool approved) {
        Proposal storage proposal = proposals[proposalId];
        return proposal.forVotes > proposal.againstVotes;
    }

    function executeProposal(uint256 proposalId) private {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.executed) revert ProposalAlreadyExecuted();
        proposal.executed = true;
        emit ProposalExecuted(proposalId);
        // Execute proposal actions here
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
        return (token.totalSupply() * quorumNumerator(blockNumber)) / quorumDenominator();
    }
}
