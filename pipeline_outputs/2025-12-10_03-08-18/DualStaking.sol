// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title DualStaking - A dual-staking contract where users earn rewards in two different tokens.
contract DualStaking {
    // State Variables
    address public stakeToken;
    address public rewardToken1;
    address public rewardToken2;
    uint256 public totalStaked;
    
    mapping(address => uint256) private userStakes;
    uint256 private rewardRate1;
    uint256 private rewardRate2;
    
    address private owner;

    // Events
    event Staked(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardsClaimed(address indexed user, uint256 reward1, uint256 reward2);

    // Custom Errors
    error NotOwner();
    error InsufficientStake();
    error TransferFailed();

    // Modifiers
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @dev Constructor to set the initial addresses for tokens and owner.
    /// @param _stakeToken The address of the token to be staked.
    /// @param _rewardToken1 The address of the first reward token.
    /// @param _rewardToken2 The address of the second reward token.
    constructor(address _stakeToken, address _rewardToken1, address _rewardToken2) {
        stakeToken = _stakeToken;
        rewardToken1 = _rewardToken1;
        rewardToken2 = _rewardToken2;
        owner = msg.sender;
    }

    /// @notice Allows users to stake a specified amount of tokens.
    /// @param amount The amount of tokens to stake.
    function stake(uint256 amount) external {
        require(amount > 0, "Amount must be greater than zero");
        
        // Transfer the stake tokens from the user to the contract
        (bool success, ) = stakeToken.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", msg.sender, address(this), amount));
        if (!success) revert TransferFailed();

        // Update user's stake and total staked amount
        userStakes[msg.sender] += amount;
        totalStaked += amount;

        emit Staked(msg.sender, amount);
    }

    /// @notice Allows users to withdraw a specified amount of their staked tokens.
    /// @param amount The amount of tokens to withdraw.
    function withdraw(uint256 amount) external {
        if (userStakes[msg.sender] < amount) revert InsufficientStake();

        // Update user's stake and total staked amount
        userStakes[msg.sender] -= amount;
        totalStaked -= amount;

        // Transfer the stake tokens back to the user
        (bool success, ) = stakeToken.call(abi.encodeWithSignature("transfer(address,uint256)", msg.sender, amount));
        if (!success) revert TransferFailed();

        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Allows users to claim their earned rewards in both reward tokens.
    function claimRewards() external {
        uint256 userStake = userStakes[msg.sender];
        require(userStake > 0, "No stake to claim rewards");

        uint256 reward1 = userStake * rewardRate1;
        uint256 reward2 = userStake * rewardRate2;

        // Transfer rewards to the user
        (bool success1, ) = rewardToken1.call(abi.encodeWithSignature("transfer(address,uint256)", msg.sender, reward1));
        if (!success1) revert TransferFailed();

        (bool success2, ) = rewardToken2.call(abi.encodeWithSignature("transfer(address,uint256)", msg.sender, reward2));
        if (!success2) revert TransferFailed();

        emit RewardsClaimed(msg.sender, reward1, reward2);
    }

    /// @notice Sets the reward rates for both reward tokens.
    /// @param rate1 The reward rate for the first reward token.
    /// @param rate2 The reward rate for the second reward token.
    function setRewardRates(uint256 rate1, uint256 rate2) external onlyOwner {
        rewardRate1 = rate1;
        rewardRate2 = rate2;
    }

    /// @notice Allows the owner to withdraw tokens from the contract.
    /// @param token The address of the token to withdraw.
    /// @param amount The amount of tokens to withdraw.
    function withdrawTokens(address token, uint256 amount) external onlyOwner {
        (bool success, ) = token.call(abi.encodeWithSignature("transfer(address,uint256)", owner, amount));
        if (!success) revert TransferFailed();
    }
}
