// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyToken is ERC20, Ownable {
    uint256 private constant INITIAL_SUPPLY = 1000 * (10 ** decimals());
    mapping(address => uint256) private _balances;

    constructor() ERC20("MyToken", "MTK") {
        _mint(msg.sender, INITIAL_SUPPLY);
        transferOwnership(msg.sender);
    }

    function mint(address to, uint256 amount) public onlyOwner {
        require(_balances[msg.sender] >= amount, "Not enough balance to mint");
        _mint(to, amount);
        _balances[msg.sender] -= amount;
    }

    function burn(uint256 amount) public onlyOwner {
        _burn(amount);
    }

    function transfer(address to, uint256 amount) override public {
        require(_balances[msg.sender] >= amount, "Not enough balance to transfer");
        _transfer(to, amount);
        _balances[msg.sender] -= amount;
    }

    function (_) override public {
        emit Transfer(address(this), msg.data.origin, msg.data.inputs[0].values[0]);
    }

    function balanceOf(address account) public view returns (uint256) {
        return _balances[account];
    }
}