"""
Run Stage 3 on all existing contracts in pipeline_outputs
==========================================================

This script processes all contract directories in pipeline_outputs that don't have
stage3_report.json files yet, running Stage 3 security analysis on them.
"""

import json
import os
from pathlib import Path
from stage_3 import run_stage3


def find_sol_file(directory: Path) -> Path:
    """Find the .sol file in a directory"""
    sol_files = list(directory.glob("*.sol"))
    if not sol_files:
        return None
    
    # Skip files that are just ".sol" (empty names)
    valid_files = [f for f in sol_files if f.stem]
    if not valid_files:
        return None
    
    return valid_files[0]


def get_contract_name(sol_file: Path, metadata_file: Path) -> str:
    """Extract contract name from .sol file or metadata"""
    # Try metadata first
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                contract_name = metadata.get('contract_name')
                if contract_name:
                    return contract_name
        except:
            pass
    
    # Fall back to filename
    return sol_file.stem


def process_contract_directory(contract_dir: Path, skip_auto_fix: bool = True):
    """Process a single contract directory"""
    stage3_report = contract_dir / "stage3_report.json"
    
    # Skip if already processed
    if stage3_report.exists():
        print(f"⏭️  Skipping {contract_dir.name} (already has stage3_report.json)")
        return True
    
    # Find .sol file
    sol_file = find_sol_file(contract_dir)
    if not sol_file:
        print(f"⚠️  Skipping {contract_dir.name} (no .sol file found)")
        return False
    
    # Read Solidity code
    try:
        with open(sol_file, 'r', encoding='utf-8') as f:
            solidity_code = f.read()
    except Exception as e:
        print(f"❌ Error reading {sol_file}: {e}")
        return False
    
    # Get contract name
    metadata_file = contract_dir / "metadata.json"
    contract_name = get_contract_name(sol_file, metadata_file)
    
    # Load metadata if available
    stage2_metadata = None
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                stage2_metadata = json.load(f)
        except:
            pass
    
    print(f"\n{'='*80}")
    print(f"Processing: {contract_dir.name}")
    print(f"Contract: {contract_name}")
    print(f"{'='*80}")
    
    try:
        # Run Stage 3
        result = run_stage3(
            solidity_code=solidity_code,
            contract_name=contract_name,
            stage2_metadata=stage2_metadata,
            max_iterations=2,
            tools=["slither", "mythril", "semgrep", "solhint"],
            skip_auto_fix=skip_auto_fix
        )
        
        # Save stage3_report.json
        with open(stage3_report, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"✅ Saved stage3_report.json")
        print(f"   Issues found: {len(result.initial_analysis.issues)}")
        if result.final_analysis:
            print(f"   Final issues: {len(result.final_analysis.issues)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {contract_dir.name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run Stage 3 on all existing contracts in pipeline_outputs"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="pipeline_outputs",
        help="Directory containing pipeline output directories"
    )
    parser.add_argument(
        "--skip-auto-fix",
        action="store_true",
        help="Skip auto-fix, only run analysis (faster)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of contracts to process (for testing)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    
    # Fallback: check parent directory
    if not input_path.exists() and args.input_dir == "pipeline_outputs":
        if (Path("..") / "pipeline_outputs").exists():
            input_path = Path("..") / "pipeline_outputs"
            print(f"ℹ️  Found pipeline_outputs in parent directory: {input_path}")
    
    if not input_path.exists():
        print(f"❌ Input directory not found: {input_path}")
        return
    
    print("="*80)
    print("STAGE 3 BATCH PROCESSOR")
    print("="*80)
    print(f"Input directory: {input_path}")
    print(f"Mode: {'Analysis only' if args.skip_auto_fix else 'Analysis + Auto-fix'}")
    print("="*80)
    
    # Find all contract directories
    contract_dirs = [d for d in input_path.iterdir() if d.is_dir()]
    
    if args.limit:
        contract_dirs = contract_dirs[:args.limit]
        print(f"\n⚠️  Processing limited to {args.limit} contracts")
    
    print(f"\n📂 Found {len(contract_dirs)} contract directories")
    
    # Process each directory
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, contract_dir in enumerate(contract_dirs, 1):
        print(f"\n[{i}/{len(contract_dirs)}] {contract_dir.name}")
        
        if (contract_dir / "stage3_report.json").exists():
            skip_count += 1
            continue
        
        if process_contract_directory(contract_dir, skip_auto_fix=args.skip_auto_fix):
            success_count += 1
        else:
            error_count += 1
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Successfully processed: {success_count}")
    print(f"⏭️  Already processed (skipped): {skip_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(contract_dirs)}")
    print("="*80)
    
    if success_count > 0:
        print(f"\n✅ Stage 3 reports generated! You can now run:")
        print(f"   python ICBC_Results_Work/generate_icbc_results.py")


if __name__ == "__main__":
    main()

