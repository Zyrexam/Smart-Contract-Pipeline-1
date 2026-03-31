// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DecentralizedVoting {
    struct Proposal {
        string title;
        string description;
        bool isActive;
        mapping(address => uint256) votes;
    }[] proposals;

    function addProposal(string _title, string _description) public {
        proposals.push(Proposal(_title, _description, false, mapping()));
    }

    function voteForProposal(uint256 _proposalId, address _voter) public {
        require(_proposalId < proposals.length, "Invalid proposal ID");
        require(_voter != address(0), "Invalid voter address");

        Proposal storage proposal = proposals[_proposalId];
        require(proposition.isActive, "Proposal is not active");

        uint256 vote = proposal.votes[_voter].add(1);
        proposal.votes[_voter] = vote;
    }

    function getVoteCount() public view returns (uint256) {
        return proposals[0].votes[_voter];
    }
}