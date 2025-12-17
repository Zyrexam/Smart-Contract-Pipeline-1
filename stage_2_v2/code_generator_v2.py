# solidity_code_generator/code_generator_v2.py
"""
Profile-Aware Code Generation

Applies fixes intelligently based on contract profile:
- Template contracts (ERC20, Governor) → Apply constructor fixes
- Custom contracts (elections, certificates) → Skip fixes
"""

import os
import sys
from typing import Tuple, List
from dotenv import load_dotenv
from openai import OpenAI

# Import from stage_2 (parent module)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stage_2.repair import strip_markdown_fences, ensure_headers, repair_with_model_if_needed
from stage_2.constructor_resolver import ConstructorResolver
from stage_2.validator import validate_generated_code
from stage_2.semantic_validator import validate_semantics
from stage_2.logic_repair import repair_semantic_issues
from .llm_utils import call_chat_completion, estimate_tokens, truncate_spec_for_prompt

load_dotenv()
_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
if not _API_KEY:
    raise RuntimeError("OpenAI API key not found in environment")

_client = OpenAI(api_key=_API_KEY)

# Token limits (conservative estimate)
MAX_PROMPT_TOKENS = 120000  # ~480k chars, leaving room for response


def generate_solidity_code(
    system_prompt: str,
    user_prompt: str,
    json_spec: dict,
    profile: 'ContractProfile',
    debug: bool = False,
    max_repair_attempts: int = 3
) -> Tuple[str, List]:
    """
    Generate Solidity code with profile-aware validation and repair.
    
    Returns:
        Tuple of (solidity_code, fixes_applied_list)
    """
    """
    Generate Solidity code with profile-aware validation and repair.
    
    Args:
        system_prompt: System instructions for LLM
        user_prompt: User request for LLM
        json_spec: JSON specification
        profile: Contract profile (determines if fixes should be applied)
        debug: Enable debug output
        max_repair_attempts: Maximum repair iterations
    
    Returns:
        Generated Solidity code
    """
    
    if debug:
        print("\n" + "="*80)
        print("CODE GENERATION START")
        print("="*80)
        print(f"Profile: {profile.category}")
        print(f"Is Template: {profile.is_template}")
        print(f"Will apply fixes: {profile.is_template}")
    
    # Check prompt size and truncate if needed
    total_prompt = system_prompt + user_prompt
    estimated_tokens = estimate_tokens(total_prompt)
    
    if estimated_tokens > MAX_PROMPT_TOKENS:
        if debug:
            print(f"Warning: Prompt too large ({estimated_tokens} tokens), truncating spec...")
        # Truncate json_spec in user_prompt (this is a simplified check - in practice, 
        # you'd want to rebuild the prompt with truncated spec)
        # For now, we'll proceed but log a warning
        if debug:
            print(f"Proceeding with large prompt - consider optimizing spec size")
    
    # Initial generation with resilient wrapper
    if debug:
        print("\n[1] Calling GPT-4o for initial code generation...")
        print(f"    Estimated prompt tokens: {estimated_tokens}")
    
    try:
        response = call_chat_completion(
            client=_client,
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            timeout=120,  # Longer timeout for code generation
            max_retries=1,
            debug=debug
        )
    except Exception as e:
        if debug:
            print(f"[1] LLM call failed: {e}")
        raise RuntimeError(f"Failed to generate code: {e}")
    
    solidity_code = response.choices[0].message.content or ""
    
    if debug:
        print(f"[1] Generated {len(solidity_code)} characters")
    
    # Clean up markdown fences and ensure headers
    solidity_code = strip_markdown_fences(solidity_code)
    solidity_code = ensure_headers(solidity_code)
    
    # Initialize fixes tracking
    fixes_applied = []
    
    # Decide whether to apply fixes based on profile
    should_apply_fixes = profile.is_template
    
    if not should_apply_fixes:
        if debug:
            print("\n[2] Custom contract detected - validating syntax and semantics...")
        
        # Validate both syntax and semantics (but don't apply constructor fixes)
        syntax_result = validate_generated_code(solidity_code, debug=debug)
        semantic_result = validate_semantics(solidity_code, json_spec, debug=debug)
        
        if debug:
            syntax_status = "✅ VALID" if syntax_result['is_valid'] else "⚠️  HAS ISSUES"
            semantic_status = "✅ VALID" if semantic_result['is_valid'] else "⚠️  HAS ISSUES"
            print(f"\nSyntax Status: {syntax_status}")
            print(f"  Errors: {syntax_result['error_count']}, Warnings: {syntax_result['warning_count']}")
            print(f"\nSemantic Status: {semantic_status}")
            print(f"  Errors: {semantic_result['error_count']}, Warnings: {semantic_result['warning_count']}")
            
            if semantic_result['errors']:
                print("\nSemantic errors (will attempt repair):")
                for err in semantic_result['errors'][:3]:
                    print(f"  - {err}")
        
        # For custom contracts, we still fix semantic issues (logic problems)
        # but skip constructor fixes (which might break custom logic)
        if semantic_result['errors']:
            if debug:
                print("\n[2.5] Fixing semantic/logic issues for custom contract...")
            
            errors_before = semantic_result['error_count']
            code_before = solidity_code
            
            solidity_code = repair_semantic_issues(
                _client,
                solidity_code,
                semantic_result['errors'],
                json_spec,
                debug=debug
            )
            
            # Re-validate after repair
            semantic_result_after = validate_semantics(solidity_code, json_spec, debug=debug)
            
            if code_before != solidity_code:
                fixes_applied.append({
                    "attempt": 0,
                    "method": "semantic_repair",
                    "description": "Fixed semantic/logic issues for custom contract",
                    "errors_before": errors_before,
                    "errors_after": semantic_result_after['error_count']
                })
            
            if debug:
                if semantic_result_after['is_valid']:
                    print("[2.5] ✅ Semantic issues resolved!")
                else:
                    print(f"[2.5] ⚠️  Some semantic issues remain: {semantic_result_after['error_count']} errors")
        
        return solidity_code, fixes_applied
    
    # For template contracts, apply validation and repair loop
    if debug:
        print("\n[2] Template contract - applying validation and repair loop...")
    
    for attempt in range(max_repair_attempts):
        if debug:
            print(f"\n[{attempt + 2}] Validation attempt {attempt + 1}/{max_repair_attempts}")
        
        # Validate both syntax and semantics
        syntax_result = validate_generated_code(solidity_code, debug=debug)
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
                    print(f"[{attempt + 2}] ✅ All validations passed!")
                else:
                    print(f"[{attempt + 2}] Max attempts reached, proceeding with current code")
            break
        
        # Priority 1: Fix semantic/logic issues first
        if semantic_result['errors']:
            if debug:
                print(f"[{attempt + 2}] Fixing semantic/logic issues...")
            
            code_before = solidity_code
            solidity_code = repair_semantic_issues(
                _client,
                solidity_code,
                semantic_result['errors'],
                json_spec,
                debug=debug
            )
            
            if code_before != solidity_code:
                fixes_applied.append({
                    "attempt": attempt + 1,
                    "method": "semantic_repair",
                    "description": "Fixed semantic/logic issues",
                    "errors_before": semantic_result['error_count']
                })
            
            # Re-validate after semantic repair
            semantic_result = validate_semantics(solidity_code, json_spec, debug=debug)
            if semantic_result['is_valid']:
                if debug:
                    print(f"[{attempt + 2}] ✅ Semantic issues resolved!")
        
        # Priority 2: Fix syntax/constructor issues
        if not syntax_result['is_valid']:
            if debug:
                print(f"[{attempt + 2}] Applying constructor resolver...")
            
            code_before = solidity_code
            resolver = ConstructorResolver(debug=debug)
            solidity_code = resolver.process(solidity_code, json_spec)
            
            # Track fix
            if code_before != solidity_code:
                fixes_applied.append({
                    "attempt": attempt + 1,
                    "method": "constructor_resolver",
                    "description": "Applied constructor fixes for OpenZeppelin v5 compatibility",
                    "errors_before": syntax_result['error_count'],
                    "warnings_before": syntax_result['warning_count']
                })
            
            # Re-validate after constructor fix
            syntax_result = validate_generated_code(solidity_code, debug=debug)
            if syntax_result['is_valid']:
                if debug:
                    print(f"[{attempt + 2}] ✅ Constructor resolver fixed the issues!")
                continue
            
            # If still issues, use model repair
            if debug:
                print(f"[{attempt + 2}] Using model repair for remaining syntax issues...")
            
            code_before = solidity_code
            solidity_code = repair_with_model_if_needed(_client, solidity_code)
            
            # Track model repair
            if code_before != solidity_code:
                fixes_applied.append({
                    "attempt": attempt + 1,
                    "method": "model_repair",
                    "description": "Applied LLM-based repair for remaining validation issues",
                    "errors_before": syntax_result['error_count']
                })
    
    # Final validation report
    final_syntax = validate_generated_code(solidity_code, debug=debug)
    final_semantic = validate_semantics(solidity_code, json_spec, debug=debug)
    
    if debug:
        print("\n" + "="*80)
        print("CODE GENERATION COMPLETE")
        print("="*80)
        
        syntax_status = "✅ VALID" if final_syntax['is_valid'] else "⚠️  HAS ISSUES"
        semantic_status = "✅ VALID" if final_semantic['is_valid'] else "⚠️  HAS ISSUES"
        
        print(f"Syntax Status: {syntax_status}")
        print(f"  Errors: {final_syntax['error_count']}, Warnings: {final_syntax['warning_count']}")
        
        print(f"\nSemantic Status: {semantic_status}")
        print(f"  Errors: {final_semantic['error_count']}, Warnings: {final_semantic['warning_count']}")
        
        if final_semantic['errors']:
            print("\nRemaining semantic issues:")
            for err in final_semantic['errors'][:5]:
                print(f"  - {err}")
        
        if final_semantic['warnings']:
            print("\nSemantic warnings (first 5):")
            for warn in final_semantic['warnings'][:5]:
                print(f"  - {warn}")
        
        print("="*80 + "\n")
    
    return solidity_code, fixes_applied
