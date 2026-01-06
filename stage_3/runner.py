"""
Stage 3 Runner
==============

Main entry point for Stage 3 security analysis and auto-fix
"""

from typing import Dict, List, Optional

from .analyzer import SecurityAnalyzer
from .fixer import SecurityFixer
from .models import AnalysisResult, Severity, Stage3Result


def run_stage3(
    solidity_code: str,
    contract_name: str,
    stage2_metadata: Optional[Dict] = None,
    max_iterations: int = 2,
    tools: Optional[List[str]] = None,
    skip_auto_fix: bool = False
) -> Stage3Result:
    """
    Run Stage 3: Security Analysis & Auto-Fix
    
    Args:
        solidity_code: Solidity code from Stage 2
        contract_name: Name of the contract
        stage2_metadata: Stage 2 metadata (profile, coverage, etc.)
        max_iterations: Maximum number of fix iterations
        tools: List of tools to use (default: ["slither", "mythril", "semgrep", "solhint"])
        skip_auto_fix: If True, only run analysis (no fixing)
    
    Returns:
        Stage3Result with analysis and fix results
    """
    print("\n" + "="*80)
    print("STAGE 3: SECURITY ANALYSIS" + (" & AUTO-FIX" if not skip_auto_fix else ""))
    print("Mode: Docker-based execution (Windows compatible)")
    if skip_auto_fix:
        print("Mode: Issue detection only (auto-fix disabled)")
    print("="*80)
    
    # Allow verbose to be passed via options (for pipeline integration)
    verbose = stage2_metadata.get("_verbose", False) if stage2_metadata else False
    analyzer = SecurityAnalyzer(verbose=verbose)
    fixer = SecurityFixer()
    
    original_code = solidity_code
    current_code = solidity_code
    fixes_applied = []
    
    # Initial analysis
    print("\n[1/2] Security analysis")
    initial_analysis = analyzer.analyze(current_code, contract_name, tools)
    
    if not initial_analysis.success:
        print(f"\n  ✗ Analysis failed: {initial_analysis.error}")
        return Stage3Result(
            original_code=original_code,
            final_code=current_code,
            iterations=0,
            initial_analysis=initial_analysis,
            final_analysis=None,
            fixes_applied=[],
            issues_resolved=0,
            stage2_metadata=stage2_metadata,
            compiles=None
        )
    
    print(f"\n  Found {len(initial_analysis.issues)} total issues:")
    print(f"    • Critical: {len(initial_analysis.get_by_severity(Severity.CRITICAL))}")
    print(f"    • High: {len(initial_analysis.get_by_severity(Severity.HIGH))}")
    print(f"    • Medium: {len(initial_analysis.get_by_severity(Severity.MEDIUM))}")
    print(f"    • Low: {len(initial_analysis.get_by_severity(Severity.LOW))}")
    print(f"    • Info: {len(initial_analysis.get_by_severity(Severity.INFO))}")
    
    # Skip auto-fix if requested
    if skip_auto_fix:
        print("\n[2/2] Skipping auto-fix")
        print("\n✅ Stage 3 Complete (Analysis Only):")
        print(f"  • Issues found: {len(initial_analysis.issues)}")
        
        return Stage3Result(
            original_code=original_code,
            final_code=current_code,
            iterations=0,
            initial_analysis=initial_analysis,
            final_analysis=initial_analysis,
            fixes_applied=[],
            issues_resolved=0,
            stage2_metadata=stage2_metadata,
            compiles=None
        )
    
    # Iterative fixing
    print("\n[2/3] Applying automatic fixes")
    
    iteration = 0
    current_analysis = initial_analysis
    
    while iteration < max_iterations:
        high_priority = current_analysis.get_critical_high()
        
        if not high_priority:
            print(f"\n  ✓ No critical/high issues after {iteration} iterations")
            break
        
        iteration += 1
        
        fixed_code = fixer.fix_issues(
            current_code,
            high_priority,
            contract_name,
            stage2_metadata,
            iteration
        )
        
        if fixed_code == current_code:
            print(f"  ⚠️ No changes in iteration {iteration}")
            break
        
        current_code = fixed_code
        
        print(f"\n  🔍 Re-analyzing...")
        current_analysis = analyzer.analyze(current_code, contract_name, tools)
        
        if not current_analysis.success:
            print(f"  ⚠️ Re-analysis failed")
            current_code = original_code
            break
        
        fixes_applied.append({
            "iteration": iteration,
            "issues_before": len(high_priority),
            "issues_after": len(current_analysis.get_critical_high())
        })
        
        print(f"  ✓ Iteration {iteration}: {len(current_analysis.issues)} issues remain")
    
    # Final check
    print("\n[3/3] Final verification")
    final_analysis = current_analysis if iteration > 0 else initial_analysis
    
    issues_resolved = len(initial_analysis.issues) - len(final_analysis.issues)
    
    print(f"\n✅ Stage 3 Complete:")
    print(f"  • Iterations: {iteration}")
    print(f"  • Initial issues: {len(initial_analysis.issues)}")
    print(f"  • Final issues: {len(final_analysis.issues)}")
    print(f"  • Issues resolved: {issues_resolved}")
    
    return Stage3Result(
        original_code=original_code,
        final_code=current_code,
        iterations=iteration,
        initial_analysis=initial_analysis,
        final_analysis=final_analysis,
        fixes_applied=fixes_applied,
        issues_resolved=issues_resolved,
        stage2_metadata=stage2_metadata,
        compiles=None  # Compile check can be added if needed
    )

