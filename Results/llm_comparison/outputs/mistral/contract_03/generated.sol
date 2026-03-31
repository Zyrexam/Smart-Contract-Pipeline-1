// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DecentralizedVoting {
    struct Proposal {
        uint id;
        string title;
        mapping(address => bool) voters;
    }

    Proposal[] public proposals;

    function createProposal(string memory _title) external {
        Proposal memory newProposal;
        newProposal.id = proposals.length + 1;
        newProposal.title = _title;
        newProposal.voters = mapping(address => bool)(abi.call(_vote, newProposal.id));
        proposals.push(newProposal);
    }

    function _vote(uint _proposalId) internal {
        require(!_isVoted(_proposalId), "You have already voted on this proposal");
        emit Vote(_msg.sender, _proposalId);
        proposals[_proposalId].voters[_msg.sender] = true;
    }

    function _isVoted(uint _proposalId) internal view returns (bool) {
        return proposals[_proposalId].voters[_msg.sender];
    }

    event Vote(address indexed voter, uint indexed proposal);
}