// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DAOGovernance {
    struct Proposal {
        string description;
        uint256 voteCount;
        bool executed;
        mapping(address => bool) voted;
    }

    address public chairperson;
    mapping(address => uint256) public tokenBalance;
    Proposal[] public proposals;

    event ProposalCreated(uint256 proposalId, string description);
    event Voted(uint256 proposalId, address voter);
    event ProposalExecuted(uint256 proposalId);

    modifier onlyChairperson() {
        require(msg.sender == chairperson, "Only chairperson can execute this");
        _;
    }

    modifier hasTokens() {
        require(tokenBalance[msg.sender] > 0, "Must hold tokens to participate");
        _;
    }

    constructor() {
        chairperson = msg.sender;
    }

    function depositTokens(uint256 amount) external {
        require(amount > 0, "Amount must be greater than zero");
        tokenBalance[msg.sender] += amount;
    }

    function createProposal(string memory description) external hasTokens {
        proposals.push(Proposal({
            description: description,
            voteCount: 0,
            executed: false
        }));
        emit ProposalCreated(proposals.length - 1, description);
    }

    function vote(uint256 proposalId) external hasTokens {
        Proposal storage proposal = proposals[proposalId];
        require(!proposal.voted[msg.sender], "Already voted");
        require(!proposal.executed, "Proposal already executed");

        proposal.voted[msg.sender] = true;
        proposal.voteCount += tokenBalance[msg.sender];
        emit Voted(proposalId, msg.sender);
    }

    function executeProposal(uint256 proposalId) external onlyChairperson {
        Proposal storage proposal = proposals[proposalId];
        require(!proposal.executed, "Proposal already executed");
        require(proposal.voteCount > 0, "No votes cast");

        proposal.executed = true;
        emit ProposalExecuted(proposalId);
    }

    function getProposal(uint256 proposalId) external view returns (string memory description, uint256 voteCount, bool executed) {
        Proposal storage proposal = proposals[proposalId];
        return (proposal.description, proposal.voteCount, proposal.executed);
    }
}