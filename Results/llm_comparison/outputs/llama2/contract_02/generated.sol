// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ERC20Token {
    string name;
    uint256 totalSupply;
    mapping(address => uint256) public balances;

    event Mint(address indexed from, uint256 value);
    event Burn(address indexed from, uint256 value);

    constructor() public {
        name = "MyToken";
        totalSupply = 1000000;
    }

    function mint(address to, uint256 amount) public {
        require(amount <= totalSupply, "Insufficient token supply");
        balances[to] += amount;
        emit Mint(msg.sender, amount);
    }

    function burn(uint256 amount) public {
        require(amount > 0, "Invalid burn amount");
        balances[msg.sender] -= amount;
        emit Burn(msg.sender, amount);
    }
}