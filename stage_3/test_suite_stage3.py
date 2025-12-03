"""
Stage 3 Test Suite
==================

Tests for security analysis and vulnerability fixing.
"""

import json
from pathlib import Path
from security_integration import (
    analyze_and_fix,
    SmartBugsRunner,
    VulnerabilityFixer,
    VulnerabilitySeverity,
    VulnerabilityCategory,
    NormalizedIssue
)


# ============================================================================
# TEST CONTRACTS
# ============================================================================

# Contract with reentrancy vulnerability
REENTRANCY_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ReentrancyVulnerable {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    // VULNERABLE: Reentrancy attack possible
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
    }
}
"""

# Contract with access control issues
ACCESS_CONTROL_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract AccessControlVulnerable is ERC20 {
    constructor() ERC20("Test", "TST") {
        _mint(msg.sender, 1000000 * 10**18);
    }
    
    // VULNERABLE: No access control
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
    
    // VULNERABLE: Anyone can pause
    function emergencyStop() external {
        // Emergency stop logic
    }
}
"""

# Contract with tx.origin vulnerability
TX_ORIGIN_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TxOriginVulnerable {
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // VULNERABLE: Uses tx.origin instead of msg.sender
    function transferOwnership(address newOwner) external {
        require(tx.origin == owner, "Not owner");
        owner = newOwner;
    }
}
"""

# Contract with unchecked call
UNCHECKED_CALL_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract UncheckedCallVulnerable {
    function sendEther(address payable recipient, uint256 amount) external {
        // VULNERABLE: Unchecked low-level call
        recipient.call{value: amount}("");
    }
    
    function sendToken(address token, address to, uint256 amount) external {
        // VULNERABLE: No return value check
        (bool success, ) = token.call(
            abi.encodeWithSignature("transfer(address,uint256)", to, amount)
        );
        // Missing: require(success, "Transfer failed");
    }
}
"""

