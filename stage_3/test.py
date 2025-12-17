import os
import sys
import re
from pathlib import Path
from typing import Tuple, List

from stage_3 import run_stage3


def read_contract_file(filepath: str) -> Tuple[str, str]:
    with open(filepath, "r", encoding="utf8") as f:
        code = f.read()
    
    # Extract contract name (simple extraction)
    contract_name = Path(filepath).stem  # Default to filename without extension
    
    # Try to find contract declaration using regex
    import re
    # Pattern: contract ContractName or contract ContractName is ...
    match = re.search(r'contract\s+(\w+)', code)
    if match:
        contract_name = match.group(1)
    
    return code, contract_name


def get_contract_files() -> List[str]:
    """Get all .sol files from stage_3/contracts/ folder"""
    contracts_dir = Path(__file__).parent / "contracts"
    
    if not contracts_dir.exists():
        print(f"⚠️  Contracts directory not found: {contracts_dir}")
        return []
    
    sol_files = list(contracts_dir.glob("*.sol"))
    return [str(f) for f in sol_files]


def test_analysis_only(contract_file: str):
    """
    Test Stage 3 analysis only (no fixing)
    
    Args:
        contract_file: Path to Solidity file
    """
    print("="*80)
    print("TEST: Security Analysis (No Auto-Fix)")
    print("="*80)
    print(f"Analyzing: {contract_file}")
    
    # Read contract file
    try:
        contract_code, contract_name = read_contract_file(contract_file)
        print(f"Contract name: {contract_name}")
    except Exception as e:
        print(f"❌ Failed to read contract file: {e}")
        return None
    
    # Sample Stage 2 metadata (can be enhanced to read from metadata.json if exists)
    stage2_metadata = {
        "base_standard": "CUSTOM",
        "category": "CUSTOM",
        "access_control": "NONE",
        "security_features": [],
        "inheritance_chain": [],
        "imports_used": []
    }
    
    # Try to read metadata.json if it exists
    metadata_file = Path(contract_file).parent / "metadata.json"
    if metadata_file.exists():
        try:
            import json
            with open(metadata_file, "r") as f:
                stage2_metadata = json.load(f)
            print("✓ Loaded metadata from metadata.json")
        except Exception:
            pass
    
    # Run analysis with verbose debugging
    from stage_3.analyzer import SecurityAnalyzer
    
    print("\n" + "="*80)
    print("TEST: Security Analysis (No Auto-Fix)")
    print("="*80)
    
    analyzer = SecurityAnalyzer(verbose=True)  # Enable verbose for debugging
    analysis_result = analyzer.analyze(
        solidity_code=contract_code,
        contract_name=contract_name,
        tools=["slither", "mythril", "semgrep", "solhint"],
        timeout=120
    )
    
    # Create a mock Stage3Result for compatibility
    from stage_3.models import Stage3Result
    result = Stage3Result(
        original_code=contract_code,
        final_code=contract_code,
        iterations=0,
        initial_analysis=analysis_result,
        final_analysis=None,
        fixes_applied=[],
        issues_resolved=0,
        stage2_metadata=stage2_metadata,
        compiles=None
    )
    
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80)
    print(f"Tools used: {', '.join(result.initial_analysis.tools_used) if result.initial_analysis.tools_used else 'None'}")
    print(f"Total issues: {len(result.initial_analysis.issues)}")
    print(f"Critical/High: {len(result.initial_analysis.get_critical_high())}")
    
    if result.initial_analysis.issues:
        print("\n📋 Detected Issues:")
        print("-" * 80)
        for i, issue in enumerate(result.initial_analysis.issues[:20], 1):  # Show first 20
            line_info = f"Line {issue.line}" if issue.line else "Unknown location"
            if issue.line_end and issue.line_end != issue.line:
                line_info = f"Lines {issue.line}-{issue.line_end}"
            
            print(f"\n{i}. [{issue.severity.value}] {issue.title}")
            print(f"   Location: {line_info}")
            print(f"   Tool: {issue.tool}")
            print(f"   Description: {issue.description[:100]}{'...' if len(issue.description) > 100 else ''}")
            if issue.recommendation:
                print(f"   Recommendation: {issue.recommendation}")
    else:
        print("\n✅ No security issues detected!")
    
    return result


