// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract StakingContract is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    // Custom errors
    error InvalidAddress();
    error ContractPaused();
    error NotEnoughBalance();

    // State variables
    uint256 private rewardRate;
    bool private paused;
    IERC20 private stakingToken;

    mapping(address => uint256) private stakes;
    mapping(address => uint256) private rewards;

    // Events
    event Staked(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 rewards);
    event RewardRateSet(uint256 newRate);
    event Paused(bool status);

    // Constructor
    constructor(IERC20 _stakingToken) {
        if (address(_stakingToken) == address(0)) revert InvalidAddress();
        stakingToken = _stakingToken;
        rewardRate = 0;
        paused = false;
    }

    // Modifiers
    modifier whenNotPaused() {
        if (paused) revert ContractPaused();
        _;
    }

    /** 
     * @notice Allows users to stake a specified amount of ERC20 tokens.
     * @param amount The amount of tokens to stake.
     */
    function stakeTokens(uint256 amount) external nonReentrant whenNotPaused {
        if (amount == 0) revert NotEnoughBalance();
        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        stakes[msg.sender] += amount;
        emit Staked(msg.sender, amount);
    }

    /** 
     * @notice Allows users to claim their earned rewards.
     * @return rewards The amount of rewards claimed.
     */
    function claimRewards() external nonReentrant whenNotPaused returns (uint256 rewards) {
        rewards = calculateRewards(msg.sender);
        if (rewards > 0) {
            stakingToken.safeTransfer(msg.sender, rewards);
            emit RewardClaimed(msg.sender, rewards);
        }
    }

    /** 
     * @notice Allows the owner to set a new reward rate.
     * @param newRate The new reward rate to set.
     */
    function setRewardRate(uint256 newRate) external onlyOwner {
        rewardRate = newRate;
        emit RewardRateSet(newRate);
    }

    /** 
     * @notice Allows the owner to pause the contract.
     */
    function pauseContract() external onlyOwner {
        paused = !paused;
        emit Paused(paused);
    }

    // Internal function to calculate rewards
    function calculateRewards(address user) internal view returns (uint256) {
        return stakes[user] * rewardRate / 1e18;
    }
}
