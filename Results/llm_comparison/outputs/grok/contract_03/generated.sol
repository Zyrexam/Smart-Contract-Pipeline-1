// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DecentralizedVoting {
    // Mapping of users to their votes
    mapping(address => uint256) public userVotes;

    // Mapping of proposals to their vote counts
    mapping(uint256 => uint256) public proposalVotes;

    // Mapping of proposals to their proposal details
    mapping(uint256 => Proposal) public proposals;

    // Array of all proposals
    uint256[] public proposalIds;

    // Enum for vote status
    enum VoteStatus { Active, Closed }

    // Struct for proposal details
    struct Proposal {
        uint256 id;
        string title;
        string description;
        VoteStatus status;
    }

    // Event emitted when a user votes
    event UserVoted(uint256 indexed proposalId, address indexed voter);

    // Event emitted when a proposal is created
    event ProposalCreated(uint256 indexed proposalId, string title, string description);

    // Event emitted when a proposal is closed
    event ProposalClosed(uint256 indexed proposalId);

    // Function to create a new proposal
    function createProposal(string memory _title, string memory _description) public {
        // Generate a new proposal ID
        uint256 proposalId = proposalIds.length;

        // Add the proposal to the mapping
        proposals[proposalId] = Proposal(proposalId, _title, _description, VoteStatus.Active);

        // Add the proposal ID to the array
        proposalIds.push(proposalId);

        // Emit the proposal created event
        emit ProposalCreated(proposalId, _title, _description);
    }

    // Function to vote for a proposal
    function vote(uint256 _proposalId) public {
        // Check if the proposal exists
        require(proposals[_proposalId].id != 0, "Proposal does not exist");

        // Check if the proposal is active
        require(proposals[_proposalId].status == VoteStatus.Active, "Proposal is not active");

        // Check if the user has already voted
        require(userVotes[msg.sender] == 0, "User has already voted");

        // Increment the user's vote count
        userVotes[msg.sender] = 1;

        // Increment the proposal's vote count
        proposalVotes[_proposalId]++;

        // Emit the user voted event
        emit UserVoted(_proposalId, msg.sender);
    }

    // Function to close a proposal
    function closeProposal(uint256 _proposalId) public {
        // Check if the proposal exists
        require(proposals[_proposalId].id != 0, "Proposal does not exist");

        // Check if the proposal is active
        require(proposals[_proposalId].status == VoteStatus.Active, "Proposal is not active");

        // Set the proposal's status to closed
        proposals[_proposalId].status = VoteStatus.Closed;

        // Emit the proposal closed event
        emit ProposalClosed(_proposalId);
    }
}