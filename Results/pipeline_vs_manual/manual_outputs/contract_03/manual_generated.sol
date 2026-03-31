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

    modifier onlyChairperson() {
        require(msg.sender == chairperson, "Only chairperson can call this function.");
        _;
    }

    constructor(string[] memory proposalNames) {
        chairperson = msg.sender;
        for (uint i = 0; i < proposalNames.length; i++) {
            proposals.push(Proposal({
                description: proposalNames[i],
                voteCount: 0
            }));
        }
    }

    function giveRightToVote(address voter) external onlyChairperson {
        require(!voters[voter].hasVoted, "The voter already voted.");
        voters[voter].hasVoted = false;
    }

    function vote(uint proposalId) external {
        Voter storage sender = voters[msg.sender];
        require(!sender.hasVoted, "Already voted.");
        require(proposalId < proposals.length, "Invalid proposal ID.");

        sender.hasVoted = true;
        sender.votedProposalId = proposalId;

        proposals[proposalId].voteCount += 1;
    }

    function winningProposal() public view returns (uint winningProposalId) {
        uint winningVoteCount = 0;
        for (uint i = 0; i < proposals.length; i++) {
            if (proposals[i].voteCount > winningVoteCount) {
                winningVoteCount = proposals[i].voteCount;
                winningProposalId = i;
            }
        }
    }

    function winnerDescription() external view returns (string memory winnerDescription) {
        winnerDescription = proposals[winningProposal()].description;
    }
}