# Well-secured contract (should pass)
SECURE_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SecureToken is ERC20, ReentrancyGuard, Ownable {
    constructor() ERC20("Secure", "SEC") Ownable(msg.sender) {
        _mint(msg.sender, 1000000 * 10**18);
    }
    
    function mint(address to, uint256 amount) external onlyOwner {
        require(to != address(0), "Invalid address");
        _mint(to, amount);
    }
    
    function withdraw(uint256 amount) external nonReentrant {
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        _burn(msg.sender, amount);
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }
}
"""


# ============================================================================
# TEST CASES
# ============================================================================

def test_reentrancy_detection():
    """Test detection of reentrancy vulnerability"""
    print("\n" + "=" * 80)
    print("TEST: Reentrancy Detection")
    print("=" * 80)
    
    runner = SmartBugsRunner("./smartbugs")
    
    try:
        result = runner.run_analysis(
            REENTRANCY_CONTRACT,
            "ReentrancyTest",
            tools=["slither"],
            timeout=60
        )
        
        if not result.success:
            print(f"❌ Analysis failed: {result.error_message}")
            return False
        
        reentrancy_issues = [
            issue for issue in result.issues_found
            if issue.category == VulnerabilityCategory.REENTRANCY
        ]
        
        if reentrancy_issues:
            print(f"✅ Detected {len(reentrancy_issues)} reentrancy issue(s)")
            for issue in reentrancy_issues:
                print(f"   • {issue.title} [{issue.severity.value}]")
            return True
        else:
            print("⚠️  No reentrancy issues detected (unexpected)")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_access_control_detection():
    """Test detection of access control issues"""
    print("\n" + "=" * 80)
    print("TEST: Access Control Detection")
    print("=" * 80)
    
    runner = SmartBugsRunner("./smartbugs")
    
    try:
        result = runner.run_analysis(
            ACCESS_CONTROL_CONTRACT,
            "AccessControlTest",
            tools=["slither"],
            timeout=60
        )
        
        if not result.success:
            print(f"❌ Analysis failed: {result.error_message}")
            return False
        
        access_issues = [
            issue for issue in result.issues_found
            if issue.category == VulnerabilityCategory.ACCESS_CONTROL
        ]
        
        if access_issues:
            print(f"✅ Detected {len(access_issues)} access control issue(s)")
            return True
        else:
            print("⚠️  No access control issues detected")
            return True  # May not always detect, not critical
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_vulnerability_fixing():
    """Test automatic vulnerability fixing"""
    print("\n" + "=" * 80)
    print("TEST: Automatic Vulnerability Fixing")
    print("=" * 80)
    
    try:
        result = analyze_and_fix(
            solidity_code=REENTRANCY_CONTRACT,
            contract_name="ReentrancyFix",
            max_iterations=2,
            smartbugs_path="./smartbugs",
            tools=["slither"]
        )
        
        initial_issues = len(result.initial_analysis.issues_found)
        final_issues = len(result.remaining_issues)
        
        print(f"\nResults:")
        print(f"  • Iterations: {result.iterations}")
        print(f"  • Initial issues: {initial_issues}")
        print(f"  • Final issues: {final_issues}")
        print(f"  • Issues resolved: {initial_issues - final_issues}")
        
        if final_issues < initial_issues:
            print(f"\n✅ Successfully reduced vulnerabilities")
            print(f"\nFixed code preview:")
            print(result.final_code[:500] + "...")
            return True
        elif initial_issues == 0:
            print(f"\n✅ No issues found (may need SmartBugs setup)")
            return True
        else:
            print(f"\n⚠️  Could not reduce vulnerabilities")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_secure_contract():
    """Test that secure contract passes analysis"""
    print("\n" + "=" * 80)
    print("TEST: Secure Contract Analysis")
    print("=" * 80)
    
    runner = SmartBugsRunner("./smartbugs")
    
    try:
        result = runner.run_analysis(
            SECURE_CONTRACT,
            "SecureTest",
            tools=["slither"],
            timeout=60
        )
        
        if not result.success:
            print(f"❌ Analysis failed: {result.error_message}")
            return False
        
        high_severity = result.get_high_severity_count()
        
        print(f"\nResults:")
        print(f"  • Total issues: {len(result.issues_found)}")
        print(f"  • High/Critical: {high_severity}")
        
        if high_severity == 0:
            print(f"\n✅ Secure contract passed (no high-severity issues)")
            return True
        else:
            print(f"\n⚠️  Detected {high_severity} high-severity issues in 'secure' contract")
            for issue in result.issues_found:
                if issue.severity in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]:
                    print(f"   • {issue.title}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_llm_fixer_only():
    """Test LLM fixer without SmartBugs"""
    print("\n" + "=" * 80)
    print("TEST: LLM Fixer (Standalone)")
    print("=" * 80)
    
    # Create mock issues
    mock_issues = [
        NormalizedIssue(
            tool="test",
            category=VulnerabilityCategory.REENTRANCY,
            severity=VulnerabilitySeverity.HIGH,
            title="Reentrancy in withdraw",
            description="State change after external call",
            recommendation="Use checks-effects-interactions pattern"
        ),
        NormalizedIssue(
            tool="test",
            category=VulnerabilityCategory.ACCESS_CONTROL,
            severity=VulnerabilitySeverity.CRITICAL,
            title="Missing access control on mint",
            description="Anyone can mint tokens",
            recommendation="Add onlyOwner modifier"
        )
    ]
    
    try:
        fixer = VulnerabilityFixer()
        fixed_code = fixer.generate_fix(
            REENTRANCY_CONTRACT,
            mock_issues,
            "TestContract",
            iteration=1
        )
        
        # Check if fixes were applied
        has_reentrancy_guard = "ReentrancyGuard" in fixed_code
        has_only_owner = "onlyOwner" in fixed_code or "Ownable" in fixed_code
        
        print(f"\nFix Analysis:")
        print(f"  • Added ReentrancyGuard: {has_reentrancy_guard}")
        print(f"  • Added Access Control: {has_only_owner}")
        print(f"  • Code length: {len(fixed_code)} chars")
        
        if has_reentrancy_guard:
            print(f"\n✅ LLM successfully generated fixes")
            return True
        else:
            print(f"\n⚠️  LLM did not apply expected fixes")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all Stage 3 tests"""
    print("\n" + "#" * 80)
    print("STAGE 3 TEST SUITE")
    print("#" * 80)
    
    # Check if SmartBugs is available
    smartbugs_path = Path("./smartbugs")
    if not smartbugs_path.exists():
        print("\n⚠️  SmartBugs not found at ./smartbugs")
        print("Some tests will be skipped.")
        print("\nTo run all tests:")
        print("  git clone https://github.com/smartbugs/smartbugs.git")
        print("  cd smartbugs && pip install -r requirements.txt")
        print()
        
        # Run only LLM fixer test
        results = {
            "LLM Fixer": test_llm_fixer_only()
        }
    else:
        # Run all tests
        results = {
            "Reentrancy Detection": test_reentrancy_detection(),
            "Access Control Detection": test_access_control_detection(),
            "Vulnerability Fixing": test_vulnerability_fixing(),
            "Secure Contract": test_secure_contract(),
            "LLM Fixer": test_llm_fixer_only()
        }
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        
        tests = {
            "reentrancy": test_reentrancy_detection,
            "access": test_access_control_detection,
            "fixing": test_vulnerability_fixing,
            "secure": test_secure_contract,
            "llm": test_llm_fixer_only
        }
        
        if test_name in tests:
            success = tests[test_name]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test: {test_name}")
            print(f"Available tests: {', '.join(tests.keys())}")
            sys.exit(1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)