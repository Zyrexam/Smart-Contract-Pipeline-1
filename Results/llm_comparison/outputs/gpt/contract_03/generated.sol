// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DecentralizedVoting {
    struct Proposal {
        string description;
        uint voteCount;
    }

    struct Voter {
        bool hasVoted;
        uint votedProposalId;
    }

    address public chairperson;
    mapping(address => Voter) public voters;
    Proposal[] public proposals;

    event ProposalAdded(uint proposalId, string description);
    event Voted(address voter, uint proposalId);

    modifier onlyChairperson() {
        require(msg.sender == chairperson, "Only chairperson can call this function.");
        _;
    }

    modifier hasNotVoted() {
        require(!voters[msg.sender].hasVoted, "You have already voted.");
        _;
    }

    constructor(string[] memory proposalDescriptions) {
        chairperson = msg.sender;
        for (uint i = 0; i < proposalDescriptions.length; i++) {
            proposals.push(Proposal({
                description: proposalDescriptions[i],
                voteCount: 0
            }));
            emit ProposalAdded(i, proposalDescriptions[i]);
        }
    }

    function vote(uint proposalId) external hasNotVoted {
        require(proposalId < proposals.length, "Invalid proposal ID.");
        voters[msg.sender] = Voter({
            hasVoted: true,
            votedProposalId: proposalId
        });
        proposals[proposalId].voteCount += 1;
        emit Voted(msg.sender, proposalId);
    }

    function getWinningProposal() external view returns (uint winningProposalId) {
        uint winningVoteCount = 0;
        for (uint i = 0; i < proposals.length; i++) {
            if (proposals[i].voteCount > winningVoteCount) {
                winningVoteCount = proposals[i].voteCount;
                winningProposalId = i;
            }
        }
    }

    function getProposalDescription(uint proposalId) external view returns (string memory) {
        require(proposalId < proposals.length, "Invalid proposal ID.");
        return proposals[proposalId].description;
    }

    function getProposalVoteCount(uint proposalId) external view returns (uint) {
        require(proposalId < proposals.length, "Invalid proposal ID.");
        return proposals[proposalId].voteCount;
    }
}