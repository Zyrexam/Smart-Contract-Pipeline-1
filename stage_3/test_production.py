from stage_3 import run_stage3

# Vulnerable test contract with known issues
TEST_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title EtherVault
/// @notice A contract where users can deposit Ether and the owner can withdraw it.
contract EtherVault {
    /// @notice Address of the contract owner
    address private owner;

    /// @notice Mapping to store the balance of each user
    mapping(address => uint256) private balances;

    /// @notice Event emitted when a user deposits Ether
    /// @param user The address of the user who deposited Ether
    /// @param amount The amount of Ether deposited
    event Deposit(address indexed user, uint256 amount);

    /// @notice Event emitted when the owner withdraws Ether
    /// @param owner The address of the owner who withdrew Ether
    /// @param amount The amount of Ether withdrawn
    event Withdrawal(address indexed owner, uint256 amount);

    /// @notice Custom error for unauthorized access
    error Unauthorized();

    /// @notice Custom error for insufficient balance
    error InsufficientBalance();

    /// @dev Sets the deployer as the initial owner
    constructor() {
        owner = msg.sender;
    }

    /// @notice Allows users to deposit Ether into the contract
    /// @dev The deposited amount is added to the user's balance
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /// @notice Allows the owner to withdraw a specified amount of Ether from the contract
    /// @param amount The amount of Ether to withdraw
    function withdraw(uint256 amount) external {
        if (msg.sender != owner) revert Unauthorized();
        if (address(this).balance < amount) revert InsufficientBalance();

        // Effects
        emit Withdrawal(owner, amount);

        // Interactions
        payable(owner).transfer(amount);
    }

    /// @notice Returns the balance of the specified user
    /// @param user The address of the user
    /// @return The balance of the user
    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}

"""

def main():
    print("=" * 80)
    print("STAGE 3 PRODUCTION TEST")
    print("=" * 80)
    print("\nTesting with vulnerable contract...")
    
    # Test 1: Analysis only (all tools)
    print("\n[TEST 1] Running all tools (analysis only)")
    print("-" * 80)
    
    result = run_stage3(
        solidity_code=TEST_CONTRACT,
        contract_name="VulnerableContract",
        tools=["slither", "mythril", "semgrep", "solhint"],
        skip_auto_fix=True
    )
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Success: {result.initial_analysis.success}")
    print(f"Tools used: {', '.join(result.initial_analysis.tools_used)}")
    print(f"Total issues: {len(result.initial_analysis.issues)}")
    print(f"Critical/High: {len(result.initial_analysis.get_critical_high())}")
    
    if result.initial_analysis.warnings:
        print(f"\nWarnings:")
        for warning in result.initial_analysis.warnings:
            print(f"  ⚠️  {warning}")
    
    # Show top issues
    if result.initial_analysis.issues:
        print("\n📋 Top Security Issues Found:")
        print("-" * 80)
        critical_high = result.initial_analysis.get_critical_high()
        for i, issue in enumerate(critical_high[:10], 1):
            print(f"\n{i}. [{issue.severity.value}] {issue.title}")
            print(f"   Tool: {issue.tool}")
            print(f"   Line: {issue.line or 'N/A'}")
            print(f"   Description: {issue.description[:100]}...")
            if issue.recommendation:
                print(f"   Fix: {issue.recommendation}")
    
    # Test 2: With auto-fix (optional)
    print("\n" + "=" * 80)
    response = input("\n[TEST 2] Run auto-fix test? (requires OPENAI_API_KEY) [y/N]: ")
    
    if response.lower() == 'y':
        print("\nRunning with auto-fix...")
        print("-" * 80)
        
        try:
            result_fixed = run_stage3(
                solidity_code=TEST_CONTRACT,
                contract_name="VulnerableContract",
                tools=["mythril", "semgrep", "solhint"],  # Skip slither if problematic
                max_iterations=1
            )
            
            print("\n" + "=" * 80)
            print("AUTO-FIX RESULTS")
            print("=" * 80)
            print(f"Iterations: {result_fixed.iterations}")
            print(f"Issues resolved: {result_fixed.issues_resolved}")
            print(f"Initial issues: {len(result_fixed.initial_analysis.issues)}")
            print(f"Final issues: {len(result_fixed.final_analysis.issues) if result_fixed.final_analysis else 0}")
            
            if result_fixed.fixes_applied:
                print("\n🔧 Fixes Applied:")
                for fix in result_fixed.fixes_applied:
                    print(f"  Iteration {fix['iteration']}: {fix['issues_before']} → {fix['issues_after']} issues")
        
        except Exception as e:
            print(f"\n⚠️  Auto-fix failed: {e}")
            print("This is expected if OPENAI_API_KEY is not set")
    
    print("\n" + "=" * 80)
    print("✅ PRODUCTION TEST COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print(f"  • Tools tested: 4 (slither, mythril, semgrep, solhint)")
    print(f"  • Tools succeeded: {len([t for t in result.initial_analysis.tools_used if not t.endswith('-failed') and not t.endswith('-error')])}")
    print(f"  • Issues found: {len(result.initial_analysis.issues)}")
    print(f"  • Pipeline status: {'✅ READY' if result.initial_analysis.success else '⚠️  NEEDS ATTENTION'}")

if __name__ == "__main__":
    main()
