# solidity_code_generator/generator.py
from typing import Dict, List
from .categories import GenerationResult, SpecCoverage, ContractProfile, ContractCategory
from .profile_selector import select_profile
from .coverage_mapper import CoverageMapper
from .prompt_builder import build_prompts
from .code_generator import generate_solidity_code

class SpecValidator:
    REQUIRED_FIELDS = ["contract_name", "contract_type"]
    VALID_VISIBILITIES = {"public","private","internal","external"}
    @staticmethod
    def validate(json_spec: Dict) -> List[str]:
        errors = []
        for f in SpecValidator.REQUIRED_FIELDS:
            if f not in json_spec or not json_spec[f]:
                errors.append(f"Missing required field: '{f}'")
        for var in json_spec.get("state_variables", []):
            if "name" not in var or "type" not in var:
                errors.append(f"State variable missing 'name' or 'type': {var}")
            vis = var.get("visibility")
            if vis and vis not in SpecValidator.VALID_VISIBILITIES:
                errors.append(f"Invalid visibility '{vis}' for variable '{var.get('name')}'")
        for func in json_spec.get("functions", []):
            if "name" not in func:
                errors.append(f"Function missing 'name': {func}")
            vis = func.get("visibility")
            if vis and vis not in SpecValidator.VALID_VISIBILITIES:
                errors.append(f"Invalid visibility for function '{func.get('name')}'")
            restricted_to = func.get("restricted_to")
            if restricted_to:
                roles = [r.get("name") for r in json_spec.get("roles",[])]
                if restricted_to not in roles and restricted_to != "owner":
                    errors.append(f"Function '{func.get('name')}' restricted to undefined role '{restricted_to}'")
        return errors

def generate_solidity(json_spec: Dict, debug: bool = False) -> GenerationResult:
    print("="*80)
    print("STAGE 2: GENERATING SOLIDITY (MODULAR)")
    print("="*80)
    # 1) Validate
    validation_errors = SpecValidator.validate(json_spec)
    if validation_errors:
        print(f"Found {len(validation_errors)} validation issues (stage2 will still run):")
        for e in validation_errors[:5]:
            print(" -", e)
    else:
        print("Spec validation OK")
    # 2) Profile selection
    profile: ContractProfile = select_profile(json_spec)
    print("Profile:", profile.base_standard, "|", profile.category.value)
    # 3) Coverage
    coverage: SpecCoverage = CoverageMapper.map_specification(json_spec, profile)
    # 4) Build prompts & generate code
    system_prompt, user_prompt, imports_used, inheritance_chain = build_prompts(json_spec, profile, coverage)
    solidity_code = generate_solidity_code(system_prompt, user_prompt, json_spec, debug=debug)
    # 5) Security summary (simple)
    security_summary = f"Access Control: {profile.access_control.value}\nSecurity Features: {', '.join([s.value for s in profile.security_features]) or 'Standard'}\n"
    # 6) Build result
    result = GenerationResult(
        solidity_code=solidity_code,
        profile=profile,
        coverage=coverage,
        validation_errors=validation_errors,
        security_summary=security_summary,
        imports_used=imports_used,
        inheritance_chain=inheritance_chain,
    )
    print("Generation complete")
    print("="*80)
    return result
