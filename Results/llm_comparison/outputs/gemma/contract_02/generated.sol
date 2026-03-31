// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ERC20Token {
    // Token name
    string private tokenName;

    // Token symbol
    string private tokenSymbol;

    // Initial supply of tokens
    uint256 private initialSupply;

    // Mapping of token owners to their balances
    mapping(address => uint256) private tokenOwners;

    // Events
    event Mint(address indexed owner, uint256 amount);
    event Burn(address indexed owner, uint256 amount);

    constructor(string memory _tokenName, string memory _tokenSymbol, uint256 _initialSupply) {
        tokenName = _tokenName;
        tokenSymbol = _tokenSymbol;
        initialSupply = _initialSupply;
    }

    // Function to mint tokens
    function mint(uint256 _amount) public {
        require(msg.sender == tokenOwners[address(this)], "Only the owner can mint");

        // Add the minted tokens to the owner's balance
        tokenOwners[msg.sender] += _amount;

        // Mint event
        emit Mint(msg.sender, _amount);
    }

    // Function to burn tokens
    function burn(uint256 _amount) public {
        require(tokenOwners[msg.sender] >= _amount, "Insufficient tokens to burn");

        // Remove the burned tokens from the owner's balance
        tokenOwners[msg.sender] -= _amount;

        // Burn event
        emit Burn(msg.sender, _amount);
    }

    // Get the token name
    function name() public view returns (string memory) {
        return tokenName;
    }

    // Get the token symbol
    function symbol() public view returns (string memory) {
        return tokenSymbol;
    }

    // Get the initial supply of tokens
    function totalSupply() public view returns (uint256) {
        return initialSupply;
    }
}