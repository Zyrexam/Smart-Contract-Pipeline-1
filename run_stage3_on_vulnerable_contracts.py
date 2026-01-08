import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from stage_3 import run_stage3


def extract_contract_name(solidity_code: str) -> str:
    match = re.search(r'contract\s+(\w+)', solidity_code)
    if match:
        return match.group(1)
    
    return "UnknownContract"


def extract_vulnerability_info(solidity_code: str, filename: str) -> Dict:
    info = {
        "category": "Vulnerable",
        "base_standard": "Custom",
        "vulnerability_type": "Unknown",
        "swc_id": None,
        "severity": "Unknown"
    }
    
    # Try to extract SWC ID
    swc_match = re.search(r'SWC-(\d+)', solidity_code)
    if swc_match:
        info["swc_id"] = f"SWC-{swc_match.group(1)}"
    
    # Try to extract vulnerability type from comments
    if "reentrancy" in solidity_code.lower() or "Reentrancy" in solidity_code:
        info["vulnerability_type"] = "Reentrancy"
        info["severity"] = "High"
    elif "access control" in solidity_code.lower() or "Access Control" in solidity_code:
        info["vulnerability_type"] = "Access Control"
        info["severity"] = "Critical"
    elif "tx.origin" in solidity_code.lower():
        info["vulnerability_type"] = "tx.origin Usage"
        info["severity"] = "Medium"
    elif "randomness" in solidity_code.lower() or "random" in solidity_code.lower():
        info["vulnerability_type"] = "Weak Randomness"
        info["severity"] = "Medium"
    
    # Map filename to known vulnerabilities
    filename_lower = filename.lower()
    if "reentrancy" in filename_lower:
        info["vulnerability_type"] = "Reentrancy"
        info["severity"] = "High"
    elif "unprotected" in filename_lower or "vault" in filename_lower:
        info["vulnerability_type"] = "Access Control"
        info["severity"] = "Critical"
    elif "phish" in filename_lower:
        info["vulnerability_type"] = "tx.origin Usage"
        info["severity"] = "Medium"
    elif "lottery" in filename_lower or "bad" in filename_lower:
        info["vulnerability_type"] = "Weak Randomness"
        info["severity"] = "Medium"
    
    return info


def process_vulnerable_contract(
    contract_path: Path,
    output_base: Path,
    max_iterations: int = 2,
    skip_auto_fix: bool = False
) -> Optional[Dict]:
    print(f"\n{'='*80}")
    print(f"Processing: {contract_path.name}")
    print('='*80)
    
    # Read contract code
    try:
        with open(contract_path, 'r', encoding='utf-8') as f:
            solidity_code = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None
    
    # Extract contract name
    contract_name = extract_contract_name(solidity_code)
    print(f"Contract name: {contract_name}")
    
    # Extract vulnerability info
    vuln_info = extract_vulnerability_info(solidity_code, contract_path.name)
    print(f"Vulnerability: {vuln_info['vulnerability_type']} ({vuln_info['severity']})")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = output_base / f"{timestamp}_{contract_name}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy original contract file
    output_contract_path = output_dir / f"{contract_name}.sol"
    with open(output_contract_path, 'w', encoding='utf-8') as f:
        f.write(solidity_code)
    
    # Run Stage 3
    print(f"\nRunning Stage 3...")
    try:
        result = run_stage3(
            solidity_code=solidity_code,
            contract_name=contract_name,
            stage2_metadata=None,  # No Stage 2 metadata for direct contracts
            max_iterations=max_iterations,
            tools=["slither", "mythril", "semgrep", "solhint"],
            skip_auto_fix=skip_auto_fix
        )
    except Exception as e:
        print(f"❌ Stage 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Save final code if fixes were applied
    if result.final_code and result.final_code != solidity_code:
        final_contract_path = output_dir / f"final_{contract_name}.sol"
        with open(final_contract_path, 'w', encoding='utf-8') as f:
            f.write(result.final_code)
        print(f"✅ Fixed code saved: {final_contract_path.name}")
    
    # Create metadata.json
    metadata = {
        "category": vuln_info["category"],
        "base_standard": vuln_info["base_standard"],
        "contract_name": contract_name,
        "source_file": str(contract_path),
        "vulnerability_type": vuln_info["vulnerability_type"],
        "swc_id": vuln_info["swc_id"],
        "expected_severity": vuln_info["severity"],
        "is_vulnerable": True,
        "source": "vulnerable_dataset"
    }
    
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    # Create stage3_report.json (convert Stage3Result to dict)
    stage3_report = result.to_dict()
    
    stage3_report_path = output_dir / "stage3_report.json"
    with open(stage3_report_path, 'w', encoding='utf-8') as f:
        json.dump(stage3_report, f, indent=2, default=str)
    
    # Print summary
    print(f"\n✅ Results saved to: {output_dir}")
    print(f"  • Initial issues: {len(result.initial_analysis.issues) if result.initial_analysis else 0}")
    print(f"  • Final issues: {len(result.final_analysis.issues) if result.final_analysis else 0}")
    print(f"  • Issues resolved: {result.issues_resolved}")
    print(f"  • Iterations: {result.iterations}")
    
    return {
        "contract_name": contract_name,
        "output_dir": output_dir,
        "result": result,
        "metadata": metadata
    }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run Stage 3 on vulnerable contracts from vulnerable_dataset"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="vulnerable_dataset",
        help="Directory containing vulnerable .sol files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="pipeline_outputs",
        help="Output directory (will create subdirectories for each contract)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum fix iterations"
    )
    parser.add_argument(
        "--skip-auto-fix",
        action="store_true",
        help="Only run analysis, skip auto-fix"
    )
    parser.add_argument(
        "--contract",
        type=str,
        help="Process only a specific contract file (optional)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    
    if not input_path.exists():
        print(f"❌ Input directory not found: {input_path}")
        return
    
    # Find all .sol files
    if args.contract:
        contract_files = [input_path / args.contract]
        if not contract_files[0].exists():
            print(f"❌ Contract file not found: {contract_files[0]}")
            return
    else:
        contract_files = list(input_path.glob("*.sol"))
    
    if not contract_files:
        print(f"⚠️  No .sol files found in {input_path}")
        return
    
    print("="*80)
    print("RUNNING STAGE 3 ON VULNERABLE CONTRACTS")
    print("="*80)
    print(f"Input directory: {input_path}")
    print(f"Output directory: {output_path}")
    print(f"Contracts found: {len(contract_files)}")
    print(f"Skip auto-fix: {args.skip_auto_fix}")
    print(f"Max iterations: {args.max_iterations}")
    
    # Process each contract
    results = []
    for contract_file in contract_files:
        result = process_vulnerable_contract(
            contract_file,
            output_path,
            max_iterations=args.max_iterations,
            skip_auto_fix=args.skip_auto_fix
        )
        if result:
            results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Contracts processed: {len(results)}/{len(contract_files)}")
    
    if results:
        total_initial = sum(len(r["result"].initial_analysis.issues) if r["result"].initial_analysis else 0 for r in results)
        total_final = sum(len(r["result"].final_analysis.issues) if r["result"].final_analysis else 0 for r in results)
        total_resolved = sum(r["result"].issues_resolved for r in results)
        
        print(f"Total initial issues: {total_initial}")
        print(f"Total final issues: {total_final}")
        print(f"Total issues resolved: {total_resolved}")
        print(f"\n✅ Results are saved in: {output_path}")
        print(f"   Run generate_icbc_results.py to include these in your ICBC results!")


if __name__ == "__main__":
    main()
