// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract DualStaking is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    IERC20 private immutable stakingToken;
    IERC20 private immutable rewardToken1;
    IERC20 private immutable rewardToken2;

    uint256 private rewardRate1;
    uint256 private rewardRate2;
    uint256 private totalStaked;

    mapping(address => uint256) private stakes;
    mapping(address => uint256) private rewardDebt1;
    mapping(address => uint256) private rewardDebt2;

    event Staked(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 reward1, uint256 reward2);
    event RewardRatesSet(uint256 rate1, uint256 rate2);

    error NotAdmin();
    error InsufficientStake();
    error ZeroAmount();

    constructor(
        address stakingTokenAddress,
        address rewardToken1Address,
        address rewardToken2Address
    ) {
        stakingToken = IERC20(stakingTokenAddress);
        rewardToken1 = IERC20(rewardToken1Address);
        rewardToken2 = IERC20(rewardToken2Address);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Sets the reward rates for the two reward tokens.
     * @param rate1 The reward rate for the first reward token.
     * @param rate2 The reward rate for the second reward token.
     */
    function setRewardRates(uint256 rate1, uint256 rate2) external {
        if (!hasRole(ADMIN_ROLE, msg.sender)) revert NotAdmin();
        rewardRate1 = rate1;
        rewardRate2 = rate2;
        emit RewardRatesSet(rate1, rate2);
    }

    /**
     * @dev Allows users to stake a specified amount of the staking token.
     * @param amount The amount of tokens to stake.
     */
    function stake(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();

        _updateRewards(msg.sender);

        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        stakes[msg.sender] += amount;
        totalStaked += amount;

        emit Staked(msg.sender, amount);
    }

    /**
     * @dev Allows users to withdraw a specified amount of their staked tokens.
     * @param amount The amount of tokens to withdraw.
     */
    function withdraw(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        if (stakes[msg.sender] < amount) revert InsufficientStake();

        _updateRewards(msg.sender);

        stakes[msg.sender] -= amount;
        totalStaked -= amount;
        stakingToken.safeTransfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @dev Allows users to claim their accumulated rewards in both reward tokens.
     */
    function claimRewards() external nonReentrant {
        _updateRewards(msg.sender);

        uint256 reward1 = rewardDebt1[msg.sender];
        uint256 reward2 = rewardDebt2[msg.sender];

        if (reward1 > 0) {
            rewardDebt1[msg.sender] = 0;
            rewardToken1.safeTransfer(msg.sender, reward1);
        }

        if (reward2 > 0) {
            rewardDebt2[msg.sender] = 0;
            rewardToken2.safeTransfer(msg.sender, reward2);
        }

        emit RewardClaimed(msg.sender, reward1, reward2);
    }

    function _updateRewards(address user) private {
        uint256 userStake = stakes[user];
        if (userStake > 0) {
            rewardDebt1[user] += (userStake * rewardRate1) / 1e18;
            rewardDebt2[user] += (userStake * rewardRate2) / 1e18;
        }
    }
}
