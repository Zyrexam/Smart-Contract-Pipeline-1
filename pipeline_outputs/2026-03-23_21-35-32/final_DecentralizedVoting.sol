// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title DecentralizedVoting - A smart contract for decentralized voting where users can vote for proposals.
contract DecentralizedVoting {
    /// @notice Represents a proposal in the voting system.
    struct Proposal {
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        bool votingEnded;
    }

    /// @notice Array of all proposals.
    Proposal[] public proposals;

    /// @notice Mapping to track registered voters.
    mapping(address => bool) public voters;

    /// @notice Mapping to track if a voter has voted on a specific proposal.
    mapping(uint256 => mapping(address => bool)) public hasVoted;

    /// @notice Role-based access control for admin.
    address public admin;

    /// @notice Event emitted when a new proposal is created.
    event ProposalCreated(uint256 proposalId, string description);

    /// @notice Event emitted when a vote is cast.
    event VoteCast(address voter, uint256 proposalId);

    /// @notice Event emitted when voting ends for a proposal.
    event VotingEnded(uint256 proposalId);

    /// @notice Custom error for unauthorized access.
    error Unauthorized();

    /// @notice Custom error for already voted.
    error AlreadyVoted();

    /// @notice Custom error for voting period ended.
    error VotingPeriodEnded();

    /// @notice Modifier to restrict access to admin only.
    modifier onlyAdmin() {
        if (msg.sender != admin) revert Unauthorized();
        _;
    }

    /// @notice Modifier to restrict access to registered voters only.
    modifier onlyVoter() {
        if (!voters[msg.sender]) revert Unauthorized();
        _;
    }

    /// @notice Constructor to set the initial admin.
    constructor() {
        admin = msg.sender;
    }

    /// @notice Allows an admin to create a new proposal.
    /// @param description The description of the proposal.
    function createProposal(string calldata description) external onlyAdmin {
        proposals.push(Proposal({
            description: description,
            forVotes: 0,
            againstVotes: 0,
            votingEnded: false
        }));
        emit ProposalCreated(proposals.length - 1, description);
    }

    /// @notice Allows a voter to vote for a proposal.
    /// @param proposalId The ID of the proposal to vote on.
    function vote(uint256 proposalId) external onlyVoter {
        Proposal storage proposal = proposals[proposalId];

        // Automatically end voting if the period has ended
        if (block.timestamp > block.timestamp + 1 weeks && !proposal.votingEnded) {
            _endVoting(proposalId);
        }

        if (proposal.votingEnded) revert VotingPeriodEnded();
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();

        // Record the vote
        hasVoted[proposalId][msg.sender] = true;
        proposal.forVotes += 1; // Assuming a simple majority vote for demonstration
        emit VoteCast(msg.sender, proposalId);
    }

    /// @notice Allows an admin to end voting for a proposal.
    /// @param proposalId The ID of the proposal to end voting on.
    function endVoting(uint256 proposalId) external onlyAdmin {
        _endVoting(proposalId);
    }

    /// @notice Internal function to end voting for a proposal.
    /// @param proposalId The ID of the proposal to end voting on.
    function _endVoting(uint256 proposalId) internal {
        Proposal storage proposal = proposals[proposalId];
        proposal.votingEnded = true;
        emit VotingEnded(proposalId);
    }

    /// @notice Returns the results of a proposal.
    /// @param proposalId The ID of the proposal to get results for.
    /// @return results The number of votes for the proposal.
    function getProposalResults(uint256 proposalId) external view returns (uint256 results) {
        Proposal storage proposal = proposals[proposalId];
        return proposal.forVotes;
    }
}