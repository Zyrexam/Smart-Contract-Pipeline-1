"""
Complete Smart Contract Generation Pipeline
===========================================

Stage 1: Intent Extraction (Natural Language → JSON)
Stage 2: Code Generation (JSON → Solidity)
Stage 3: Security Analysis & Auto-Fix (Solidity → Secure Solidity)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from stage_1.intent_extraction import extract_intent
from stage_2.solidity_generator_v3 import generate_solidity_v3, GenerationResult
from security_integration import analyze_and_fix, Stage3Result


# ============================================================================
# FULL PIPELINE ORCHESTRATOR
# ============================================================================

def run_complete_pipeline(
    user_input: str,
    enable_stage3: bool = True,
    max_security_iterations: int = 3,
    smartbugs_path: str = "./smartbugs",
    security_tools: Optional[list] = None,
    output_dir: Optional[str] = None
) -> dict:
    """
    Run the complete 3-stage smart contract generation pipeline.
    
    Args:
        user_input: Natural language contract description
        enable_stage3: Whether to run security analysis
        max_security_iterations: Maximum iterations for security fixes
        smartbugs_path: Path to SmartBugs installation
        security_tools: Tools to use for analysis (default: slither, mythril)
        output_dir: Where to save outputs (default: output/timestamp/)
    
    Returns:
        dict with all pipeline results
    """
    
    # Setup output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"output/{timestamp}"
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 80)
    print("SMART CONTRACT GENERATION PIPELINE")
    print("3-Stage: Intent → Code → Security")
    print("=" * 80)
    
    print(f"\n📝 User Input:")
    print("-" * 80)
    print(user_input.strip())
    print("-" * 80)
    
    results = {
        "user_input": user_input,
        "output_directory": str(output_path),
        "stage1_result": None,
        "stage2_result": None,
        "stage3_result": None,
        "success": False,
        "final_contract": None
    }
    
    # =========================================================================
    # STAGE 1: INTENT EXTRACTION
    # =========================================================================
    print("\n" + "🔷" * 40)
    print("STAGE 1: INTENT EXTRACTION")
    print("🔷" * 40)
    
    try:
        json_spec = extract_intent(user_input)
        results["stage1_result"] = json_spec
        
        print("\n✅ Stage 1 Complete")
        print(f"Contract Type: {json_spec.get('contract_type')}")
        print(f"Functions: {len(json_spec.get('functions', []))}")
        print(f"State Variables: {len(json_spec.get('state_variables', []))}")
        
        # Save Stage 1 output
        stage1_file = output_path / "stage1_intent.json"
        with open(stage1_file, 'w') as f:
            json.dump(json_spec, f, indent=2)
        print(f"\n💾 Saved: {stage1_file}")
        
    except Exception as e:
        print(f"\n❌ Stage 1 Failed: {e}")
        import traceback
        traceback.print_exc()
        return results
    
    # =========================================================================
    # STAGE 2: CODE GENERATION
    # =========================================================================
    print("\n" + "🔷" * 40)
    print("STAGE 2: SOLIDITY CODE GENERATION")
    print("🔷" * 40)
    
    try:
        stage2_result: GenerationResult = generate_solidity_v3(json_spec)
        results["stage2_result"] = stage2_result.to_metadata_dict()
        
        print("\n✅ Stage 2 Complete")
        print(f"Category: {stage2_result.profile.category.value}")
        print(f"Base Standard: {stage2_result.profile.base_standard}")
        print(f"Extensions: {', '.join(stage2_result.profile.extensions) or 'None'}")
        
        # Save Stage 2 outputs
        contract_name = json_spec.get('contract_name', 'GeneratedContract')
        
        stage2_contract_file = output_path / f"{contract_name}_stage2.sol"
        with open(stage2_contract_file, 'w') as f:
            f.write(stage2_result.solidity_code)
        
        stage2_metadata_file = output_path / "stage2_metadata.json"
        with open(stage2_metadata_file, 'w') as f:
            json.dump(stage2_result.to_metadata_dict(), f, indent=2)
        
        stage2_coverage_file = output_path / "stage2_coverage.json"
        with open(stage2_coverage_file, 'w') as f:
            json.dump(stage2_result.coverage.to_dict(), f, indent=2)
        
        print(f"\n💾 Saved:")
        print(f"  • {stage2_contract_file}")
        print(f"  • {stage2_metadata_file}")
        print(f"  • {stage2_coverage_file}")
        
        # Set as current final contract
        results["final_contract"] = stage2_result.solidity_code
        
    except Exception as e:
        print(f"\n❌ Stage 2 Failed: {e}")
        import traceback
        traceback.print_exc()
        return results
    
    # =========================================================================
    # STAGE 3: SECURITY ANALYSIS & AUTO-FIX (Optional)
    # =========================================================================
    if enable_stage3:
        print("\n" + "🔷" * 40)
        print("STAGE 3: SECURITY ANALYSIS & AUTO-FIX")
        print("🔷" * 40)
        
        # Check if SmartBugs is available
        if not Path(smartbugs_path).exists():
            print(f"\n⚠️  SmartBugs not found at {smartbugs_path}")
            print("To enable Stage 3:")
            print("  1. git clone https://github.com/smartbugs/smartbugs.git")
            print("  2. Follow SmartBugs setup instructions")
            print("\nSkipping Stage 3 for now...")
        else:
            try:
                stage3_result: Stage3Result = analyze_and_fix(
                    solidity_code=stage2_result.solidity_code,
                    contract_name=contract_name,
                    max_iterations=max_security_iterations,
                    smartbugs_path=smartbugs_path,
                    tools=security_tools
                )
                
                results["stage3_result"] = stage3_result.to_dict()
                
                print("\n✅ Stage 3 Complete")
                print(f"Iterations: {stage3_result.iterations}")
                print(f"Initial Issues: {len(stage3_result.initial_analysis.issues_found)}")
                print(f"Final Issues: {len(stage3_result.remaining_issues)}")
                print(f"Issues Resolved: {len(stage3_result.initial_analysis.issues_found) - len(stage3_result.remaining_issues)}")
                
                # Save Stage 3 outputs
                stage3_contract_file = output_path / f"{contract_name}_final.sol"
                with open(stage3_contract_file, 'w') as f:
                    f.write(stage3_result.final_code)
                
                stage3_report_file = output_path / "stage3_security_report.json"
                with open(stage3_report_file, 'w') as f:
                    json.dump(stage3_result.to_dict(), f, indent=2)
                
                # Save initial analysis
                initial_analysis_file = output_path / "stage3_initial_analysis.json"
                with open(initial_analysis_file, 'w') as f:
                    json.dump(stage3_result.initial_analysis.to_dict(), f, indent=2)
                
                # Save remaining issues
                if stage3_result.remaining_issues:
                    issues_file = output_path / "stage3_remaining_issues.json"
                    with open(issues_file, 'w') as f:
                        json.dump(
                            [issue.to_dict() for issue in stage3_result.remaining_issues],
                            f,
                            indent=2
                        )
                
                print(f"\n💾 Saved:")
                print(f"  • {stage3_contract_file}")
                print(f"  • {stage3_report_file}")
                print(f"  • {initial_analysis_file}")
                if stage3_result.remaining_issues:
                    print(f"  • {issues_file}")
                
                # Update final contract
                results["final_contract"] = stage3_result.final_code
                
            except Exception as e:
                print(f"\n❌ Stage 3 Failed: {e}")
                import traceback
                traceback.print_exc()
                print("\n⚠️  Continuing with Stage 2 output as final contract")
    else:
        print("\n⚠️  Stage 3 disabled, using Stage 2 output as final contract")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    
    # Save pipeline summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "user_input": user_input,
        "stages_completed": [],
        "output_directory": str(output_path),
        "final_contract_file": f"{contract_name}_{'final' if enable_stage3 else 'stage2'}.sol"
    }
    
    if results["stage1_result"]:
        summary["stages_completed"].append("Stage 1: Intent Extraction")
        summary["contract_name"] = results["stage1_result"].get("contract_name")
        summary["contract_type"] = results["stage1_result"].get("contract_type")
    
    if results["stage2_result"]:
        summary["stages_completed"].append("Stage 2: Code Generation")
        summary["category"] = results["stage2_result"].get("category")
        summary["base_standard"] = results["stage2_result"].get("base_standard")
    
    if results["stage3_result"]:
        summary["stages_completed"].append("Stage 3: Security Analysis")
        summary["security_iterations"] = results["stage3_result"]["iterations"]
        summary["issues_resolved"] = (
            results["stage3_result"]["summary"]["initial_issues"] -
            results["stage3_result"]["summary"]["final_issues"]
        )
    
    summary_file = output_path / "pipeline_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📊 Pipeline Summary:")
    print(f"  ✓ {len(summary['stages_completed'])} stages completed")
    for stage in summary["stages_completed"]:
        print(f"    • {stage}")
    
    print(f"\n💾 All outputs saved to: {output_path}/")
    print(f"\n🎉 Final contract: {output_path}/{summary['final_contract_file']}")
    
    results["success"] = True
    results["summary"] = summary
    
    return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def run_quick_pipeline(user_input: str, with_security: bool = False):
    """
    Quick run with defaults.
    
    Args:
        user_input: Natural language contract description
        with_security: Whether to run Stage 3 (requires SmartBugs setup)
    """
    return run_complete_pipeline(
        user_input=user_input,
        enable_stage3=with_security,
        max_security_iterations=2
    )


def run_pipeline_from_file(input_file: str, with_security: bool = False):
    """
    Run pipeline with input from a text file.
    
    Args:
        input_file: Path to file containing contract description
        with_security: Whether to run Stage 3
    """
    with open(input_file, 'r') as f:
        user_input = f.read()
    
    return run_complete_pipeline(
        user_input=user_input,
        enable_stage3=with_security
    )


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Example usage
    test_input = """
Create a staking contract where users can:
- Stake ERC20 tokens to earn rewards
- Unstake their tokens anytime
- Claim accumulated rewards
- Owner can set the reward rate
- Emergency pause functionality
"""
    
    # Check command line args
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage:")
            print("  python full_pipeline.py [--with-security]")
            print("  python full_pipeline.py --file <input.txt> [--with-security]")
            print("\nOptions:")
            print("  --with-security    Enable Stage 3 security analysis (requires SmartBugs)")
            print("  --file <path>      Read contract description from file")
            sys.exit(0)
        
        enable_security = "--with-security" in sys.argv
        
        if "--file" in sys.argv:
            file_idx = sys.argv.index("--file")
            if file_idx + 1 < len(sys.argv):
                input_file = sys.argv[file_idx + 1]
                run_pipeline_from_file(input_file, enable_security)
            else:
                print("Error: --file requires a path argument")
                sys.exit(1)
        else:
            run_quick_pipeline(test_input, enable_security)
    else:
        # Default: run without security
        print("Running with default test input (Stage 1 + 2 only)")
        print("Use --with-security to enable Stage 3")
        print("Use --help for more options\n")
        
        run_quick_pipeline(test_input, with_security=False)