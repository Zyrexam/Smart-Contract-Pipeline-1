import argparse
import csv
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_severity(sev):
    """Normalize severity to uppercase string"""
    if not sev:
        return "INFO"
    if isinstance(sev, str):
        return sev.upper()
    return str(sev).upper()


def count_by_severity(issues):
    """Count issues by severity from issues array"""
    counts = defaultdict(int)
    for issue in issues:
        sev = normalize_severity(issue.get("severity"))
        counts[sev] += 1
    counts["TOTAL"] = sum(counts.values())
    return counts


def count_critical_high(issues):
    """Count Critical and High severity issues"""
    count = 0
    for issue in issues:
        sev = normalize_severity(issue.get("severity"))
        if sev in ["CRITICAL", "HIGH"]:
            count += 1
    return count


def issue_signature(issue):
    """Create a unique signature for an issue to detect duplicates"""
    return (
        issue.get("tool"),
        issue.get("title"),
        issue.get("contract"),
        issue.get("function"),
        issue.get("line")
    )


# ============================================================================
# EXPORT FUNCTIONS (Paper-Ready Formats)
# ============================================================================

def save_table_csv(path: Path, headers: List[str], rows: List[List]):
    """Save table as CSV for Excel/Google Docs"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)




class ResultsAggregator:
    """Aggregates results from multiple pipeline runs"""
    
    def __init__(self):
        self.contracts: List[Dict] = []
        self.issues_by_tool: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.issues_by_severity: Dict[str, int] = defaultdict(int)
        self.fix_results: List[Dict] = []
        
    def load_contract_result(self, contract_dir: Path):
        """Load results from a single contract run"""
        stage3_report = contract_dir / "stage3_report.json"
        metadata_file = contract_dir / "metadata.json"
        
        if not stage3_report.exists():
            return None
        
        try:
            with open(stage3_report, 'r') as f:
                stage3_data = json.load(f)
            
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Validate that we have initial_analysis
            if "initial_analysis" not in stage3_data:
                print(f"⚠️  Warning: {contract_dir.name} missing initial_analysis")
                return None
            
            initial_analysis = stage3_data.get("initial_analysis", {})
            issues = initial_analysis.get("issues", [])
            tools_used = initial_analysis.get("tools_used", [])
            
            # Diagnostic: Check if tools ran but found no issues
            if issues:
                # Count issues by tool
                issues_by_tool = {}
                for issue in issues:
                    tool = issue.get("tool", "unknown")
                    issues_by_tool[tool] = issues_by_tool.get(tool, 0) + 1
                
                # Check if expected tools ran but found nothing
                expected_tools = ["slither", "mythril", "semgrep", "solhint"]
                for tool in expected_tools:
                    if tool in tools_used and tool not in issues_by_tool:
                        # Tool ran but found no issues - this is OK, but worth noting
                        pass
            
            return {
                "contract_name": initial_analysis.get("contract_name", "Unknown"),
                "category": metadata.get("category", "Unknown"),
                "stage3": stage3_data,
                "metadata": metadata
            }
        except Exception as e:
            print(f"⚠️  Error loading {contract_dir}: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def aggregate_vulnerability_detection(self):
        """Generate Table 2: Vulnerability Detection by Tool"""
        print("\n" + "="*80)
        print("TABLE 2: VULNERABILITY DETECTION BY TOOL")
        print("="*80)
        
        # Reset counters
        tool_counts = defaultdict(lambda: defaultdict(int))
        combined_issues = defaultdict(int)
        tool_total_issues = defaultdict(int)  # Track total per tool
        
        for contract in self.contracts:
            initial = contract["stage3"].get("initial_analysis", {})
            issues = initial.get("issues", [])
            
            # Count by tool
            for issue in issues:
                tool = issue.get("tool", "unknown")
                severity = normalize_severity(issue.get("severity"))
                tool_counts[tool][severity] += 1
                tool_total_issues[tool] += 1
                combined_issues[severity] += 1
        
        # Debug: Print what we found
        if not tool_counts:
            print("\n⚠️  WARNING: No issues found in any contracts!")
            print("   This might indicate:")
            print("   - Tools are not detecting issues correctly")
            print("   - Parsing is failing")
            print("   - Contracts are genuinely secure (unlikely)")
        else:
            print(f"\n📊 Found issues from {len(tool_counts)} tools:")
            for tool, counts in tool_counts.items():
                total = sum(counts.values())
                print(f"   {tool}: {total} issues ({dict(counts)})")
        
        # Print table
        print(f"\n{'Tool':<12} | {'Critical':<8} | {'High':<8} | {'Medium':<8} | {'Low':<8} | {'Info':<8} | {'Total':<8}")
        print("-" * 80)
        
        tools = ["slither", "mythril", "semgrep", "solhint"]
        totals = defaultdict(int)
        
        for tool in tools:
            counts = tool_counts[tool]
            # All severities are already normalized to uppercase
            critical = counts.get("CRITICAL", 0)
            high = counts.get("HIGH", 0)
            medium = counts.get("MEDIUM", 0)
            low = counts.get("LOW", 0)
            info = counts.get("INFO", 0)
            total = critical + high + medium + low + info
            
            print(f"{tool.capitalize():<12} | {critical:<8} | {high:<8} | {medium:<8} | {low:<8} | {info:<8} | {total:<8}")
            
            totals["CRITICAL"] += critical
            totals["HIGH"] += high
            totals["MEDIUM"] += medium
            totals["LOW"] += low
            totals["INFO"] += info
        
        # Combined row (deduplicated - approximate)
        print("-" * 80)
        combined_total = sum(totals.values())
        print(f"{'Combined':<12} | {totals['CRITICAL']:<8} | {totals['HIGH']:<8} | {totals['MEDIUM']:<8} | {totals['LOW']:<8} | {totals['INFO']:<8} | {combined_total:<8}")
        
        result = {
            "tool_counts": dict(tool_counts),
            "combined": dict(totals)
        }
        
        # Prepare data for export
        result["_csv_rows"] = []
        
        for tool in tools:
            counts = tool_counts[tool]
            critical = counts.get("CRITICAL", 0)
            high = counts.get("HIGH", 0)
            medium = counts.get("MEDIUM", 0)
            low = counts.get("LOW", 0)
            info = counts.get("INFO", 0)
            total = critical + high + medium + low + info
            
            result["_csv_rows"].append([tool.capitalize(), critical, high, medium, low, info, total])
        
        # Combined row
        result["_csv_rows"].append([
            "Combined",
            totals["CRITICAL"],
            totals["HIGH"],
            totals["MEDIUM"],
            totals["LOW"],
            totals["INFO"],
            sum(totals.values())
        ])

        return result
    
    def aggregate_repair_effectiveness(self):
        """Generate Table 3: Repair Effectiveness"""
        print("\n" + "="*80)
        print("TABLE 3: REPAIR EFFECTIVENESS (BEFORE vs AFTER)")
        print("="*80)
        
        before = defaultdict(int)
        after = defaultdict(int)
        total_contracts = 0
        
        for contract in self.contracts:
            initial = contract["stage3"].get("initial_analysis", {})
            final = contract["stage3"].get("final_analysis")
            
            if not final:
                continue
            
            total_contracts += 1
            
            # Count from issues array (CORRECT way)
            before_counts = count_by_severity(initial.get("issues", []))
            after_counts = count_by_severity(final.get("issues", []))
            
            # Aggregate
            before["CRITICAL"] += before_counts.get("CRITICAL", 0)
            before["HIGH"] += before_counts.get("HIGH", 0)
            before["MEDIUM"] += before_counts.get("MEDIUM", 0)
            before["LOW"] += before_counts.get("LOW", 0)
            before["INFO"] += before_counts.get("INFO", 0)
            before["TOTAL"] += before_counts.get("TOTAL", 0)
            
            after["CRITICAL"] += after_counts.get("CRITICAL", 0)
            after["HIGH"] += after_counts.get("HIGH", 0)
            after["MEDIUM"] += after_counts.get("MEDIUM", 0)
            after["LOW"] += after_counts.get("LOW", 0)
            after["INFO"] += after_counts.get("INFO", 0)
            after["TOTAL"] += after_counts.get("TOTAL", 0)
        
        if total_contracts == 0:
            print("⚠️  No contracts with fix results found")
            return None
        
        # Calculate resolved
        print(f"\n{'Metric':<15} | {'Before':<10} | {'After':<10} | {'Resolved':<15} | {'%':<8}")
        print("-" * 80)
        
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "TOTAL"]
        
        for severity in severities:
            b = before[severity]
            a = after[severity]
            resolved = b - a
            pct = (resolved / b * 100) if b > 0 else 0
            
            print(f"{severity.capitalize():<15} | {b:<10} | {a:<10} | {resolved:<15} | {pct:.1f}%")
        
        print(f"\nTotal contracts analyzed: {total_contracts}")
        
        result = {
            "before": dict(before),
            "after": dict(after),
            "contracts": total_contracts
        }
        
        # Prepare data for export
        result["_csv_rows"] = []        
        
        for severity in severities:
            b = before[severity]
            a = after[severity]
            resolved = b - a
            pct = (resolved / b * 100) if b > 0 else 0
            
            result["_csv_rows"].append([severity.capitalize(), b, a, resolved, f"{pct:.1f}%"])
        
        return result
    
    def aggregate_convergence(self):
        """Generate convergence data for Figure 1"""
        print("\n" + "="*80)
        print("CONVERGENCE DATA (For Figure 1)")
        print("="*80)
        
        convergence_data = []
        
        for contract in self.contracts:
            fixes = contract["stage3"].get("fixes_applied", [])
            initial = contract["stage3"].get("initial_analysis", {})
            
            # Iteration 0 (initial) - count from issues array
            initial_issues = initial.get("issues", [])
            initial_crit_high = count_critical_high(initial_issues)
            convergence_data.append({
                "contract": contract["contract_name"],
                "iteration": 0,
                "critical_high": initial_crit_high
            })
            
            # Subsequent iterations
            # fixes_applied contains: {"iteration": N, "issues_before": X, "issues_after": Y}
            for fix in fixes:
                iteration = fix.get("iteration", 0)
                issues_after = fix.get("issues_after")
                
                if issues_after is not None:
                    # Use the value from fixes_applied
                    convergence_data.append({
                        "contract": contract["contract_name"],
                        "iteration": iteration,
                        "critical_high": issues_after
                    })
            
            # Add final state if we have final_analysis
            final = contract["stage3"].get("final_analysis")
            if final:
                final_issues = final.get("issues", [])
                final_crit_high = count_critical_high(final_issues)
                # Calculate final iteration as max existing iteration + 1 (ensures monotonic increase)
                existing_iterations = [d["iteration"] for d in convergence_data 
                                      if d["contract"] == contract["contract_name"]]
                final_iteration = (max(existing_iterations) + 1) if existing_iterations else 0
                
                convergence_data.append({
                    "contract": contract["contract_name"],
                    "iteration": final_iteration,
                    "critical_high": final_crit_high
                })
        
        # Aggregate by iteration
        print("\nAverage Critical+High Issues by Iteration:")
        print(f"{'Iteration':<12} | {'Avg Issues':<15} | {'Contracts':<10}")
        print("-" * 50)
        
        by_iteration = defaultdict(list)
        for data in convergence_data:
            by_iteration[data["iteration"]].append(data["critical_high"])
        
        for iteration in sorted(by_iteration.keys()):
            issues = by_iteration[iteration]
            avg = sum(issues) / len(issues) if issues else 0
            print(f"{iteration:<12} | {avg:<15.2f} | {len(issues):<10}")
        
        return convergence_data
    
    def aggregate_metadata_impact(self, with_metadata_dir: Path, without_metadata_dir: Path):
        """Generate Table 4: Metadata Ablation Study"""
        print("\n" + "="*80)
        print("TABLE 4: METADATA ABLATION STUDY")
        print("="*80)
        print("⚠️  This requires running Stage 3 twice (with/without metadata)")
        print("    Compare results from two different directories")
        
        # Load with metadata results
        with_meta = []
        for contract_dir in with_metadata_dir.iterdir():
            if contract_dir.is_dir():
                result = self.load_contract_result(contract_dir)
                if result:
                    with_meta.append(result)
        
        # Load without metadata results
        without_meta = []
        for contract_dir in without_metadata_dir.iterdir():
            if contract_dir.is_dir():
                result = self.load_contract_result(contract_dir)
                if result:
                    without_meta.append(result)
        
        if not with_meta or not without_meta:
            print("⚠️  Need both 'with_metadata' and 'without_metadata' result directories")
            return None
        
        # Compare fix success rates
        print("\nComparison (requires manual analysis of fix quality):")
        print("Run Stage 3 on same contracts with and without metadata")
        print("Compare fix quality, over-restrictive fixes, logic-breaking changes")
        
        return {
            "with_metadata": len(with_meta),
            "without_metadata": len(without_meta)
        }
    
    def aggregate_tool_complementarity(self):
        """Generate Table 5: Tool Complementarity"""
        print("\n" + "="*80)
        print("TABLE 5: TOOL COMPLEMENTARITY (Unique vs Shared Issues)")
        print("="*80)
        print("⚠️  Requires deduplication logic (see ICBC_RESULTS_STRATEGY.md)")
        
        # Simple approximation: count issues by tool
        tool_issue_counts = defaultdict(int)
        all_issues = []
        
        for contract in self.contracts:
            initial = contract["stage3"].get("initial_analysis", {})
            issues = initial.get("issues", [])
            
            for issue in issues:
                tool = issue.get("tool", "unknown")
                tool_issue_counts[tool] += 1
                all_issues.append(issue)
        
        print("\nIssue counts by tool (approximate):")
        print(f"{'Tool':<12} | {'Total Issues':<15}")
        print("-" * 30)
        
        for tool, count in sorted(tool_issue_counts.items()):
            print(f"{tool.capitalize():<12} | {count:<15}")
        
        print("\n⚠️  For accurate unique/shared counts, implement deduplication")
        print("    (see Change 2 in ICBC_RESULTS_STRATEGY.md)")
        
        return tool_issue_counts
    
    def aggregate_fix_stability(self):
        """Generate Table 6: Fix Stability Metrics"""
        print("\n" + "="*80)
        print("TABLE 6: FIX STABILITY METRICS")
        print("="*80)
        
        iterations = []
        new_issues_count = 0
        total_contracts = 0
        
        for contract in self.contracts:
            stage3 = contract["stage3"]
            initial = stage3.get("initial_analysis", {})
            final = stage3.get("final_analysis")
            
            if not final:
                continue
            
            total_contracts += 1
            iterations.append(stage3.get("iterations", 0))
            
            # Check for new issues using issue signatures (more robust)
            initial_types = {issue_signature(i) for i in initial.get("issues", [])}
            final_types = {issue_signature(i) for i in final.get("issues", [])}
            new_types = final_types - initial_types
            if new_types:
                new_issues_count += len(new_types)
        
        if total_contracts == 0:
            print("⚠️  No contracts with fix results found")
            return None
        
        avg_iterations = sum(iterations) / len(iterations) if iterations else 0
        
        print(f"\n{'Metric':<30} | {'Value':<10}")
        print("-" * 45)
        print(f"{'Average Iterations':<30} | {avg_iterations:<10.2f}")
        print(f"{'New Issues Introduced':<30} | {new_issues_count:<10}")
        print(f"{'ABI Changes':<30} | {'N/A':<10} (requires solc)")
        print(f"{'ERC Compliance Broken':<30} | {'N/A':<10} (requires manual check)")
        print(f"\nTotal contracts: {total_contracts}")
        
        return {
            "avg_iterations": avg_iterations,
            "new_issues": new_issues_count,
            "contracts": total_contracts
        }
    
    def aggregate_performance(self):
        """Generate Table 7: Performance Breakdown"""
        print("\n" + "="*80)
        print("TABLE 7: PERFORMANCE BREAKDOWN")
        print("="*80)
        print("⚠️  Timing data not currently tracked")
        print("    Add timing instrumentation (see ICBC_RESULTS_STRATEGY.md)")
        
        print("\nTo add timing:")
        print("1. Add time.time() at start/end of each stage")
        print("2. Store in result objects")
        print("3. Re-run pipeline to collect timing data")
        
        return None
    
    def generate_comparison_table(self):
        """Generate Table 8: Comparison with Prior Work"""
        print("\n" + "="*80)
        print("TABLE 8: COMPARISON WITH PRIOR WORK")
        print("="*80)
        
        print("\n{'Feature':<30} | {'SmartBugs':<12} | {'Oyente':<12} | {'Ours':<12}")
        print("-" * 70)
        
        features = [
            ("Multi-tool analysis", "✓", "❌", "✓"),
            ("Automated repair", "❌", "❌", "✓"),
            ("Metadata-aware fixing", "❌", "❌", "✓"),
            ("Windows support", "⚠️", "❌", "✓"),
            ("End-to-end NL→Secure SC", "❌", "❌", "✓"),
        ]
        
        for feature, smartbugs, oyente, ours in features:
            print(f"{feature:<30} | {smartbugs:<12} | {oyente:<12} | {ours:<12}")
        
        return features
    
    def generate_dataset_summary(self):
        """Generate Table 1: Dataset Summary"""
        print("\n" + "="*80)
        print("TABLE 1: DATASET SUMMARY")
        print("="*80)
        
        # Group by category
        by_category = defaultdict(list)
        
        for contract in self.contracts:
            category = contract.get("category", "Unknown")
            by_category[category].append(contract)
        
        print(f"\n{'Category':<20} | {'Contracts':<12} | {'Avg LOC':<10}")
        print("-" * 45)
        
        total_contracts = 0
        csv_rows = []
        for category, contracts in sorted(by_category.items()):
            count = len(contracts)
            total_contracts += count
            # LOC estimation (if available in metadata)
            locs = []
            for c in contracts:
                meta = c.get("metadata", {})
                if "loc" in meta:
                    locs.append(meta["loc"])
            
            avg_loc = int(sum(locs) / len(locs)) if locs else "N/A"
            print(f"{category:<20} | {count:<12} | {avg_loc:<10}")
            csv_rows.append([category, count, avg_loc])
        
        print("-" * 45)
        print(f"{'Total':<20} | {total_contracts:<12} | {'-':<10}")
        csv_rows.append(["Total", total_contracts, "-"])
        
        return {
            "by_category": dict(by_category),
            "total": total_contracts,
            "_csv_rows": csv_rows
        }


def main():
    parser = argparse.ArgumentParser(description="Generate ICBC paper results")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="pipeline_outputs",
        help="Directory containing pipeline output directories"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="icbc_results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--with-metadata-dir",
        type=str,
        help="Directory with results using metadata (for ablation study)"
    )
    parser.add_argument(
        "--without-metadata-dir",
        type=str,
        help="Directory with results without metadata (for ablation study)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    
    # Fallback: check legacy/parent location if default is used but not found
    if not input_path.exists() and args.input_dir == "pipeline_outputs":
        if (Path("..") / "pipeline_outputs").exists():
            input_path = Path("..") / "pipeline_outputs"
            print(f"ℹ️  Found pipeline_outputs in parent directory: {input_path}")

    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)
    
    if not input_path.exists():
        print(f"❌ Input directory not found: {input_path}")
        return
    
    print("="*80)
    print("ICBC RESULTS GENERATOR")
    print("="*80)
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    aggregator = ResultsAggregator()
    
    # Load all contract results
    print("\n📂 Loading contract results...")
    contract_dirs = [d for d in input_path.iterdir() if d.is_dir()]
    
    loaded_count = 0
    skipped_count = 0
    
    for contract_dir in contract_dirs:
        result = aggregator.load_contract_result(contract_dir)
        if result:
            aggregator.contracts.append(result)
            loaded_count += 1
        else:
            skipped_count += 1
    
    print(f"✅ Loaded {loaded_count} contract results")
    if skipped_count > 0:
        print(f"⚠️  Skipped {skipped_count} directories (missing stage3_report.json or invalid)")
    
    if len(aggregator.contracts) == 0:
        print("⚠️  No contract results found. Make sure Stage 3 has been run.")
        print("    Run: python -m stage_3.test_production")
        return
    
    # Diagnostic: Check tool usage across all contracts
    print("\n📊 Tool Usage Diagnostics:")
    tool_usage = defaultdict(int)
    tool_issue_counts = defaultdict(int)
    
    for contract in aggregator.contracts:
        initial = contract["stage3"].get("initial_analysis", {})
        tools_used = initial.get("tools_used", [])
        issues = initial.get("issues", [])
        
        for tool in tools_used:
            tool_usage[tool] += 1
        
        for issue in issues:
            tool = issue.get("tool", "unknown")
            tool_issue_counts[tool] += 1
    
    print(f"   Tools used across contracts:")
    for tool in ["slither", "mythril", "semgrep", "solhint"]:
        usage = tool_usage.get(tool, 0)
        issues = tool_issue_counts.get(tool, 0)
        status = "✓" if usage > 0 else "✗"
        print(f"     {status} {tool}: used in {usage}/{len(aggregator.contracts)} contracts, found {issues} total issues")
    
    # Generate all tables
    print("\n" + "="*80)
    print("GENERATING RESULTS TABLES")
    print("="*80)
    
    results = {}
    
    # Table 1: Dataset Summary
    results["dataset"] = aggregator.generate_dataset_summary()
    
    # Table 2: Vulnerability Detection
    results["detection"] = aggregator.aggregate_vulnerability_detection()
    
    # Table 3: Repair Effectiveness
    results["repair"] = aggregator.aggregate_repair_effectiveness()
    
    # Convergence data
    results["convergence"] = aggregator.aggregate_convergence()
    
    # Table 4: Metadata Ablation (if directories provided)
    if args.with_metadata_dir and args.without_metadata_dir:
        results["metadata_ablation"] = aggregator.aggregate_metadata_impact(
            Path(args.with_metadata_dir),
            Path(args.without_metadata_dir)
        )
    
    # Table 5: Tool Complementarity
    results["complementarity"] = aggregator.aggregate_tool_complementarity()
    
    # Table 6: Fix Stability
    results["stability"] = aggregator.aggregate_fix_stability()
    
    # Table 7: Performance
    aggregator.aggregate_performance()
    
    # Table 8: Comparison
    results["comparison"] = aggregator.generate_comparison_table()
    
    # Save results to JSON
    results_file = output_path / "results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        # Remove internal export data before saving JSON
        clean_results = {}
        for key, value in results.items():
            if isinstance(value, dict) and key in ["detection", "repair", "dataset"]:
                clean_value = {k: v for k, v in value.items() if not k.startswith("_")}
                clean_results[key] = clean_value
            else:
                clean_results[key] = value
        json.dump(clean_results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to: {results_file}")
    
    # ========================================================================
    # EXPORT PAPER-READY FORMATS
    # ========================================================================
    print("\n" + "="*80)
    print("EXPORTING PAPER-READY FORMATS")
    print("="*80)
    
    # Table 2: Vulnerability Detection
    if results.get("detection") and results["detection"].get("_csv_rows"):
        csv_path = output_path / "table2_vulnerability_detection.csv"
        save_table_csv(
            csv_path,
            ["Tool", "Critical", "High", "Medium", "Low", "Info", "Total"],
            results["detection"]["_csv_rows"]
        )
        print(f"✅ CSV: {csv_path}")
    
    # Table 3: Repair Effectiveness
    if results.get("repair") and results["repair"].get("_csv_rows"):
        csv_path = output_path / "table3_repair_effectiveness.csv"
        save_table_csv(
            csv_path,
            ["Metric", "Before", "After", "Resolved", "%"],
            results["repair"]["_csv_rows"]
        )
        print(f"✅ CSV: {csv_path}")
    
    # Table 1: Dataset Summary
    if results.get("dataset") and results["dataset"].get("_csv_rows"):
        dataset = results["dataset"]
        csv_path = output_path / "table1_dataset_summary.csv"
        save_table_csv(
            csv_path,
            ["Category", "Contracts", "Avg LOC"],
            dataset["_csv_rows"]
        )
        print(f"✅ CSV: {csv_path}")
    
    # Convergence Data (Figure 1)
    if results.get("convergence"):
        convergence_file = output_path / "figure1_convergence.json"
        with open(convergence_file, 'w', encoding='utf-8') as f:
            json.dump(results["convergence"], f, indent=2, default=str)
        print(f"✅ Convergence JSON: {convergence_file}")
        print("   (Use this to plot Figure 1 with matplotlib or pgfplots)")
        
        # Also export as CSV for quick plotting
        csv_path = output_path / "figure1_convergence.csv"
        save_table_csv(
            csv_path,
            ["Contract", "Iteration", "Critical+High"],
            [[d["contract"], d["iteration"], d["critical_high"]] for d in results["convergence"]]
        )
        print(f"✅ Convergence CSV: {csv_path}")
    
    print("\n" + "="*80)
    print("📋 PAPER-READY FILES GENERATED")
    print("="*80)
    print("\nYou can now:")
    print("  1. Import CSV files into Excel/Google Docs for formatting")
    print("  2. Use convergence.json to plot Figure 1")
    print("  3. Reference results.json for programmatic access")
    print("\nAll files are in:", output_path)


if __name__ == "__main__":
    main()

