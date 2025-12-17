// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract TokenStaking is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    mapping(address => uint256) private stakedTokens;
    mapping(address => uint256) private rewardTokens;
    mapping(address => uint256) private lastUpdateTime;
    uint256 private totalStaked;
    uint256 private rewardRate;
    address private erc20Token;
    address private rewardToken;

    event TokensStaked(address indexed user, uint256 amount);
    event TokensWithdrawn(address indexed user, uint256 amount);
    event RewardsClaimed(address indexed user, uint256 amount);

    error NotEnoughStakedTokens();
    error NotEnoughRewardTokens();
    error Unauthorized();
    error InvalidAddress();

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Allows users to stake a specified amount of ERC20 tokens.
     * @param amount The amount of tokens to stake.
     */
    function stakeTokens(uint256 amount) external nonReentrant {
        if (amount == 0) revert InvalidAddress();
        IERC20(erc20Token).safeTransferFrom(msg.sender, address(this), amount);
        _updateRewards(msg.sender);
        stakedTokens[msg.sender] += amount;
        totalStaked += amount;
        emit TokensStaked(msg.sender, amount);
    }

    /**
     * @dev Allows users to withdraw a specified amount of staked tokens.
     * @param amount The amount of tokens to withdraw.
     */
    function withdrawTokens(uint256 amount) external nonReentrant {
        if (stakedTokens[msg.sender] < amount) revert NotEnoughStakedTokens();
        _updateRewards(msg.sender);
        stakedTokens[msg.sender] -= amount;
        totalStaked -= amount;
        IERC20(erc20Token).safeTransfer(msg.sender, amount);
        emit TokensWithdrawn(msg.sender, amount);
    }

    /**
     * @dev Allows users to claim their earned reward tokens.
     */
    function claimRewards() external nonReentrant {
        _updateRewards(msg.sender);
        uint256 reward = rewardTokens[msg.sender];
        if (reward == 0) revert NotEnoughRewardTokens();
        rewardTokens[msg.sender] = 0;
        IERC20(rewardToken).safeTransfer(msg.sender, reward);
        emit RewardsClaimed(msg.sender, reward);
    }

    /**
     * @dev Allows admin to set the reward rate for staking.
     * @param newRate The new reward rate.
     */
    function setRewardRate(uint256 newRate) external {
        if (!hasRole(ADMIN_ROLE, msg.sender)) revert Unauthorized();
        rewardRate = newRate;
    }

    /**
     * @dev Allows admin to set the addresses of the ERC20 and reward tokens.
     * @param erc20TokenAddress The address of the ERC20 token.
     * @param rewardTokenAddress The address of the reward token.
     */
    function setTokenAddresses(address erc20TokenAddress, address rewardTokenAddress) external {
        if (!hasRole(ADMIN_ROLE, msg.sender)) revert Unauthorized();
        if (erc20TokenAddress == address(0) || rewardTokenAddress == address(0)) revert InvalidAddress();
        erc20Token = erc20TokenAddress;
        rewardToken = rewardTokenAddress;
    }

    function _updateRewards(address user) internal {
        uint256 timeDifference = block.timestamp - lastUpdateTime[user];
        rewardTokens[user] += stakedTokens[user] * rewardRate * timeDifference / 1e18;
        lastUpdateTime[user] = block.timestamp;
    }
}
