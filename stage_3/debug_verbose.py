"""
Debug Test - Verbose Mode
"""

from stage_3.analyzer import SecurityAnalyzer

# Simple vulnerable contract
TEST_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    
    function withdraw() public {
        uint256 amount = balances[msg.sender];
        (bool success,) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }
    
    function badAuth() public view returns (bool) {
        return tx.origin == msg.sender;
    }
    
    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}
"""

print("=" * 80)
print("VERBOSE DEBUG TEST")
print("=" * 80)

# Test each tool individually with verbose mode
analyzer = SecurityAnalyzer(verbose=True)

for tool in ["slither", "mythril", "semgrep", "solhint"]:
    print(f"\n{'=' * 80}")
    print(f"Testing: {tool}")
    print("=" * 80)
    
    result = analyzer.analyze(
        solidity_code=TEST_CODE,
        contract_name="VulnerableContract",
        tools=[tool],
        timeout=120
    )
    
    print(f"\nResult for {tool}:")
    print(f"  Success: {result.success}")
    print(f"  Issues found: {len(result.issues)}")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")
    if result.error:
        print(f"  Error: {result.error}")
