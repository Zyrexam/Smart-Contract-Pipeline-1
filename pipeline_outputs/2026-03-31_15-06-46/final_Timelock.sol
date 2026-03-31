// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract Timelock is Ownable {
    using SafeERC20 for IERC20;

    uint256 public releaseTime;
    address public beneficiary;
    uint256 public lockedAmount;
    IERC20 private immutable token;

    event Deposited(uint256 amount);
    event Withdrawn(uint256 amount);

    error NotBeneficiary();
    error ReleaseTimeNotReached();
    error InsufficientBalance();

    constructor(address tokenAddress, address beneficiaryAddress, uint256 initialReleaseTime) Ownable(msg.sender) {
        token = IERC20(tokenAddress);
        beneficiary = beneficiaryAddress;
        releaseTime = initialReleaseTime;
    }

    /**
     * @dev Allows depositing funds into the contract.
     * @param amount The amount to deposit.
     */
    function deposit(uint256 amount) external onlyOwner {
        lockedAmount += amount;
        token.safeTransferFrom(msg.sender, address(this), amount);
        emit Deposited(amount);
    }

    /**
     * @dev Allows the beneficiary to withdraw funds after the release time.
     */
    function withdraw() external {
        if (msg.sender != beneficiary) revert NotBeneficiary();
        if (block.timestamp < releaseTime) revert ReleaseTimeNotReached();
        if (lockedAmount == 0) revert InsufficientBalance();

        uint256 amount = lockedAmount;
        lockedAmount = 0;
        token.safeTransfer(beneficiary, amount);
        emit Withdrawn(amount);
    }

    /**
     * @dev Sets the release time for the funds.
     * @param time The new release time.
     */
    function setReleaseTime(uint256 time) external onlyOwner {
        releaseTime = time;
    }
}