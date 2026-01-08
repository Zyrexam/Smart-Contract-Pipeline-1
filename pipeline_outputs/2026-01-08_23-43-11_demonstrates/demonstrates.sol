// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title BadLottery
 * @dev VULNERABLE CONTRACT - DO NOT USE IN PRODUCTION
 * 
 * This contract demonstrates weak randomness using block attributes (SWC-120).
 * Miners can manipulate block.timestamp or block.prevrandao (difficulty) to game the system.
 */
contract BadLottery {
    uint256 public ticketPrice = 0.1 ether;
    address public winner;
    bool public ended;

    function enter() external payable {
        require(msg.value == ticketPrice, "Incorrect ticket price");
        require(!ended, "Lottery ended");
    }

    // VULNERABILITY: Weak randomness using block variables
    function pickWinner(address[] memory players) external {
        require(!ended, "Already ended");
        require(players.length > 0, "No players");
        
        // Vulnerable source of randomness
        // block.timestamp is predictable and manipulatable by miners
        uint256 randomIndex = uint256(
            keccak256(
                abi.encodePacked(
                    block.timestamp, 
                    block.prevrandao, 
                    players.length
                )
            )
        ) % players.length;

        winner = players[randomIndex];
        ended = true;
    }
}
