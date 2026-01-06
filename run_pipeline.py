"""
Pipeline Runner
===============

Runs the complete pipeline (Stage 1 → Stage 2 V2 → Stage 3) with user input.
Edit the USER_INPUT variable below to specify your contract description.

Stage 2 V2 uses LLM-powered classification for generalized contract generation.
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

from stage_1.intent_extraction import extract_intent
from stage_2_v2.generator_v2 import generate_solidity_v2
from stage_3 import run_stage3


# ============================================================================
# CONFIGURATION - Edit these values to customize the pipeline
# ============================================================================

# User input: Natural language description of the smart contract
# You can include main description and conditions like:
#   "Create a token vault where users can deposit tokens."
#   Conditions: Only the owner can withdraw. Users can check their balance.
USER_INPUT = """Create a rental NFT system where users can rent NFTs for a fixed duration."""

# Stage 3 Configuration
STAGE3_CONFIG = {
    "enable_stage3": True,      # Set to False to skip Stage 3 security analysis
    "skip_auto_fix": False,     # Set to True for analysis only (no auto-fix)
    "max_iterations": 2,         # Maximum number of fix iterations (1-5)
    "verbose": False             # Set to True to see detailed tool execution logs
}

# ============================================================================


def ensure(path: str):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)




def run_full_pipeline(user_input: str, stage3_options: dict):
    """
    Run complete pipeline: Stage 1 → Stage 2 → Stage 3
    
    Args:
        user_input: Natural language description of contract
        stage3_options: Dictionary with Stage 3 configuration
    """
    print("\n" + "="*80)
    print("RUNNING FULL PIPELINE (Stage 1 → Stage 2 → Stage 3)")
    print("="*80)
    print("\n📝 USER INPUT:")
    print(user_input)
    print("\n" + "-"*80)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = f"pipeline_outputs/{timestamp}"
    ensure(outdir)
    
    # ------------------------------------------------------------------  
    # Stage 1 — Intent Extraction  
    # ------------------------------------------------------------------
    print("\n[1/3] Stage 1: Extracting contract intent...")
    print("-" * 80)
    try:
        spec = extract_intent(user_input)
        print("✅ Stage 1 complete!")
        print(f"\n📋 Contract Specification:")
        print(f"   • Contract Name: {spec.get('contract_name', 'Unknown')}")
        print(f"   • Contract Type: {spec.get('contract_type', 'Unknown')}")
        print(f"   • Functions: {len(spec.get('functions', []))}")
        print(f"   • State Variables: {len(spec.get('state_variables', []))}")
        print(f"   • Events: {len(spec.get('events', []))}")
    except Exception as e:
        print(f"❌ Stage 1 Failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Save Stage 1 output
    with open(f"{outdir}/stage1_spec.json", "w") as f:
        json.dump(spec, f, indent=2)
    print(f"   📄 Saved: {outdir}/stage1_spec.json")
    
    # ------------------------------------------------------------------  
    # Stage 2 V2 — LLM-Powered Solidity Generation  
    # ------------------------------------------------------------------
    print("\n[2/3] Stage 2 V2: LLM-Powered Solidity Generation...")
    print("-" * 80)
    try:
        stage2_result = generate_solidity_v2(user_input, spec, debug=False)
        print("✅ Stage 2 V2 complete!")
    except Exception as e:
        print(f"❌ Stage 2 Failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Save Stage 2 outputs
    contract_name = spec.get('contract_name', 'Contract')
    sol_path = f"{outdir}/{contract_name}.sol"
    meta_path = f"{outdir}/metadata.json"
    
    with open(sol_path, "w") as f:
        f.write(stage2_result.solidity_code)
    
    with open(meta_path, "w") as f:
        json.dump(stage2_result.to_metadata_dict(), f, indent=2)
    
    print(f"\n📦 Stage 2 outputs saved:")
    print(f"   • Solidity: {sol_path}")
    print(f"   • Metadata: {meta_path}")
    
    # Show contract preview
    lines = stage2_result.solidity_code.split('\n')
    print(f"\n📄 Contract Preview (first 20 lines):")
    for i, line in enumerate(lines[:20], 1):
        print(f"   {i:3d} | {line}")
    if len(lines) > 20:
        print(f"   ... ({len(lines) - 20} more lines)")
    
    # ------------------------------------------------------------------  
    # Stage 3 — Security Analysis & Auto-Fix  
    # ------------------------------------------------------------------
    stage3_result = None
    if stage3_options.get("enable_stage3", True):
        print("\n[3/3] Stage 3: Security Analysis" + 
              (" & Auto-Fix" if not stage3_options.get("skip_auto_fix", False) else ""))
        print("-" * 80)
        
        try:
            # Add verbose flag to metadata for Stage 3
            stage2_metadata = stage2_result.to_metadata_dict()
            stage2_metadata["_verbose"] = stage3_options.get("verbose", False)
            
            stage3_result = run_stage3(
                solidity_code=stage2_result.solidity_code,
                contract_name=contract_name,
                stage2_metadata=stage2_metadata,
                max_iterations=stage3_options.get("max_iterations", 2),
                tools=["slither", "mythril", "semgrep", "solhint"],
                skip_auto_fix=stage3_options.get("skip_auto_fix", False)
            )
            
            # Save Stage 3 outputs
            final_sol_path = f"{outdir}/final_{contract_name}.sol"
            with open(final_sol_path, "w") as f:
                f.write(stage3_result.final_code)
            
            stage3_report_path = f"{outdir}/stage3_report.json"
            with open(stage3_report_path, "w") as f:
                json.dump(stage3_result.to_dict(), f, indent=2)
            
            print(f"\n📦 Stage 3 outputs saved:")
            print(f"   • Fixed Contract: {final_sol_path}")
            print(f"   • Security Report: {stage3_report_path}")
            
            # Show summary
            print(f"\n📊 Stage 3 Summary:")
            initial_issues = len(stage3_result.initial_analysis.issues)
            final_issues = len(stage3_result.final_analysis.issues) if stage3_result.final_analysis else 0
            print(f"   • Initial issues found: {initial_issues}")
            print(f"   • Final issues: {final_issues}")
            print(f"   • Issues resolved: {stage3_result.issues_resolved}")
            print(f"   • Iterations: {stage3_result.iterations}")
            
            # Show severity breakdown
            if initial_issues > 0:
                from stage_3.models import Severity
                print(f"\n   Issue Breakdown (Initial):")
                print(f"     - Critical: {len(stage3_result.initial_analysis.get_by_severity(Severity.CRITICAL))}")
                print(f"     - High: {len(stage3_result.initial_analysis.get_by_severity(Severity.HIGH))}")
                print(f"     - Medium: {len(stage3_result.initial_analysis.get_by_severity(Severity.MEDIUM))}")
                print(f"     - Low: {len(stage3_result.initial_analysis.get_by_severity(Severity.LOW))}")
                print(f"     - Info: {len(stage3_result.initial_analysis.get_by_severity(Severity.INFO))}")
        
        except Exception as e:
            print(f"⚠️  Stage 3 Failed: {e}")
            print("Continuing with Stage 2 output only...")
            import traceback
            traceback.print_exc()
            stage3_result = None
    else:
        print("\n[3/3] Stage 3: Skipped")
    
    # ------------------------------------------------------------------  
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETE")
    print("="*80)
    print(f"\n📁 All outputs saved in: {outdir}")
    print(f"\n📋 Files generated:")
    print(f"   • stage1_spec.json - Intent specification")
    print(f"   • {contract_name}.sol - Generated contract")
    print(f"   • metadata.json - Stage 2 metadata")
    if stage3_result:
        print(f"   • final_{contract_name}.sol - Security-fixed contract")
        print(f"   • stage3_report.json - Security analysis report")
    
    return {
        "output_dir": outdir,
        "spec": spec,
        "stage2_result": stage2_result,
        "stage3_result": stage3_result
    }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run the complete pipeline (Stage 1 → Stage 2 → Stage 3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use USER_INPUT variable from file (default)
  python run_pipeline.py
  
  # Override with command-line input
  python run_pipeline.py --input "Create a token vault" --skip-stage3
  
  # Override with analysis only
  python run_pipeline.py --input "Create an election system" --analysis-only
        """
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Override USER_INPUT variable with command-line input"
    )
    parser.add_argument(
        "--skip-stage3",
        action="store_true",
        help="Skip Stage 3 security analysis (overrides STAGE3_CONFIG)"
    )
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Run Stage 3 analysis only (no auto-fix, overrides STAGE3_CONFIG)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum fix iterations (overrides STAGE3_CONFIG)"
    )
    
    args = parser.parse_args()
    
    try:
        # Get user input (use command-line arg if provided, otherwise use variable)
        if args.input:
            user_input = args.input
            print("\n" + "="*80)
            print("SMART CONTRACT PIPELINE")
            print("="*80)
            print(f"\n📝 Input (from command-line): {user_input}")
        else:
            user_input = USER_INPUT
            if not user_input or not user_input.strip():
                print("❌ USER_INPUT is empty. Please edit the USER_INPUT variable in run_pipeline.py")
                print("   Or use --input flag: python run_pipeline.py --input 'Your description'")
                sys.exit(1)
            print("\n" + "="*80)
            print("SMART CONTRACT PIPELINE")
            print("="*80)
            print(f"\n📝 Input (from USER_INPUT variable): {user_input}")
        
        # Get Stage 3 options (command-line args override config)
        stage3_options = STAGE3_CONFIG.copy()
        
        if args.skip_stage3:
            stage3_options["enable_stage3"] = False
        elif args.analysis_only:
            stage3_options["enable_stage3"] = True
            stage3_options["skip_auto_fix"] = True
            stage3_options["max_iterations"] = 1
        
        if args.max_iterations:
            stage3_options["max_iterations"] = args.max_iterations
        
        print(f"\n⚙️  Stage 3 Config:")
        print(f"   • Enable Stage 3: {stage3_options['enable_stage3']}")
        if stage3_options['enable_stage3']:
            print(f"   • Auto-fix: {not stage3_options['skip_auto_fix']}")
            print(f"   • Max iterations: {stage3_options['max_iterations']}")
        
        # Run pipeline
        result = run_full_pipeline(user_input, stage3_options)
        
        if result:
            print("\n" + "="*80)
            if result.get("stage3_result"):
                print("✅ Pipeline completed successfully!")
                print(f"📄 Final secure contract: {result['output_dir']}/final_{result['spec']['contract_name']}.sol")
            else:
                print("✅ Pipeline completed (Stage 3 skipped or failed)")
                print(f"📄 Generated contract: {result['output_dir']}/{result['spec']['contract_name']}.sol")
            print("="*80)
        else:
            print("\n❌ Pipeline failed. Check errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

