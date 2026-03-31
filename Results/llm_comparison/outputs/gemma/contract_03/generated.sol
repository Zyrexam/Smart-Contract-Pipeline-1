pragma solidity ^0.8.20;

contract Voting {

    // Contract state
    struct Proposal {
        string title;
        uint256 support;
        uint256 opposition;
    }

    // Mapping of proposals to voters
    mapping(uint256 => address) private voters;

    // List of proposals
    Proposal[] public proposals;

    // Function to add a proposal
    function addProposal(string memory _title, uint256 _support, uint256 _opposition) public {
        proposals.push(Proposal(_title, _support, _opposition));
    }

    // Function to vote for a proposal
    function vote(uint256 _proposalId) public {
        // Check if the voter is already registered
        require(voters[msg.address] != address(0), "Already registered");

        // Get the proposal
        Proposal memory proposal = proposals[_proposalId];

        // Increment the vote count for the proposal
        voters[msg.address] = proposal.title;

        // Check if the voter has enough votes to vote
        require(proposal.support > 0 && proposal.support > proposal.opposition, "Insufficient votes");
    }

    // Function to get the winning proposal
    function getWinner() public view returns (uint256) {
        // Find the proposal with the highest support
        uint256 highestSupport = 0;
        uint256 winningProposalId = 0;
        for (uint256 i = 0; i < proposals.length; i++) {
            if (proposals[i].support > highestSupport) {
                highestSupport = proposals[i].support;
                winningProposalId = i;
            }
        }

        // Return the winning proposal ID
        return winningProposalId;
    }
}