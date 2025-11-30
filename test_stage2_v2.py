"""
Enhanced Full Pipeline Test: Stage 1 + Enhanced Stage 2
Tests category-aware code generation with proper standards compliance
"""

import json
import os
from intent_extraction import extract_intent
from solidity_generator_v2 import generate_solidity_code



# Example 1: ERC20 Token (Default)
USER_INPUT = """
Create a token contract called MyToken with the following features:
- Token name "MyToken" and symbol "MTK"
- Total supply of 1 million tokens
- Owner can mint new tokens
- Users can transfer tokens to each other
- Emit events when tokens are minted
"""





def run_enhanced_pipeline(user_input: str):
    """
    Run the enhanced pipeline with category-aware code generation.
    
    Args:
        user_input: Natural language description of the smart contract
    """
    
    print("=" * 80)
    print("ENHANCED SMART CONTRACT GENERATOR")
    print("Category-Aware Code Generation ")
    print("=" * 80)
    print()
    
    # Display user input
    print("📝 User Input:")
    print("-" * 80)
    print(user_input.strip())
    print("-" * 80)
    print()
    
    # ==================== STAGE 1: Intent Extraction ====================
    print("🔹 STAGE 1: Extracting Intent from Natural Language")
    print("-" * 80)
    
    try:
        json_spec = extract_intent(user_input)
        
        print("✅ Stage 1 Complete - Intent Extracted Successfully!")
        print()
        print("JSON Specification:")
        print(json.dumps(json_spec, indent=2))
        print()
        
    except Exception as e:
        print(f"❌ Stage 1 Failed: {e}")
        return
    
    # ==================== STAGE 2: Enhanced Code Generation ====================
    print("🔹 STAGE 2: Category-Aware Solidity Code Generation")
    print("-" * 80)
    
    try:
        solidity_code, metadata = generate_solidity_code(json_spec)
        
        print("✅ Stage 2 Complete - Solidity Code Generated Successfully!")
        print()
        print("📊 Generation Metadata:")
        print(f"   • Category: {metadata['category']}")
        print(f"   • Standard: {metadata['standard']}")
        print(f"   • Access Control: {metadata['access_control']}")
        print(f"   • Imports: {len(metadata['imports_used'])} OpenZeppelin contracts")
        print(f"   • Inheritance: {', '.join(metadata['inheritance'])}")
        print()
        print("=" * 80)
        print("GENERATED SOLIDITY CONTRACT:")
        print("=" * 80)
        print(solidity_code)
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ Stage 2 Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ==================== Save Output Files ====================
    contract_name = json_spec.get('contract_name', 'GeneratedContract')
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Save JSON specification
    json_filename = "output/contract_spec.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(json_spec, f, indent=2)
    
    # Save Solidity contract
    sol_filename = f"output/{contract_name}.sol"
    with open(sol_filename, 'w', encoding='utf-8') as f:
        f.write(solidity_code)
    
    # Save generation metadata
    metadata_filename = "output/generation_metadata.json"
    with open(metadata_filename, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print("💾 Files Saved:")
    print(f"   📄 {json_filename}")
    print(f"      └─ JSON specification from Stage 1")
    print(f"   📄 {sol_filename}")
    print(f"      └─ Generated Solidity contract")
    print(f"   📄 {metadata_filename}")
    print(f"      └─ Generation metadata (category, standard, etc.)")
    print()
    
    # ==================== Summary ====================
    print("=" * 80)
    print("✅ ENHANCED PIPELINE COMPLETE!")
    print("=" * 80)
    print()
    


def main():
    """Main entry point"""
    try:
        run_enhanced_pipeline(USER_INPUT)
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()