// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.7.3/contracts/token/ERC20/ERC20.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.7.3/contracts/token/ERC20/extensions/ERC20Burnable.sol";

contract MyERC20Token is ERC20, ERC20Burnable {
    constructor() ERC20("My Token", "MTK") {
        _mint(msg.sender, 1000000 * 10**decimals());
    }

    function decimals() public pure override returns (uint8) {
        return 18;
    }
}