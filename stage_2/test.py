import os
import sys
import json
import shutil
from datetime import datetime

from stage_1.intent_extraction import extract_intent
from stage_2.generator import generate_solidity


USER_INPUT = """Build a rental NFT system where users can rent NFTs for a fixed duration.
"""


# ------------------------------------------------------------------------------
# Utility Helpers
# ------------------------------------------------------------------------------

def ensure(path: str):
    os.makedirs(path, exist_ok=True)


# ------------------------------------------------------------------------------
# Pipeline Runner
# ------------------------------------------------------------------------------

def run_pipeline(user_input: str):
    print("\n" + "="*80)
    print("RUNNING FULL PIPELINE")
    print("="*80)
    print("\n📝 USER INPUT:")
    print(user_input)
    print("\n" + "-"*80)

    # ------------------------------------------------------------------  
    # Stage 1 — Intent Extraction  
    # ------------------------------------------------------------------
    print("\n[1/3] Stage 1: Extracting contract intent...")
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
    # Stage 2 — Solidity Generation  
    # ------------------------------------------------------------------
    print("\n[2/3] Stage 2: Generating Solidity...")
    try:
        result = generate_solidity(spec, debug=True)  # Enable debug to see semantic validation
    except Exception as e:
        print(f"❌ Stage 2 Failed: {e}")
        return

    print("✓ Stage 2 complete.")

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


# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------

def main():

    if not USER_INPUT.strip():
        print("No input provided.")
        return

    run_pipeline(USER_INPUT)


if __name__ == "__main__":
    main()
