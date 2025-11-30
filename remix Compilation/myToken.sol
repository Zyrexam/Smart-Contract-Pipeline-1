// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;


import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title TimeLockedToken
 * @dev ERC20 Token with a time lock feature on transfers.
 */
contract TimeLockedToken is ERC20, Ownable {
    mapping(address => uint256) private lockTime;
    uint256 private constant lockDuration = 30 days;

    event TransferLocked(address indexed from, address indexed to, uint256 amount, uint256 unlockTime);
    event TokensUnlocked(address indexed account, uint256 amount);

    error TransferToZeroAddress();
    error TransferAmountZero();
    error InsufficientBalance();
    error TokensStillLocked();

    /**
     * @dev Constructor that gives msg.sender all of existing tokens.
     */
    constructor(string memory name, string memory symbol, uint256 initialSupply) ERC20(name, symbol) Ownable(msg.sender) {
        _mint(msg.sender, initialSupply);
    }

    /**
     * @dev Transfers tokens to a specified address and locks them for 30 days.
     * @param to The address to transfer to.
     * @param amount The amount to be transferred.
     * @return success A boolean indicating if the operation was successful.
     */
    function transfer(address to, uint256 amount) public override returns (bool success) {
        if (to == address(0)) revert TransferToZeroAddress();
        if (amount == 0) revert TransferAmountZero();
        if (balanceOf(msg.sender) < amount) revert InsufficientBalance();

        _transfer(msg.sender, to, amount);
        lockTime[to] = block.timestamp + lockDuration;

        emit TransferLocked(msg.sender, to, amount, lockTime[to]);
        return true;
    }

    /**
     * @dev Unlocks tokens that have been locked for more than 30 days.
     */
    function unlockTokens() public {
        if (block.timestamp < lockTime[msg.sender]) revert TokensStillLocked();

        uint256 lockedAmount = balanceOf(msg.sender);
        lockTime[msg.sender] = 0;

        emit TokensUnlocked(msg.sender, lockedAmount);
    }

    /**
     * @dev Returns the amount of tokens locked for a specific account.
     * @param account The address of the account.
     * @return lockedBalance The amount of tokens locked.
     */
    function getLockedBalance(address account) public view returns (uint256 lockedBalance) {
        if (block.timestamp < lockTime[account]) {
            return balanceOf(account);
        }4
        return 0;
    }
}
