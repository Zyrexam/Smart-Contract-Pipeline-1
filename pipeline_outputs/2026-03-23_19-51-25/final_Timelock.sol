// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract Timelock is Ownable {
    using SafeERC20 for IERC20;

    uint256 public lockedUntil;
    address public beneficiary;
    uint256 public amount;

    event FundsWithdrawn(address indexed beneficiary, uint256 amount);
    event LockTimeSet(uint256 time);

    error LockTimeNotReached();
    error InvalidTime();

    constructor(address beneficiaryAddress, uint256 initialAmount) {
        beneficiary = beneficiaryAddress;
        amount = initialAmount;
    }

    modifier onlyAfterLockTime() {
        if (block.timestamp < lockedUntil) {
            revert LockTimeNotReached();
        }
        _;
    }

    /**
     * @dev Sets the time until which the funds are locked.
     * @param time The new lock time.
     */
    function setLockTime(uint256 time) external onlyOwner {
        if (time <= block.timestamp) {
            revert InvalidTime();
        }
        lockedUntil = time;
        emit LockTimeSet(time);
    }

    /**
     * @dev Allows the owner to withdraw funds after the lock time has passed.
     */
    function withdrawFunds() external onlyOwner onlyAfterLockTime {
        uint256 withdrawAmount = amount;
        amount = 0;
        IERC20(beneficiary).safeTransfer(msg.sender, withdrawAmount);
        emit FundsWithdrawn(beneficiary, withdrawAmount);
    }
}
