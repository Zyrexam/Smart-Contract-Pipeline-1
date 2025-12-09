
"""
Dynamic Profile Selector using LLM Classification

Uses LLM to classify contracts and build appropriate profiles
instead of hardcoded keyword matching.
"""

from typing import Dict
from .categories_v2 import ContractProfile
from .llm_classifier import classify_contract


def select_profile_dynamic(user_input: str, json_spec: Dict, debug: bool = False) -> Dict:
    """
    Select contract profile using LLM classification.
    
    Args:
        user_input: Original user input (natural language)
        json_spec: JSON specification from Stage 1
        debug: Enable debug output
    
    Returns:
        Dict with 'classification' and 'profile' keys
    """
    
    # Step 1: LLM Classification
    classification = classify_contract(user_input, json_spec, debug=debug)
    
    # Step 2: Build profile based on classification
    profile = _build_profile_from_classification(classification, json_spec)
    
    return {
        'classification': classification,
        'profile': profile
    }


def _build_profile_from_classification(classification: Dict, json_spec: Dict) -> ContractProfile:
    """Build ContractProfile from LLM classification"""
    
    contract_type = classification['contract_type']
    is_template = classification.get('is_template', False)
    subtype = classification.get('subtype')
    
    # Determine access control
    roles = json_spec.get('roles', [])
    if len(roles) > 1:
        access_control = "role_based"
    elif len(roles) == 1 or any(f.get('restricted_to') for f in json_spec.get('functions', [])):
        access_control = "role_based"
    else:
        access_control = "single_owner"
    
    # Determine security features
    security_features = []
    functions = json_spec.get('functions', [])
    
    # Check for payable functions (need ReentrancyGuard)
    if any(f.get('payable', False) for f in functions):
        security_features.append("ReentrancyGuard")
    
    # For custom contracts, add ReentrancyGuard if handling payments
    if not is_template:
        description = json_spec.get('description', '').lower()
        if any(word in description for word in ['payment', 'transfer', 'withdraw', 'distribute', 'royalty']):
            if "ReentrancyGuard" not in security_features:
                security_features.append("ReentrancyGuard")
        
        # For elections and supply chain, add ReentrancyGuard
        if subtype in ['election', 'supply_chain', 'royalty']:
            if "ReentrancyGuard" not in security_features:
                security_features.append("ReentrancyGuard")
    
    # Build extensions for template contracts
    extensions = []
    if is_template and contract_type == "ERC20":
        func_names = {f.get('name', '').lower() for f in functions}
        if 'burn' in func_names:
            extensions.append("Burnable")
        if any('cap' in v.get('name', '').lower() or 'max' in v.get('name', '').lower() 
               for v in json_spec.get('state_variables', [])):
            extensions.append("Capped")
        if 'pause' in func_names or 'unpause' in func_names:
            extensions.append("Pausable")
            security_features.append("Pausable")
    
    # Determine base standard
    if is_template:
        if contract_type == "ERC20":
            base_standard = "ERC20"
            if "Capped" in extensions:
                base_standard = "ERC20Capped"
            elif "Burnable" in extensions:
                base_standard = "ERC20Burnable"
        elif contract_type == "ERC721":
            base_standard = "ERC721"
        elif contract_type == "Governor":
            base_standard = "Governor"
        else:
            base_standard = contract_type
    else:
        base_standard = "Custom"
    
    return ContractProfile(
        category=contract_type,
        base_standard=base_standard,
        extensions=extensions,
        access_control=access_control,
        security_features=security_features,
        subtype=subtype,
        is_template=is_template,
    )
