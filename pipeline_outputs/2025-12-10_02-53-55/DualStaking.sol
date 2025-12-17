// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title DualStaking - A dual-staking contract where users earn rewards in two different tokens.
contract DualStaking {
    /// @notice Address of the token to be staked.
    address public stakeToken;
    
    /// @notice Address of the first reward token.
    address public rewardToken1;
    
    /// @notice Address of the second reward token.
    address public rewardToken2;
    
    /// @notice Total amount of tokens staked in the contract.
    uint256 public totalStaked;
    
    /// @dev Mapping of user addresses to their staked token amounts.
    mapping(address => uint256) private userStakes;
    
    /// @dev Reward rate for the first reward token.
    uint256 private rewardRate1;
    
    /// @dev Reward rate for the second reward token.
    uint256 private rewardRate2;
    
    /// @dev Admin role for managing the contract.
    address private admin;

    /// @notice Emitted when a user stakes tokens.
    event Staked(address indexed user, uint256 amount);
    
    /// @notice Emitted when a user withdraws staked tokens.
    event Withdrawn(address indexed user, uint256 amount);
    
    /// @notice Emitted when a user claims rewards.
    event RewardsClaimed(address indexed user, uint256 reward1, uint256 reward2);

    /// @dev Error for unauthorized access.
    error Unauthorized();

    /// @dev Error for insufficient balance.
    error InsufficientBalance();

    /// @dev Error for zero amount operations.
    error ZeroAmount();

    /// @dev Modifier to restrict access to admin only.
    modifier onlyAdmin() {
        if (msg.sender != admin) revert Unauthorized();
        _;
    }

    /// @dev Constructor to initialize the contract with token addresses and admin.
    /// @param _stakeToken Address of the token to be staked.
    /// @param _rewardToken1 Address of the first reward token.
    /// @param _rewardToken2 Address of the second reward token.
    constructor(address _stakeToken, address _rewardToken1, address _rewardToken2) {
        stakeToken = _stakeToken;
        rewardToken1 = _rewardToken1;
        rewardToken2 = _rewardToken2;
        admin = msg.sender;
    }

    /// @notice Allows users to stake a specified amount of tokens.
    /// @param amount The amount of tokens to stake.
    function stake(uint256 amount) external {
        if (amount == 0) revert ZeroAmount();
        
        // Transfer the stake tokens from the user to the contract
        bool success = IERC20(stakeToken).transferFrom(msg.sender, address(this), amount);
        if (!success) revert InsufficientBalance();
        
        // Update the user's stake and total staked amount
        userStakes[msg.sender] += amount;
        totalStaked += amount;
        
        emit Staked(msg.sender, amount);
    }

    /// @notice Allows users to withdraw a specified amount of their staked tokens.
    /// @param amount The amount of tokens to withdraw.
    function withdraw(uint256 amount) external {
        if (amount == 0) revert ZeroAmount();
        if (userStakes[msg.sender] < amount) revert InsufficientBalance();
        
        // Update the user's stake and total staked amount
        userStakes[msg.sender] -= amount;
        totalStaked -= amount;
        
        // Transfer the stake tokens from the contract to the user
        bool success = IERC20(stakeToken).transfer(msg.sender, amount);
        if (!success) revert InsufficientBalance();
        
        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Allows users to claim their earned rewards in both reward tokens.
    function claimRewards() external {
        uint256 userStake = userStakes[msg.sender];
        if (userStake == 0) revert InsufficientBalance();
        
        uint256 reward1 = userStake * rewardRate1 / 1e18;
        uint256 reward2 = userStake * rewardRate2 / 1e18;
        
        // Transfer the reward tokens from the contract to the user
        bool success1 = IERC20(rewardToken1).transfer(msg.sender, reward1);
        bool success2 = IERC20(rewardToken2).transfer(msg.sender, reward2);
        if (!success1 || !success2) revert InsufficientBalance();
        
        emit RewardsClaimed(msg.sender, reward1, reward2);
    }

    /// @notice Allows the admin to set the reward rates for both reward tokens.
    /// @param rate1 The new reward rate for the first reward token.
    /// @param rate2 The new reward rate for the second reward token.
    function setRewardRates(uint256 rate1, uint256 rate2) external onlyAdmin {
        rewardRate1 = rate1;
        rewardRate2 = rate2;
    }

    /// @notice Allows the admin to withdraw tokens from the contract.
    /// @param token The address of the token to withdraw.
    /// @param amount The amount of tokens to withdraw.
    function withdrawTokens(address token, uint256 amount) external onlyAdmin {
        if (amount == 0) revert ZeroAmount();
        
        // Transfer the specified tokens from the contract to the admin
        bool success = IERC20(token).transfer(admin, amount);
        if (!success) revert InsufficientBalance();
    }
}

/// @dev Interface for ERC20 token standard.
interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function transfer(address recipient, uint256 amount) external returns (bool);
}
