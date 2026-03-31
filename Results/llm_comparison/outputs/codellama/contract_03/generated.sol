// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DecentralizedVoting {
    struct Proposal {
        string name;
        uint256 votes;
    }

    mapping(address => bool) public voters;
    mapping(uint256 => Proposal) public proposals;

    function vote(uint256 proposalId) public {
        require(!voters[msg.sender], "Voter has already voted");
        require(proposalId < proposals.length, "Proposal does not exist");

        voters[msg.sender] = true;
        proposals[proposalId].votes += 1;
    }
}