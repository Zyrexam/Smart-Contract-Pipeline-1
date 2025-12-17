# solidity_code_generator/semantic_validator.py

"""
Semantic validation to catch logic issues beyond syntax
"""

import re
from typing import List, Dict, Tuple

class SemanticValidator:
    """Validates generated Solidity code for logic and semantic issues"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def validate(self, solidity_code: str, json_spec: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Perform semantic validation
        Returns: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Extract contract info
        contract_info = self._extract_contract_info(solidity_code)
        
        # Check 1: ERC721 semantic issues
        erc721_issues = self._check_erc721_semantics(solidity_code, contract_info, json_spec)
        errors.extend(erc721_issues['errors'])
        warnings.extend(erc721_issues['warnings'])
        
        # Check 2: ERC20 semantic issues
        erc20_issues = self._check_erc20_semantics(solidity_code, contract_info, json_spec)
        errors.extend(erc20_issues['errors'])
        warnings.extend(erc20_issues['warnings'])
        
        # Check 3: ERC1155 semantic issues
        erc1155_issues = self._check_erc1155_semantics(solidity_code, contract_info, json_spec)
        errors.extend(erc1155_issues['errors'])
        warnings.extend(erc1155_issues['warnings'])
        
        # Check 4: Access control conflicts
        access_issues = self._check_access_control_conflicts(solidity_code, contract_info)
        errors.extend(access_issues['errors'])
        warnings.extend(access_issues['warnings'])
        
        # Check 4.5: Constructor initialization
        constructor_issues = self._check_constructor_initialization(solidity_code, contract_info)
        errors.extend(constructor_issues['errors'])
        warnings.extend(constructor_issues['warnings'])
        
        # Check 5: Variable/parameter shadowing
        shadowing_issues = self._check_shadowing(solidity_code, contract_info)
        errors.extend(shadowing_issues['errors'])
        warnings.extend(shadowing_issues['warnings'])
        
        # Check 5: State management issues
        state_issues = self._check_state_management(solidity_code, contract_info, json_spec)
        warnings.extend(state_issues)
        
        # Check 6: Function visibility and access patterns
        access_errors, access_warnings = self._check_function_access_patterns(solidity_code, contract_info, json_spec)
        errors.extend(access_errors)
        warnings.extend(access_warnings)
        
        is_valid = len(errors) == 0
        
        if self.debug:
            print(f"[SemanticValidator] Valid: {is_valid}, Errors: {len(errors)}, Warnings: {len(warnings)}")
        
        return is_valid, errors, warnings
    
    def _extract_contract_info(self, code: str) -> Dict:
        """Extract key contract information"""
        info = {
            'parents': [],
            'functions': [],
            'state_vars': [],
            'has_constructor': False,
            'contract_name': ''
        }
        
        # Extract contract name and parents
        contract_match = re.search(r'contract\s+(\w+)(?:\s+is\s+([^{]+))?\s*\{', code)
        if contract_match:
            info['contract_name'] = contract_match.group(1)
            if contract_match.group(2):
                info['parents'] = [p.strip() for p in contract_match.group(2).split(',')]
        
        # Extract functions
        func_pattern = r'function\s+(\w+)\s*\([^)]*\)\s+([^{]*)\{'
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            func_modifiers = match.group(2)
            info['functions'].append({
                'name': func_name,
                'modifiers': func_modifiers,
                'is_external': 'external' in func_modifiers,
                'is_public': 'public' in func_modifiers,
                'is_view': 'view' in func_modifiers,
                'is_payable': 'payable' in func_modifiers
            })
        
        # Check for constructor
        info['has_constructor'] = 'constructor' in code
        
        return info
    
    def _check_erc721_semantics(self, code: str, info: Dict, spec: Dict) -> Dict:
        """Check ERC721 implementation logic"""
        errors = []
        warnings = []
        
        if 'ERC721' not in info['parents']:
            return {'errors': errors, 'warnings': warnings}
        
        func_names = {f['name'].lower() for f in info['functions']}
        
        # Critical: ERC721 should have minting capability if managing tokens
        has_mint = 'mint' in func_names or 'safemint' in func_names
        has_transfer_logic = any('transfer' in fn or 'rent' in fn for fn in func_names)
        
        if has_transfer_logic and not has_mint:
            errors.append(
                "CRITICAL: Contract manages NFT transfers/rentals but has no mint function. "
                "ERC721 tokens must be minted before they can be transferred or rented."
            )
        
        # Check for rental logic without proper token ownership management
        has_rental = any('rent' in fn for fn in func_names)
        if has_rental:
            # Check if contract properly handles token ownership
            has_owner_tracking = 'ownerOf' in code or '_ownerOf' in code
            has_transfer_from = any('transferfrom' in fn or 'safetransferfrom' in fn for fn in func_names)
            
            # Check if rental uses actual transfers or just state variables
            uses_actual_transfer = '_transfer' in code or 'transferFrom' in code or 'safeTransferFrom' in code
            
            if has_rental and not uses_actual_transfer:
                errors.append(
                    "CRITICAL: Rental logic without actual token transfers. "
                    "NFT rentals must use _transfer() or transferFrom() to change ownership. "
                    "State variables alone are not sufficient for ERC721 compliance."
                )
            
            # Check for return mechanism
            has_return = any('return' in fn or 'withdraw' in fn or 'reclaim' in fn for fn in func_names)
            if has_rental and not has_return:
                warnings.append(
                    "WARNING: NFT rental logic without clear return/reclaim mechanism. "
                    "Rentals should have a way to return NFTs to owners after rental period."
                )
        
        # Check for enumeration if needed
        spec_funcs = [f.get('name', '').lower() for f in spec.get('functions', [])]
        if 'tokenofownerbyindex' in spec_funcs and 'ERC721Enumerable' not in info['parents']:
            warnings.append(
                "INFO: Spec requires enumeration but ERC721Enumerable not inherited. "
                "Add ERC721Enumerable for tokenOfOwnerByIndex support."
            )
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_erc20_semantics(self, code: str, info: Dict, spec: Dict) -> Dict:
        """Check ERC20 implementation logic"""
        errors = []
        warnings = []
        
        if 'ERC20' not in info['parents']:
            return {'errors': errors, 'warnings': warnings}
        
        func_names = {f['name'].lower() for f in info['functions']}
        
        # Check for transfer restrictions without _update override
        has_transfer_restriction = any(
            'pause' in fn or 'whitelist' in fn or 'blacklist' in fn or 'tax' in fn
            for fn in func_names
        )
        has_update_override = '_update' in code and 'function _update' in code
        
        if has_transfer_restriction and not has_update_override:
            warnings.append(
                "WARNING: Transfer restrictions (pause/whitelist/tax) without _update override. "
                "OpenZeppelin v5 requires _update override for transfer customization."
            )
        
        # Check for mint without access control
        has_mint = 'mint' in func_names
        mint_func = next((f for f in info['functions'] if f['name'].lower() == 'mint'), None)
        
        if has_mint and mint_func:
            has_access_control = any(
                mod in mint_func['modifiers'] 
                for mod in ['onlyOwner', 'onlyRole', 'onlyMinter']
            )
            if not has_access_control:
                errors.append(
                    "CRITICAL: mint() function without access control. "
                    "Mint functions must be restricted to prevent unauthorized token creation."
                )
        
        # Check for burn functionality
        spec_funcs = [f.get('name', '').lower() for f in spec.get('functions', [])]
        if 'burn' in spec_funcs:
            if 'ERC20Burnable' not in info['parents'] and 'burn' not in func_names:
                warnings.append(
                    "INFO: Spec requires burn but neither ERC20Burnable inherited nor custom burn implemented."
                )
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_erc1155_semantics(self, code: str, info: Dict, spec: Dict) -> Dict:
        """Check ERC1155 implementation logic"""
        errors = []
        warnings = []
        
        if 'ERC1155' not in info['parents']:
            return {'errors': errors, 'warnings': warnings}
        
        func_names = {f['name'].lower() for f in info['functions']}
        
        # ERC1155 should have minting capability
        has_mint = 'mint' in func_names or 'mintbatch' in func_names
        has_transfer_logic = any('transfer' in fn or 'safe' in fn for fn in func_names)
        
        if has_transfer_logic and not has_mint:
            errors.append(
                "CRITICAL: ERC1155 contract manages transfers but has no mint function. "
                "ERC1155 tokens must be minted before they can be transferred."
            )
        
        # Check for batch operations if needed
        spec_funcs = [f.get('name', '').lower() for f in spec.get('functions', [])]
        if any('batch' in fn for fn in spec_funcs):
            has_batch = any('batch' in fn for fn in func_names)
            if not has_batch:
                warnings.append(
                    "INFO: Spec requires batch operations but not implemented. "
                    "Consider adding safeBatchTransferFrom for efficiency."
                )
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_access_control_conflicts(self, code: str, info: Dict) -> Dict:
        """Check for access control conflicts"""
        errors = []
        warnings = []
        
        has_ownable = 'Ownable' in info['parents']
        has_access_control = 'AccessControl' in info['parents']
        
        # Critical: Both Ownable and AccessControl is usually a mistake
        if has_ownable and has_access_control:
            # Check if there's a legitimate use case (e.g., owner + roles)
            # But for most cases, it's redundant
            roles_used = len(re.findall(r'onlyRole\([^)]+\)', code))
            owner_used = len(re.findall(r'onlyOwner', code))
            
            if roles_used == 0 or owner_used == 0:
                errors.append(
                    "CRITICAL: Contract inherits both Ownable AND AccessControl but only uses one. "
                    "This creates conflicts and is redundant. Choose one: "
                    "Use Ownable for single owner, or AccessControl for role-based permissions."
                )
            else:
                warnings.append(
                    "WARNING: Contract uses both Ownable and AccessControl. "
                    "Consider if this is necessary - usually one pattern is sufficient."
                )
        
        # Check for role-based functions without proper role grants
        if has_access_control:
            # CRITICAL: Check for deprecated _setupRole (OpenZeppelin v5 removed it)
            if re.search(r'_setupRole\s*\(', code):
                errors.append(
                    "CRITICAL: _setupRole() is deprecated in OpenZeppelin v5. "
                    "Use _grantRole() instead. Example: _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);"
                )
            
            # Find role definitions
            role_pattern = r'bytes32\s+public\s+constant\s+(\w+_ROLE)\s*='
            roles = re.findall(role_pattern, code)
            
            # Check if roles are granted in constructor
            if roles and info['has_constructor']:
                constructor_match = re.search(r'constructor[^{]*\{([^}]*)\}', code, re.DOTALL)
                if constructor_match:
                    constructor_body = constructor_match.group(1)
                    for role in roles:
                        if role not in constructor_body and '_grantRole' not in constructor_body:
                            warnings.append(
                                f"WARNING: Role {role} defined but not granted in constructor. "
                                f"Remember to grant roles or users won't be able to call restricted functions."
                            )
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_shadowing(self, code: str, info: Dict) -> Dict:
        """Check for variable/parameter shadowing issues"""
        errors = []
        warnings = []
        
        # Extract all function names (including inherited)
        function_names = {f['name'].lower() for f in info['functions']}
        
        # Common OpenZeppelin function names that shouldn't be shadowed
        oz_functions = {
            'tokenuri', 'ownerof', 'balanceof', 'approve', 'transfer', 
            'transferfrom', 'safetransferfrom', 'setapprovalforall',
            'getapproved', 'isapprovedforall', 'supportsinterface',
            'totalsupply', 'name', 'symbol', 'decimals'
        }
        
        # Extract function parameters
        func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            params = match.group(2)
            
            # Extract parameter names (handle various formats)
            param_pattern = r'(\w+)\s+(?:memory|storage|calldata)?\s*\w+'
            for param_match in re.finditer(param_pattern, params):
                param_name = param_match.group(1).lower()
                
                # Check if parameter shadows a function
                if param_name in function_names:
                    errors.append(
                        f"CRITICAL: Parameter '{param_match.group(1)}' in function '{func_name}' shadows "
                        f"the function '{param_name}()'. Rename the parameter (e.g., '{param_match.group(1)}Value', "
                        f"'{param_match.group(1)}Param', or '{param_match.group(1)}Data')."
                    )
                elif param_name in oz_functions:
                    errors.append(
                        f"CRITICAL: Parameter '{param_match.group(1)}' in function '{func_name}' shadows "
                        f"OpenZeppelin function '{param_name}()'. Rename the parameter (e.g., '{param_match.group(1)}Value', "
                        f"'{param_match.group(1)}Param', or '{param_match.group(1)}Data')."
                    )
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_constructor_initialization(self, code: str, info: Dict) -> Dict:
        """Check constructor initialization for OpenZeppelin v5 compliance"""
        errors = []
        warnings = []
        
        has_ownable = 'Ownable' in info['parents']
        has_constructor = info['has_constructor']
        
        if has_ownable and has_constructor:
            # Check if constructor has Ownable(msg.sender) or Ownable(initialOwner)
            constructor_match = re.search(r'constructor[^{]*\{', code, re.DOTALL)
            if constructor_match:
                constructor_line = constructor_match.group(0)
                # Check if Ownable is initialized in constructor
                if 'Ownable(' not in constructor_line:
                    errors.append(
                        "CRITICAL: Contract inherits Ownable but constructor doesn't initialize it. "
                        "OpenZeppelin v5 requires: constructor(...) Ownable(msg.sender) {...}"
                    )
                elif 'Ownable()' in constructor_line:
                    errors.append(
                        "CRITICAL: Ownable constructor called without initialOwner parameter. "
                        "OpenZeppelin v5 requires: Ownable(msg.sender) or Ownable(initialOwner)"
                    )
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_state_management(self, code: str, info: Dict, spec: Dict) -> List[str]:
        """Check state variable management patterns"""
        warnings = []
        
        # Check for redundant state variables when using standard contracts
        if 'ERC721' in info['parents']:
            redundant_vars = ['owner', 'tokenowner', 'nftowner']
            for var in redundant_vars:
                if re.search(rf'\b{var}\b\s*;', code, re.IGNORECASE):
                    warnings.append(
                        f"INFO: State variable '{var}' may be redundant. "
                        f"ERC721 already tracks token ownership via ownerOf()."
                    )
        
        if 'ERC20' in info['parents']:
            redundant_vars = ['balance', 'balances', 'totalsupply']
            for var in redundant_vars:
                if re.search(rf'\b{var}\b\s*;', code, re.IGNORECASE):
                    warnings.append(
                        f"INFO: State variable '{var}' may be redundant. "
                        f"ERC20 already manages balances and total supply."
                    )
        
        return warnings
    
    def _check_function_access_patterns(self, code: str, info: Dict, spec: Dict) -> Tuple[List[str], List[str]]:
        """Check function access patterns for common issues
        Returns: (errors, warnings)
        """
        warnings = []
        errors = []  # Track errors for rental functions
        
        # Check for overly restrictive access
        for func in info['functions']:
            fname = func['name'].lower()
            modifiers = func['modifiers'].lower()
            
            # User-facing functions shouldn't require roles by default
            user_functions = ['rent', 'buy', 'purchase', 'claim', 'stake', 'unstake', 'vote']
            if any(uf in fname for uf in user_functions):
                if 'onlyrole' in modifiers.replace(' ', ''):
                    warnings.append(
                        f"WARNING: Function '{func['name']}' requires a role. "
                        f"User-facing functions typically shouldn't require role grants. "
                        f"Consider making it public/external without role restrictions."
                    )
        
        # Check for missing payable on functions that should handle ETH
        # For rental NFT systems, rentNFT should typically be payable
        eth_functions = ['buy', 'purchase', 'bid', 'pay', 'rent']
        has_rental_logic = any('rent' in f['name'].lower() for f in info['functions'])
        
        for func in info['functions']:
            func_name_lower = func['name'].lower()
            if any(ef in func_name_lower for ef in eth_functions):
                if not func['is_payable']:
                    # For rental functions in rental systems, this is more critical
                    if has_rental_logic and 'rent' in func_name_lower:
                        # This is a logic issue - rental functions usually need payable
                        errors.append(
                            f"CRITICAL: Function '{func['name']}' is a rental function but not marked payable. "
                            f"Rental NFT systems typically require ETH payments. Add 'payable' modifier."
                        )
                    else:
                        # Check if function should receive ETH based on spec
                        spec_funcs = {f.get('name', '').lower() for f in spec.get('functions', [])}
                        if func['name'].lower() in spec_funcs:
                            warnings.append(
                                f"INFO: Function '{func['name']}' suggests ETH handling but not marked payable. "
                                f"Add 'payable' modifier if it should receive ETH."
                            )
        
        return errors, warnings


def validate_semantics(solidity_code: str, json_spec: Dict, debug: bool = False) -> Dict:
    """
    Validate Solidity code for semantic and logic issues
    Returns dict with validation results
    """
    validator = SemanticValidator(debug=debug)
    is_valid, errors, warnings = validator.validate(solidity_code, json_spec)
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings)
    }