def test_with_auto_fix(contract_file: str):
    """
    Test Stage 3 with auto-fix (requires OpenAI API key)
    
    Args:
        contract_file: Path to Solidity file
    """
    print("\n" + "="*80)
    print("TEST: Analysis + Auto-Fix")
    print("="*80)
    print(f"Analyzing: {contract_file}")
    print("(Requires OPENAI_API_KEY environment variable)")
    
    # Read contract file
    try:
        contract_code, contract_name = read_contract_file(contract_file)
    except Exception as e:
        print(f"❌ Failed to read contract file: {e}")
        return None
    
    # Try to read metadata
    stage2_metadata = {}
    metadata_file = Path(contract_file).parent / "metadata.json"
    if metadata_file.exists():
        try:
            import json
            with open(metadata_file, "r") as f:
                stage2_metadata = json.load(f)
        except Exception:
            pass
    
    try:
        result = run_stage3(
            solidity_code=contract_code,
            contract_name=contract_name,
            stage2_metadata=stage2_metadata,
            tools=["slither", "mythril", "semgrep", "solhint"],
            max_iterations=2
        )
        
        print("\n" + "="*80)
        print("FIX RESULTS")
        print("="*80)
        print(f"Iterations: {result.iterations}")
        print(f"Issues resolved: {result.issues_resolved}")
        print(f"Initial issues: {len(result.initial_analysis.issues)}")
        print(f"Final issues: {len(result.final_analysis.issues) if result.final_analysis else 0}")
        
        if result.fixes_applied:
            print("\n🔧 Fixes Applied:")
            for fix in result.fixes_applied:
                print(f"  Iteration {fix['iteration']}: {fix['issues_before']} → {fix['issues_after']} issues")
        
        # Save fixed contract
        output_file = Path(contract_file).parent / f"fixed_{Path(contract_file).name}"
        with open(output_file, "w", encoding="utf8") as f:
            f.write(result.final_code)
        print(f"\n💾 Fixed contract saved to: {output_file}")
        
        return result
    
    except Exception as e:
        print(f"\n⚠️ Auto-fix test failed: {e}")
        print("This is expected if OPENAI_API_KEY is not set")
        return None


if __name__ == "__main__":
    # Get contract files
    contract_files = get_contract_files()
    
    if not contract_files:
        print("="*80)
        print("No contract files found!")
        print("="*80)
        print(f"\nPlease add a .sol file to: {Path(__file__).parent / 'contracts'}")
        print("\nExample:")
        print("  stage_3/contracts/my_contract.sol")
        sys.exit(1)
    
    # Use first contract file found
    contract_file = contract_files[0]
    
    if len(contract_files) > 1:
        print(f"⚠️  Multiple files found, using: {Path(contract_file).name}")
        print(f"   (Other files: {', '.join([Path(f).name for f in contract_files[1:]])})")
    
    print(f"\n📄 Analyzing: {Path(contract_file).name}")
    
    # Run analysis
    result = test_analysis_only(contract_file)
    
    if result and result.initial_analysis.success:
        # Optional auto-fix
        print("\n" + "="*80)
        response = input("Run auto-fix? (requires OPENAI_API_KEY) [y/N]: ")
        if response.lower() == 'y':
            test_with_auto_fix(contract_file)
        else:
            print("Skipping auto-fix")
    
    print("\n" + "="*80)
    print("✅ Stage 3 Testing Complete!")
    print("="*80)
    print(f"\nAnalyzed: {Path(contract_file).name}")
    print(f"Results saved in: {Path(contract_file).parent}")

