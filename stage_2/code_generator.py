# solidity_code_generator/code_generator.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from .repair import strip_markdown_fences, ensure_headers, repair_with_model_if_needed
from .constructor_resolver import ConstructorResolver
from .validator import validate_generated_code

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
        
        # Validate
        validation_result = validate_generated_code(solidity_code, debug=debug)
        
        if debug:
            print(f"[{attempt + 2}] Validation: {validation_result['error_count']} errors, {validation_result['warning_count']} warnings")
            if validation_result['errors']:
                print("Errors found:")
                for err in validation_result['errors'][:5]:  # Show first 5
                    print(f"  - {err}")
        
        # If valid or last attempt, break
        if validation_result['is_valid'] or attempt == max_repair_attempts - 1:
            if debug:
                if validation_result['is_valid']:
                    print(f"[{attempt + 2}] ✓ Validation passed!")
                else:
                    print(f"[{attempt + 2}] Max attempts reached, proceeding with current code")
            break
        
        # Apply constructor resolver
        if debug:
            print(f"[{attempt + 2}] Applying constructor resolver...")
        resolver = ConstructorResolver(debug=debug)
        solidity_code = resolver.process(solidity_code, json_spec)
        
        # Re-validate after constructor fix
        validation_result = validate_generated_code(solidity_code, debug=debug)
        if validation_result['is_valid']:
            if debug:
                print(f"[{attempt + 2}] ✓ Constructor resolver fixed the issues!")
            break
        
        # If still issues, use model repair
        if debug:
            print(f"[{attempt + 2}] Using model repair for remaining issues...")
        solidity_code = repair_with_model_if_needed(_client, solidity_code)
    
    # Final validation report
    final_validation = validate_generated_code(solidity_code, debug=debug)
    
    if debug:
        print("\n" + "="*80)
        print("CODE GENERATION COMPLETE")
        print("="*80)
        print(f"Final Status: {'✓ VALID' if final_validation['is_valid'] else '⚠ HAS ISSUES'}")
        print(f"Errors: {final_validation['error_count']}")
        print(f"Warnings: {final_validation['warning_count']}")
        
        if final_validation['warnings']:
            print("\nWarnings (first 5):")
            for warn in final_validation['warnings'][:5]:
                print(f"  - {warn}")
        print("="*80 + "\n")
    
    return solidity_code