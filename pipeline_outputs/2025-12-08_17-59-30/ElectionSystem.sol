// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title ElectionSystem - A simple, tamper-proof election system for a small community or club
contract ElectionSystem {
    /// @notice Mapping to track registered voters
    mapping(address => bool) private voters;
    
    /// @notice Mapping to track votes received by each candidate
    mapping(address => uint256) private votes;
    
    /// @notice List of candidates participating in the election
    address[] public candidates;
    
    /// @notice Timestamp indicating the end of the voting period
    uint256 public votingPeriodEnd;
    
    /// @notice Boolean indicating if the winner has been declared
    bool private winnerDeclared;
    
    /// @notice Address of the winning candidate
    address public winner;
    
    /// @notice Address of the admin
    address private admin;
    
    /// @dev Custom error for unauthorized access
    error Unauthorized();
    
    /// @dev Custom error for invalid operations
    error InvalidOperation();
    
    /// @dev Custom error for invalid input
    error InvalidInput();
    
    /// @notice Event emitted when a voter is registered
    event VoterRegistered(address indexed voterAddress);
    
    /// @notice Event emitted when a candidate is added
    event CandidateAdded(address indexed candidateAddress);
    
    /// @notice Event emitted when a vote is cast
    event VoteCast(address indexed voterAddress, uint256 candidateIndex);
    
    /// @notice Event emitted when the winner is declared
    event WinnerDeclared(address indexed winnerAddress);
    
    /// @notice Modifier to restrict access to admin only
    modifier onlyAdmin() {
        if (msg.sender != admin) revert Unauthorized();
        _;
    }
    
    /// @notice Modifier to ensure function is called during voting period
    modifier onlyDuringVotingPeriod() {
        if (block.timestamp > votingPeriodEnd) revert InvalidOperation();
        _;
    }
    
    /// @notice Modifier to ensure function is called after voting period
    modifier onlyAfterVotingPeriod() {
        if (block.timestamp <= votingPeriodEnd) revert InvalidOperation();
        _;
    }
    
    /// @notice Modifier to ensure winner is declared only once
    modifier onlyOnce() {
        if (winnerDeclared) revert InvalidOperation();
        _;
    }
    
    /// @notice Constructor to set the admin
    constructor() {
        admin = msg.sender;
    }
    
    /// @notice Registers a voter by adding their address to the list of verified voters
    /// @param voterAddress The address of the voter to register
    function registerVoter(address voterAddress) external onlyAdmin {
        if (voters[voterAddress]) revert InvalidInput();
        voters[voterAddress] = true;
        emit VoterRegistered(voterAddress);
    }
    
    /// @notice Adds a candidate to the election
    /// @param candidateAddress The address of the candidate to add
    function addCandidate(address candidateAddress) external onlyAdmin {
        candidates.push(candidateAddress);
        emit CandidateAdded(candidateAddress);
    }
    
    /// @notice Starts the voting period for a specified duration
    /// @param duration The duration of the voting period in seconds
    function startVotingPeriod(uint256 duration) external onlyAdmin {
        votingPeriodEnd = block.timestamp + duration;
    }
    
    /// @notice Allows a registered voter to cast a vote for a candidate
    /// @param candidateIndex The index of the candidate in the candidates array
    function vote(uint256 candidateIndex) external onlyDuringVotingPeriod {
        if (!voters[msg.sender] || candidateIndex >= candidates.length) revert InvalidInput();
        if (votes[msg.sender] != 0) revert InvalidOperation();
        
        votes[candidates[candidateIndex]] += 1;
        votes[msg.sender] = 1; // Mark as voted
        emit VoteCast(msg.sender, candidateIndex);
        
        // Automatically declare winner if voting period has ended
        if (block.timestamp > votingPeriodEnd) {
            _declareWinner();
        }
    }
    
    /// @notice Automatically tabulates votes and declares the winner after the voting period ends
    function declareWinner() external onlyAdmin onlyAfterVotingPeriod onlyOnce {
        _declareWinner();
    }
    
    /// @dev Internal function to declare the winner
    function _declareWinner() internal {
        uint256 highestVotes = 0;
        address winningCandidate;
        
        for (uint256 i = 0; i < candidates.length; i++) {
            if (votes[candidates[i]] > highestVotes) {
                highestVotes = votes[candidates[i]];
                winningCandidate = candidates[i];
            }
        }
        
        winner = winningCandidate;
        winnerDeclared = true;
        emit WinnerDeclared(winner);
    }
}
