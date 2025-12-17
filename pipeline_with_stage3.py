"""
Complete Pipeline: Stage 1 → Stage 2 → Stage 3
==============================================
"""

import os
import json
from datetime import datetime

from stage_1.intent_extraction import extract_intent
from stage_2.generator import generate_solidity
from stage_3 import run_stage3


def ensure(path: str):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)


def run_full_pipeline(user_input: str, enable_stage3: bool = True):
    """
    Run complete pipeline: Stage 1 → Stage 2 → Stage 3
    
    Args:
        user_input: Natural language description of contract
        enable_stage3: Whether to run Stage 3 security analysis
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
    try:
        spec = extract_intent(user_input)
    except Exception as e:
        print(f"❌ Stage 1 Failed: {e}")
        return None
    
    print("✓ Stage 1 complete. JSON Spec:")
    print(json.dumps(spec, indent=2))
    
    with open(f"{outdir}/stage1_spec.json", "w") as f:
        json.dump(spec, f, indent=2)
    
    # ------------------------------------------------------------------  
    # Stage 2 — Solidity Generation  
    # ------------------------------------------------------------------
    print("\n[2/3] Stage 2: Generating Solidity...")
    try:
        stage2_result = generate_solidity(spec, debug=True)
    except Exception as e:
        print(f"❌ Stage 2 Failed: {e}")
        return None
    
    print("✓ Stage 2 complete.")
    
    # Save Stage 2 outputs
    sol_path = f"{outdir}/{spec.get('contract_name', 'Contract')}.sol"
    meta_path = f"{outdir}/metadata.json"
    
    with open(sol_path, "w") as f:
        f.write(stage2_result.solidity_code)
    
    with open(meta_path, "w") as f:
        json.dump(stage2_result.to_metadata_dict(), f, indent=2)
    
    print(f"\n📦 Stage 2 outputs saved:")
    print(f" - Solidity: {sol_path}")
    print(f" - Metadata: {meta_path}")
    
    # ------------------------------------------------------------------  
    # Stage 3 — Security Analysis & Auto-Fix  
    # ------------------------------------------------------------------
    if enable_stage3:
        print("\n[3/3] Stage 3: Security Analysis & Auto-Fix...")
        try:
            stage3_result = run_stage3(
                solidity_code=stage2_result.solidity_code,
                contract_name=spec.get("contract_name", "Contract"),
                stage2_metadata=stage2_result.to_metadata_dict(),
                max_iterations=2,
                tools=["slither", "mythril", "semgrep", "solhint"]
            )
            
            # Save Stage 3 outputs
            final_sol_path = f"{outdir}/final_{spec.get('contract_name', 'Contract')}.sol"
            with open(final_sol_path, "w") as f:
                f.write(stage3_result.final_code)
            
            stage3_report_path = f"{outdir}/stage3_report.json"
            with open(stage3_report_path, "w") as f:
                json.dump(stage3_result.to_dict(), f, indent=2)
            
            print(f"\n📦 Stage 3 outputs saved:")
            print(f" - Fixed Contract: {final_sol_path}")
            print(f" - Security Report: {stage3_report_path}")
            
            print(f"\n📊 Stage 3 Summary:")
            print(f" - Initial issues: {len(stage3_result.initial_analysis.issues)}")
            print(f" - Final issues: {len(stage3_result.final_analysis.issues) if stage3_result.final_analysis else 0}")
            print(f" - Issues resolved: {stage3_result.issues_resolved}")
            print(f" - Iterations: {stage3_result.iterations}")
        
        except Exception as e:
            print(f"⚠️ Stage 3 Failed: {e}")
            print("Continuing with Stage 2 output only...")
            stage3_result = None
    else:
        print("\n[3/3] Stage 3: Skipped (enable_stage3=False)")
        stage3_result = None
    
    # ------------------------------------------------------------------  
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "="*80)
    print("PIPELINE COMPLETE")
    print("="*80)
    print(f"\n📁 All outputs saved in: {outdir}")
    print(f"\nFiles generated:")
    print(f"  • stage1_spec.json - Intent specification")
    print(f"  • {spec.get('contract_name', 'Contract')}.sol - Generated contract")
    print(f"  • metadata.json - Stage 2 metadata")
    if stage3_result:
        print(f"  • final_{spec.get('contract_name', 'Contract')}.sol - Security-fixed contract")
        print(f"  • stage3_report.json - Security analysis report")
    
    return {
        "output_dir": outdir,
        "spec": spec,
        "stage2_result": stage2_result,
        "stage3_result": stage3_result
    }


# ------------------------------------------------------------------------------  
# Example Usage
# ------------------------------------------------------------------------------  

if __name__ == "__main__":
    USER_INPUT = """Build a rental NFT system where users can rent NFTs for a fixed duration."""
    
    result = run_full_pipeline(USER_INPUT, enable_stage3=True)
    
    if result and result["stage3_result"]:
        print("\n✅ Pipeline completed successfully!")
        print(f"Final secure contract: {result['output_dir']}/final_{result['spec']['contract_name']}.sol")
    else:
        print("\n⚠️ Pipeline completed with warnings (check output above)")

