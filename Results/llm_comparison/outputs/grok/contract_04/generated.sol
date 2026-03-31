// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Crowdfunding {
    // Mapping of contributors and their contributions
    mapping(address => uint256) public contributions;

    // Funding goal
    uint256 public fundingGoal;

    // Current amount of funds raised
    uint256 public fundsRaised;

    // Project owner
    address public projectOwner;

    // Project name
    string public projectName;

    // Project description
    string public projectDescription;

    // Funding goal reached flag
    bool public fundingGoalReached;

    // Event emitted when a contribution is made
    event ContributionMade(address contributor, uint256 amount);

    // Event emitted when the funding goal is reached
    event FundingGoalReached();

    // Constructor to initialize the contract
    constructor(string memory _projectName, string memory _projectDescription, uint256 _fundingGoal) {
        projectOwner = msg.sender;
        projectName = _projectName;
        projectDescription = _projectDescription;
        fundingGoal = _fundingGoal;
        fundingGoalReached = false;
    }

    // Function to contribute funds
    function contribute(uint256 _amount) public {
        // Check if the contribution amount is valid
        require(_amount > 0, "Contribution amount must be greater than 0");

        // Check if the funding goal has been reached
        require(fundingGoalReached == false, "Funding goal has already been reached");

        // Update the funds raised
        fundsRaised += _amount;

        // Update the contributions mapping
        contributions[msg.sender] += _amount;

        // Emit the contribution made event
        emit ContributionMade(msg.sender, _amount);

        // Check if the funding goal has been reached
        if (fundsRaised >= fundingGoal) {
            fundingGoalReached = true;

            // Emit the funding goal reached event
            emit FundingGoalReached();
        }
    }

    // Function to get the project details
    function getProjectDetails() public view returns (string memory, string memory, uint256, uint256, bool) {
        return (projectName, projectDescription, fundingGoal, fundsRaised, fundingGoalReached);
    }
}