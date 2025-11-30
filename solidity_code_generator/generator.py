"""High-level Stage 2 generator entry point.

This is the module you should call from your pipeline:

    from solidity_code_generator import generate_solidity

It takes ONLY the Stage 1 JSON specification and returns a GenerationResult
with Solidity code + rich metadata. It does **not** consume the original
natural language prompt.
"""

from __future__ import annotations

from typing import Dict, List

from .categories import (
    ContractCategory,
    ContractProfile,
    SpecCoverage,
    GenerationResult,
    AccessControlType,
    SecurityFeature,
)
from .profile_selector import select_profile
from .coverage_mapper import CoverageMapper
from .prompt_builder import build_prompts
from .code_generator import generate_solidity_code


# ---------------------------------------------------------------------------
# Spec validation
# ---------------------------------------------------------------------------


class SpecValidator:
    """Lightweight structural validation of Stage 1 JSON.

    This is not meant to be exhaustive, just enough to catch obvious
    issues before we ask the model to generate code.
    """

    REQUIRED_FIELDS = ["contract_name", "contract_type"]
    VALID_VISIBILITIES = {"public", "private", "internal", "external"}

    @staticmethod
    def validate(json_spec: Dict) -> List[str]:
        errors: List[str] = []

        for field in SpecValidator.REQUIRED_FIELDS:
            if field not in json_spec or not json_spec[field]:
                errors.append(f"Missing required field: '{field}'")

        for var in json_spec.get("state_variables", []):
            if "name" not in var or "type" not in var:
                errors.append(f"State variable missing 'name' or 'type': {var}")
            vis = var.get("visibility")
            if vis and vis not in SpecValidator.VALID_VISIBILITIES:
                errors.append(
                    f"Invalid visibility '{vis}' for variable '{var.get('name')}'"
                )

        for func in json_spec.get("functions", []):
            if "name" not in func:
                errors.append(f"Function missing 'name': {func}")
            vis = func.get("visibility")
            if vis and vis not in SpecValidator.VALID_VISIBILITIES:
                errors.append(f"Invalid visibility for function '{func.get('name')}'")

            restricted_to = func.get("restricted_to")
            if restricted_to:
                roles = [r.get("name") for r in json_spec.get("roles", [])]
                if restricted_to not in roles and restricted_to != "owner":
                    errors.append(
                        f"Function '{func.get('name')}' restricted to undefined role '{restricted_to}'"
                    )

        return errors


# ---------------------------------------------------------------------------
# High-level generator API
# ---------------------------------------------------------------------------


def generate_solidity(json_spec: Dict) -> GenerationResult:
    """Run complete Stage 2 on a Stage 1 spec.

    Args:
        json_spec: Structured JSON from Stage 1 intent extraction.

    Returns:
        GenerationResult with Solidity source + metadata.
    """

    print("=" * 80)
    print("STAGE 2: ENHANCED SOLIDITY CODE GENERATION")
    print("=" * 80)

    # 1) Validate spec
    print("\n[1/6] Validating specification...")
    validation_errors = SpecValidator.validate(json_spec)
    if validation_errors:
        print(f"⚠️  Found {len(validation_errors)} validation issues (Stage 2 will still run):")
        for err in validation_errors[:5]:
            print(f"    • {err}")
        if len(validation_errors) > 5:
            print(f"    ... and {len(validation_errors) - 5} more")
    else:
        print("✓ Specification looks structurally valid")

    # 2) Profile selection
    print("\n[2/6] Selecting contract profile...")
    profile: ContractProfile = select_profile(json_spec)
    print(f"✓ Category: {profile.category.value}")
    print(f"  Base: {profile.base_standard}")
    print(f"  Extensions: {', '.join(profile.extensions) or 'None'}")
    print(
        f"  Security: {', '.join(sf.value for sf in profile.security_features) or 'Standard OpenZeppelin'}"
    )

    # 3) Coverage mapping
    print("\n[3/6] Mapping specification to implementation...")
    coverage: SpecCoverage = CoverageMapper.map_specification(json_spec, profile)
    print(f"✓ Mapped {len(coverage.state_variables)} state variables")
    print(f"✓ Mapped {len(coverage.functions)} functions")
    print(f"✓ Mapped {len(coverage.events)} events")

    # 4) Prompt building + code generation
    print("\n[4/6] Building prompts and generating Solidity code...")
    system_prompt, user_prompt, imports_used, inheritance_chain = build_prompts(
        json_spec, profile, coverage
    )
    solidity_code = generate_solidity_code(system_prompt, user_prompt)
    print("✓ Code generated")

    # 5) Security summary (purely descriptive)
    print("\n[5/6] Building security summary...")
    security_summary = (
        "Security Analysis:\n"
        f"- Access Control: {profile.access_control.value}\n"
        f"- Security Features: {', '.join(sf.value for sf in profile.security_features) or 'Standard OpenZeppelin protections'}\n"
        "- Overflow Protection: Built-in via Solidity ^0.8.20\n"
        f"- Reentrancy: {'Protected with ReentrancyGuard' if SecurityFeature.REENTRANCY_GUARD in profile.security_features else 'No explicit guard; relies on checks-effects-interactions'}\n"
    )
    print(security_summary)

    # 6) Assemble result
    print("\n[6/6] Finalizing Stage 2 result...")
    result = GenerationResult(
        solidity_code=solidity_code,
        profile=profile,
        coverage=coverage,
        validation_errors=validation_errors,
        security_summary=security_summary,
        imports_used=imports_used,
        inheritance_chain=inheritance_chain,
    )

    print("\n✅ STAGE 2 COMPLETE")
    print("=" * 80)

    return result
