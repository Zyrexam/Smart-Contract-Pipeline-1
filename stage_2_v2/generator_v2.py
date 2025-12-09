"""
Dynamic Solidity Generation with LLM-Powered Classification

This is the new Stage 2 that uses LLM classification instead of
hardcoded category detection.

Flow:
1. LLM classifies contract type
2. Build appropriate profile (template or custom)
3. Generate code with profile-aware prompts
4. Apply fixes only where appropriate
"""

from typing import Dict, List
from .categories_v2 import GenerationResult, SpecCoverage, ContractProfile
from .llm_classifier import classify_contract
from .profile_selector_v2 import select_profile_dynamic
from .coverage_mapper_v2 import CoverageMapper
from .updated_prompt_builder_v2 import build_prompts_dynamic
from .code_generator_v2 import generate_solidity_code


class SpecValidator:
    """Validates JSON specification"""
    
    REQUIRED_FIELDS = ["contract_name"]
    VALID_VISIBILITIES = {"public", "private", "internal", "external"}
    
    @staticmethod
    def validate(json_spec: Dict) -> List[str]:
        """Validate specification and return errors"""
        errors = []
        
        # Check required fields
        for field in SpecValidator.REQUIRED_FIELDS:
            if field not in json_spec or not json_spec[field]:
                errors.append(f"Missing required field: '{field}'")
        
        # Validate state variables
        for var in json_spec.get("state_variables", []):
            if "name" not in var:
                errors.append(f"State variable missing 'name': {var}")
            vis = var.get("visibility")
            if vis and vis not in SpecValidator.VALID_VISIBILITIES:
                errors.append(f"Invalid visibility '{vis}' for variable '{var.get('name')}'")
        
        # Validate functions
        for func in json_spec.get("functions", []):
            if "name" not in func:
                errors.append(f"Function missing 'name': {func}")
            vis = func.get("visibility")
            if vis and vis not in SpecValidator.VALID_VISIBILITIES:
                errors.append(f"Invalid visibility for function '{func.get('name')}'")
        
        return errors


def generate_solidity_v2(
    user_input: str,
    json_spec: Dict,
    debug: bool = False
) -> GenerationResult:
    """
    Generate Solidity code using LLM-powered classification.
    
    Args:
        user_input: Original user input (natural language)
        json_spec: JSON specification from Stage 1
        debug: Enable debug output
    
    Returns:
        GenerationResult with code, profile, coverage, and metadata
    """
    
    if debug:
        print("\n" + "="*80)
        print("STAGE 2: DYNAMIC SOLIDITY GENERATION")
        print("="*80)
    
    # Step 1: Validate specification
    validation_errors = SpecValidator.validate(json_spec)
    if validation_errors:
        if debug:
            print(f"\nValidation warnings: {len(validation_errors)}")
            for err in validation_errors[:5]:
                print(f"  - {err}")
    else:
        if debug:
            print("\nSpecification validation: OK")
    
    # Step 2: LLM Classification + Profile Selection
    if debug:
        print("\n[Step 1/4] LLM Classification & Profile Selection...")
    
    result = select_profile_dynamic(user_input, json_spec, debug=debug)
    classification = result['classification']
    profile = result['profile']
    
    if debug:
        print(f"\nClassified as: {classification['contract_type']}")
        print(f"Confidence: {classification['confidence']:.0%}")
        print(f"Is Template: {profile.is_template}")
        print(f"Approach: {classification['recommended_approach']}")
        if classification.get('reasoning'):
            print(f"Reasoning: {classification['reasoning']}")
    
    # Step 3: Coverage Mapping
    if debug:
        print("\n[Step 2/4] Coverage Mapping...")
    
    coverage = CoverageMapper.map_specification(json_spec, profile)
    
    if debug:
        print(f"Mapped {len(coverage.functions)} functions")
        print(f"Mapped {len(coverage.state_variables)} state variables")
    
    # Step 4: Build Prompts
    if debug:
        print("\n[Step 3/4] Building Prompts...")
    
    system_prompt, user_prompt, imports_used, inheritance_chain = build_prompts_dynamic(
        json_spec, profile, classification, coverage, debug=debug
    )
    
    if debug:
        print(f"Prompt type: {'Template' if profile.is_template else 'Custom'}")
        print(f"Imports: {len(imports_used)}")
        print(f"Inheritance: {', '.join(inheritance_chain) if inheritance_chain else 'None'}")
    
    # Step 5: Generate Code
    if debug:
        print("\n[Step 4/4] Generating Solidity Code...")
    
    solidity_code, fixes_applied = generate_solidity_code(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_spec=json_spec,
        profile=profile,
        debug=debug
    )
    
    # Step 6: Build Security Summary
    security_summary = _build_security_summary(profile, classification)
    
    # Step 7: Create Result
    result = GenerationResult(
        solidity_code=solidity_code,
        profile=profile,
        coverage=coverage,
        validation_errors=validation_errors,
        security_summary=security_summary,
        imports_used=imports_used,
        inheritance_chain=inheritance_chain,
        classification=classification,
        fixes_applied=fixes_applied
    )
    
    if debug:
        print("\n" + "="*80)
        print("GENERATION COMPLETE")
        print("="*80)
        print(f"Contract Type: {classification['contract_type']}")
        print(f"Category: {profile.category}")
        print(f"Subtype: {profile.subtype or 'N/A'}")
        print(f"Lines of Code: {len(solidity_code.splitlines())}")
        print(f"Classification Confidence: {classification['confidence']:.0%}")
        print("="*80 + "\n")
    
    return result


def _build_security_summary(profile: ContractProfile, classification: Dict) -> str:
    """Build security summary for the contract"""
    
    lines = [
        f"Contract Type: {classification['contract_type']}",
        f"Classification Confidence: {classification['confidence']:.0%}",
        f"Access Control: {profile.access_control}",
    ]
    
    if profile.security_features:
        lines.append(f"Security Features: {', '.join(profile.security_features)}")
    else:
        lines.append("Security Features: Standard")
    
    if profile.is_template:
        lines.append(f"Based on: OpenZeppelin {profile.base_standard}")
    else:
        lines.append("Implementation: Custom from scratch")
    
    if profile.subtype:
        lines.append(f"Subtype: {profile.subtype}")
    
    lines.append(f"\nReasoning: {classification.get('reasoning', 'N/A')}")
    
    return "\n".join(lines)


# Legacy compatibility function
def generate_solidity(json_spec: Dict, debug: bool = False) -> GenerationResult:
    """
    Legacy interface for backward compatibility.
    
    Note: This requires 'description' field in json_spec to work properly
    since it needs user_input for classification.
    """
    
    # Extract user input from description if available
    user_input = json_spec.get('description', '')
    
    # If description is empty, try to reconstruct from contract_type
    if not user_input:
        contract_type = json_spec.get('contract_type', 'contract')
        contract_name = json_spec.get('contract_name', 'Contract')
        user_input = f"Create a {contract_type} contract named {contract_name}"
    
    return generate_solidity_v2(user_input, json_spec, debug=debug)
