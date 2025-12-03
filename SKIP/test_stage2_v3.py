import json
import os
from datetime import datetime
from stage_1.intent_extraction import extract_intent
from solidity_generator_v3 import generate_solidity_v3


USER_INPUT = """Create a tax token that charges 3% on every transfer and sends the tax to the treasury wallet.
"""

# =============================================================================
# PIPELINE EXECUTION
# =============================================================================

def run_single_pipeline(user_input: str):
    """Runs Stage 1 + Stage 2 for a single user prompt."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = f"output/{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 80)
    print("SMART CONTRACT GENERATION PIPELINE — SINGLE INPUT MODE")
    print("=" * 80)

    print("\n📝 USER INPUT:")
    print("-" * 80)
    print(user_input.strip())
    print("-" * 80)

    # =====================================================================
    # STAGE 1: INTENT EXTRACTION
    # =====================================================================
    print("\n[1/2] Running Stage 1: Intent Extraction...")
    
    try:
        json_spec = extract_intent(user_input)
        print("✓ Stage 1 complete\n")
    except Exception as e:
        print(f"❌ Stage 1 FAILED: {e}")
        return
    
    print("Extracted JSON Spec:")
    print(json.dumps(json_spec, indent=2))

    # Save Stage 1 output
    spec_file = f"{output_dir}/spec.json"
    with open(spec_file, "w") as f:
        json.dump(json_spec, f, indent=2)
    print(f"\n✓ Saved Stage 1 Output: {spec_file}")

    # =====================================================================
    # STAGE 2: ENHANCED CODE GENERATION
    # =====================================================================
    print("\n[2/2] Running Stage 2: Enhanced Solidity Generation...")

    try:
        result = generate_solidity_v3(json_spec)
    except Exception as e:
        print(f"❌ Stage 2 FAILED: {e}")
        return

    print("\n✓ Stage 2 Complete")

    # Save outputs
    contract_file = f"{output_dir}/{json_spec.get('contract_name','Contract')}.sol"
    metadata_file = f"{output_dir}/metadata.json"
    coverage_file = f"{output_dir}/coverage.json"

    with open(contract_file, "w") as f:
        f.write(result.solidity_code)

    with open(metadata_file, "w") as f:
        json.dump(result.to_metadata_dict(), f, indent=2)

    with open(coverage_file, "w") as f:
        json.dump(result.coverage.to_dict(), f, indent=2)

    print("\n📦 OUTPUT FILES SAVED:")
    print(f"  ✓ Solidity Contract:    {contract_file}")
    print(f"  ✓ Metadata:            {metadata_file}")
    print(f"  ✓ Coverage Report:     {coverage_file}")

    print("\n" + "=" * 80)
    print("🎉 PIPELINE COMPLETE")
    print("=" * 80)


# =============================================================================
# MAIN ENTRY (AUTO-RUN)
# =============================================================================

if __name__ == "__main__":
    # No CLI args, no terminal input. Only use the variable inside file.
    run_single_pipeline(USER_INPUT)
