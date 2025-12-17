# solidity_code_generator/code_generator.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from .repair import strip_markdown_fences, ensure_headers, repair_with_model_if_needed
from .constructor_resolver import ConstructorResolver
from .validator import validate_generated_code
from .semantic_validator import validate_semantics
from .logic_repair import repair_semantic_issues

load_dotenv()
_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
if not _API_KEY:
    raise RuntimeError("OpenAI API key not found in environment")

_client = OpenAI(api_key=_API_KEY)

def generate_solidity_code(
    system_prompt: str, 
    user_prompt: str, 
    json_spec: dict, 
    debug: bool = False,
    max_repair_attempts: int = 3
) -> str:
    """
    Generate Solidity code with validation and repair loop
    Now includes semantic validation for logic issues
    """
    if debug:
        print("\n" + "="*80)
        print("CODE GENERATION START")
        print("="*80)
    
    # Initial generation
    if debug:
        print("\n[1] Calling GPT-4o for initial code generation...")
    
    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    
    solidity_code = response.choices[0].message.content or ""
    
    if debug:
        print(f"[1] Generated {len(solidity_code)} characters")
    
    # Clean up markdown fences and ensure headers
    solidity_code = strip_markdown_fences(solidity_code)
    solidity_code = ensure_headers(solidity_code)
    
    # Validation and repair loop
    for attempt in range(max_repair_attempts):
        if debug:
            print(f"\n[{attempt + 2}] Validation attempt {attempt + 1}/{max_repair_attempts}")
        
        # Syntax validation
        syntax_result = validate_generated_code(solidity_code, debug=debug)
        
        # Semantic validation (logic issues)
        semantic_result = validate_semantics(solidity_code, json_spec, debug=debug)
        
        if debug:
            print(f"[{attempt + 2}] Syntax: {syntax_result['error_count']} errors")
            print(f"[{attempt + 2}] Semantic: {semantic_result['error_count']} errors")
            
            if syntax_result['errors']:
                print("Syntax errors:")
                for err in syntax_result['errors'][:3]:
                    print(f"  - {err}")
            
            if semantic_result['errors']:
                print("Semantic/Logic errors:")
                for err in semantic_result['errors'][:3]:
                    print(f"  - {err}")
        
        # Check if both validations pass
        both_valid = syntax_result['is_valid'] and semantic_result['is_valid']
        
        # If valid or last attempt, break
        if both_valid or attempt == max_repair_attempts - 1:
            if debug:
                if both_valid:
                    print(f"[{attempt + 2}] ✓ All validations passed!")
                else:
                    print(f"[{attempt + 2}] Max attempts reached, proceeding with current code")
            break
        
        # Priority 1: Fix semantic/logic issues first
        if semantic_result['errors']:
            if debug:
                print(f"[{attempt + 2}] Fixing semantic/logic issues...")
            
            solidity_code = repair_semantic_issues(
                _client, 
                solidity_code, 
                semantic_result['errors'],
                json_spec,
                debug=debug
            )
            
            # Re-validate after semantic repair
            semantic_result = validate_semantics(solidity_code, json_spec, debug=debug)
            if semantic_result['is_valid']:
                if debug:
                    print(f"[{attempt + 2}] ✓ Semantic issues resolved!")
                # Continue to check syntax
        
        # Priority 2: Fix syntax/constructor issues
        if not syntax_result['is_valid']:
            if debug:
                print(f"[{attempt + 2}] Applying constructor resolver...")
            
            resolver = ConstructorResolver(debug=debug)
            solidity_code = resolver.process(solidity_code, json_spec)
            
            # Re-validate after constructor fix
            syntax_result = validate_generated_code(solidity_code, debug=debug)
            if syntax_result['is_valid']:
                if debug:
                    print(f"[{attempt + 2}] ✓ Constructor resolver fixed the issues!")
                continue
            
            # If still issues, use model repair
            if debug:
                print(f"[{attempt + 2}] Using model repair for remaining syntax issues...")
            solidity_code = repair_with_model_if_needed(_client, solidity_code)
    
    # Final validation report
    final_syntax = validate_generated_code(solidity_code, debug=debug)
    final_semantic = validate_semantics(solidity_code, json_spec, debug=debug)
    
    if debug:
        print("\n" + "="*80)
        print("CODE GENERATION COMPLETE")
        print("="*80)
        
        syntax_status = '✓ VALID' if final_syntax['is_valid'] else '⚠ HAS ISSUES'
        semantic_status = '✓ VALID' if final_semantic['is_valid'] else '⚠ HAS ISSUES'
        
        print(f"Syntax Status: {syntax_status}")
        print(f"  Errors: {final_syntax['error_count']}")
        print(f"  Warnings: {final_syntax['warning_count']}")
        
        print(f"\nSemantic Status: {semantic_status}")
        print(f"  Errors: {final_semantic['error_count']}")
        print(f"  Warnings: {final_semantic['warning_count']}")
        
        if final_semantic['errors']:
            print("\nRemaining semantic issues:")
            for err in final_semantic['errors'][:5]:
                print(f"  - {err}")
        
        if final_semantic['warnings']:
            print("\nSemantic warnings (first 5):")
            for warn in final_semantic['warnings'][:5]:
                print(f"  - {warn}")
        
        print("="*80 + "\n")
    
    return solidity_code