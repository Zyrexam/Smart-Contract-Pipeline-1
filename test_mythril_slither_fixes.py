"""
Test script to verify Mythril and Slither are finding issues correctly
"""

import json
from pathlib import Path
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

def test_tools_detection():
    """Test that tools are detecting issues"""
    print("="*80)
    print("TESTING MYTHRIL AND SLITHER DETECTION")
    print("="*80)
    print("\nTesting with a known vulnerable contract...")
    print("Expected vulnerabilities:")
    print("  - Reentrancy in withdraw()")
    print("  - tx.origin usage in transferOwnership()")
    print("  - Unchecked send in sendFunds()")
    print("\n" + "="*80)
    
    # Run Stage 3 with verbose mode
    result = run_stage3(
        solidity_code=TEST_CONTRACT,
        contract_name="VulnerableContract",
        stage2_metadata={"_verbose": True},  # Enable verbose mode
        tools=["slither", "mythril"],
        skip_auto_fix=True
    )
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Success: {result.initial_analysis.success}")
    print(f"Tools used: {result.initial_analysis.tools_used}")
    print(f"Total issues found: {len(result.initial_analysis.issues)}")
    
    if result.initial_analysis.warnings:
        print(f"\nWarnings:")
        for warning in result.initial_analysis.warnings:
            print(f"  - {warning}")
    
    # Group issues by tool
    issues_by_tool = {}
    for issue in result.initial_analysis.issues:
        tool = issue.tool
        if tool not in issues_by_tool:
            issues_by_tool[tool] = []
        issues_by_tool[tool].append(issue)
    
    print(f"\nIssues by tool:")
    for tool, issues in issues_by_tool.items():
        print(f"  {tool}: {len(issues)} issues")
        for issue in issues[:3]:  # Show first 3
            print(f"    - [{issue.severity.value}] {issue.title}")
    
    # Check if expected tools found issues
    print(f"\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    slither_issues = issues_by_tool.get("slither", [])
    mythril_issues = issues_by_tool.get("mythril", [])
    
    if len(slither_issues) == 0:
        print("⚠️  WARNING: Slither found 0 issues (expected at least 1)")
        print("   This might indicate:")
        print("   - Slither is not running correctly")
        print("   - Output parsing is failing")
        print("   - Docker container issue")
    else:
        print(f"✓ Slither found {len(slither_issues)} issues")
    
    if len(mythril_issues) == 0:
        print("⚠️  WARNING: Mythril found 0 issues (expected at least 1)")
        print("   This might indicate:")
        print("   - Mythril is not running correctly")
        print("   - JSON parsing is failing")
        print("   - Docker container issue")
    else:
        print(f"✓ Mythril found {len(mythril_issues)} issues")
    
    # Check for specific vulnerabilities
    issue_titles = [issue.title.lower() for issue in result.initial_analysis.issues]
    
    has_reentrancy = any("reentrancy" in title for title in issue_titles)
    has_tx_origin = any("tx.origin" in title or "tx-origin" in title for title in issue_titles)
    has_unchecked = any("unchecked" in title for title in issue_titles)
    
    print(f"\nVulnerability detection:")
    print(f"  Reentrancy: {'✓' if has_reentrancy else '✗'}")
    print(f"  tx.origin: {'✓' if has_tx_origin else '✗'}")
    print(f"  Unchecked send: {'✓' if has_unchecked else '✗'}")
    
    return result

def test_results_generation():
    """Test that results generation works correctly"""
    print("\n" + "="*80)
    print("TESTING RESULTS GENERATION")
    print("="*80)
    
    results_dir = Path("pipeline_outputs")
    if not results_dir.exists():
        print(f"⚠️  Results directory not found: {results_dir}")
        print("   Skipping results generation test")
        return
    
    # Find a sample stage3_report.json
    sample_reports = list(results_dir.glob("*/stage3_report.json"))
    if not sample_reports:
        print("⚠️  No stage3_report.json files found")
        print("   Run Stage 3 on some contracts first")
        return
    
    print(f"Found {len(sample_reports)} stage3_report.json files")
    
    # Test loading one
    sample_report = sample_reports[0]
    print(f"\nTesting with: {sample_report}")
    
    try:
        with open(sample_report, 'r') as f:
            data = json.load(f)
        
        initial = data.get("initial_analysis", {})
        issues = initial.get("issues", [])
        tools_used = initial.get("tools_used", [])
        
        print(f"  Contract: {initial.get('contract_name', 'Unknown')}")
        print(f"  Tools used: {tools_used}")
        print(f"  Total issues: {len(issues)}")
        
        # Count by tool
        by_tool = {}
        for issue in issues:
            tool = issue.get("tool", "unknown")
            by_tool[tool] = by_tool.get(tool, 0) + 1
        
        print(f"  Issues by tool: {by_tool}")
        
        print("\n✓ Results generation test passed")
        
    except Exception as e:
        print(f"✗ Error loading results: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test tool detection
    result = test_tools_detection()
    
    # Test results generation
    test_results_generation()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nIf tools found 0 issues, check:")
    print("  1. Docker containers are running")
    print("  2. Docker images are available: docker images | grep -E 'slither|mythril'")
    print("  3. Run with verbose mode to see detailed logs")
    print("  4. Check the debug output in the parsers")

