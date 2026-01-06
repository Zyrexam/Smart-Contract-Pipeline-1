"""
Debug script to check why Slither and Mythril aren't finding issues
"""

import json
from stage_3 import run_stage3

# Test with a known vulnerable contract
TEST_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title VulnerableContract
/// @notice A contract with known vulnerabilities for testing
contract VulnerableContract {
    address public owner;
    mapping(address => uint256) public balances;
    
    constructor() {
        owner = msg.sender;
    }
    
    // VULNERABILITY 1: Reentrancy (no checks-effects-interactions)
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
        balances[msg.sender] -= amount;  // State change AFTER external call
    }
    
    // VULNERABILITY 2: tx.origin usage
    function transferOwnership(address newOwner) external {
        require(tx.origin == owner, "Not owner");  // Should use msg.sender
        owner = newOwner;
    }
    
    // VULNERABILITY 3: Unchecked send
    function sendFunds(address to, uint256 amount) external {
        require(msg.sender == owner, "Not owner");
        payable(to).send(amount);  // send() returns bool but not checked
    }
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
}
"""

def main():
    print("="*80)
    print("DEBUGGING STAGE 3 TOOLS")
    print("="*80)
    print("\nTesting with a known vulnerable contract...")
    print("Expected vulnerabilities:")
    print("  - Reentrancy in withdraw()")
    print("  - tx.origin usage in transferOwnership()")
    print("  - Unchecked send in sendFunds()")
    print("\n" + "="*80)
    
    # Run with verbose mode (we need to modify runner to support this)
    # For now, let's manually create analyzer with verbose=True
    from stage_3.analyzer import SecurityAnalyzer
    
    print("\n[1] Creating analyzer with verbose mode...")
    analyzer = SecurityAnalyzer(verbose=True)
    
    print("\n[2] Running analysis...")
    result = analyzer.analyze(
        solidity_code=TEST_CONTRACT,
        contract_name="VulnerableContract",
        tools=["slither", "mythril"],
        timeout=120
    )
    
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80)
    print(f"Success: {result.success}")
    print(f"Tools used: {result.tools_used}")
    print(f"Total issues found: {len(result.issues)}")
    print(f"Warnings: {result.warnings}")
    
    if result.issues:
        print("\n📋 Issues Found:")
        for i, issue in enumerate(result.issues, 1):
            print(f"\n{i}. [{issue.severity.value}] {issue.title}")
            print(f"   Tool: {issue.tool}")
            print(f"   Line: {issue.line}")
            print(f"   Description: {issue.description[:100]}...")
    else:
        print("\n⚠️  NO ISSUES FOUND - This is suspicious!")
        print("\nPossible reasons:")
        print("  1. Tools are not running correctly")
        print("  2. Output parsing is failing")
        print("  3. Docker containers are not set up properly")
        print("  4. Tools are configured incorrectly")
    
    # Also test with the actual pipeline
    print("\n" + "="*80)
    print("TESTING WITH FULL PIPELINE")
    print("="*80)
    
    pipeline_result = run_stage3(
        solidity_code=TEST_CONTRACT,
        contract_name="VulnerableContract",
        tools=["slither", "mythril", "semgrep", "solhint"],
        skip_auto_fix=True
    )
    
    print(f"\nPipeline Results:")
    print(f"  Initial issues: {len(pipeline_result.initial_analysis.issues)}")
    print(f"  Tools used: {pipeline_result.initial_analysis.tools_used}")
    
    if pipeline_result.initial_analysis.warnings:
        print(f"\n  Warnings:")
        for warning in pipeline_result.initial_analysis.warnings:
            print(f"    - {warning}")

if __name__ == "__main__":
    main()

