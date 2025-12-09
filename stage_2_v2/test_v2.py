import os
import sys
import json
from datetime import datetime

# Add parent directory to path to import from stage_1 and stage_2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage_1.intent_extraction import extract_intent
from stage_2_v2.generator_v2 import generate_solidity_v2


USER_INPUT = """
"Implement a smart contract for a secure and transparent decentralized autonomous organization (DAO) voting system."

Conditions: Token holders can submit proposals and vote on them using their tokens. The contract ensures that each token is counted once, prevents double-voting, calculates the results, and automatically executes the approved actions (e.g., updating a protocol parameter) when a majority is reached.

"""


def ensure(path: str):
    os.makedirs(path, exist_ok=True)


def run_pipeline_v2(user_input: str):
    """
    Run the v2 pipeline with LLM-powered classification.
    """
    print("\n" + "="*80)
    print("RUNNING V2 PIPELINE (LLM-POWERED)")
    print("="*80)
    print("\n📝 USER INPUT:")
    print(user_input)
    print("\n" + "-"*80)

    # ------------------------------------------------------------------  
    # Stage 1 — Intent Extraction  
    # ------------------------------------------------------------------
    print("\n[1/2] Stage 1: Extracting contract intent...")
    try:
        spec = extract_intent(user_input)
    except Exception as e:
        print(f"❌ Stage 1 Failed: {e}")
        return

    print("✓ Stage 1 complete. JSON Spec:")
    print(json.dumps(spec, indent=2))

    # Output folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outdir = f"pipeline_outputs/{timestamp}"
    ensure(outdir)

    with open(f"{outdir}/stage1_spec.json", "w") as f:
        json.dump(spec, f, indent=2)

    # ------------------------------------------------------------------  
    # Stage 2 V2 — LLM-Powered Solidity Generation  
    # ------------------------------------------------------------------
    print("\n[2/2] Stage 2 V2: LLM-Powered Solidity Generation...")
    try:
        result = generate_solidity_v2(user_input, spec, debug=True)
    except Exception as e:
        print(f"❌ Stage 2 V2 Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("✓ Stage 2 V2 complete.")

    # Save Solidity + Metadata
    sol_path = f"{outdir}/{spec.get('contract_name', 'Contract')}.sol"
    meta_path = f"{outdir}/metadata.json"

    with open(sol_path, "w") as f:
        f.write(result.solidity_code)

    with open(meta_path, "w") as f:
        json.dump(result.to_metadata_dict(), f, indent=2)

    print(f"\n📦 Outputs saved in: {outdir}")
    print(f" - Solidity: {sol_path}")
    print(f" - Metadata: {meta_path}")

    print("\n" + "="*80)
    print("PIPELINE COMPLETE")
    print("="*80)


def main():
    """
    Execute v2 pipeline with USER_INPUT from the file.
    """
    print("="*80)
    print("V2 PIPELINE EXECUTION (LLM-POWERED)")
    print("="*80)
    
    # Check if USER_INPUT is set and not empty
    if not USER_INPUT or not USER_INPUT.strip():
        print("❌ No input found!")
        print("\nPlease set USER_INPUT variable in test_v2.py")
        return
    
    print(f"✓ Using input from USER_INPUT\n")
    run_pipeline_v2(USER_INPUT.strip())


if __name__ == "__main__":
    main()
