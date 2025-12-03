# solidity_code_generator/validator.py
"""
Post-generation validation to catch common issues before compilation
"""
import re
from typing import List, Dict, Tuple

class SolidityValidator:
    """Validates generated Solidity code for common issues"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def validate(self, solidity_code: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Solidity code
        Returns: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check 1: Has required headers
        if "SPDX-License-Identifier" not in solidity_code:
            errors.append("Missing SPDX license identifier")
        if "pragma solidity" not in solidity_code:
            errors.append("Missing pragma statement")
        
        # Check 2: OpenZeppelin v5 compatibility
        oz_issues = self._check_openzeppelin_v5(solidity_code)
        errors.extend(oz_issues)
        
        # Check 3: Constructor issues
        constructor_issues = self._check_constructors(solidity_code)
        errors.extend(constructor_issues)
        
        # Check 4: Access control patterns
        access_warnings = self._check_access_control(solidity_code)
        warnings.extend(access_warnings)
        
        # Check 5: Reentrancy protection
        reentrancy_warnings = self._check_reentrancy(solidity_code)
        warnings.extend(reentrancy_warnings)
        
        # Check 6: Event emissions
        event_warnings = self._check_events(solidity_code)
        warnings.extend(event_warnings)
        
        is_valid = len(errors) == 0
        
        if self.debug:
            print(f"[Validator] Valid: {is_valid}, Errors: {len(errors)}, Warnings: {len(warnings)}")
        
        return is_valid, errors, warnings
    
    def _check_openzeppelin_v5(self, code: str) -> List[str]:
        """Check for OpenZeppelin v5 incompatibilities"""
        errors = []
        
        # Deprecated hooks
        if "_beforeTokenTransfer" in code:
            errors.append("CRITICAL: _beforeTokenTransfer is deprecated in OZ v5. Use _update override instead.")
        if "_afterTokenTransfer" in code:
            errors.append("CRITICAL: _afterTokenTransfer is deprecated in OZ v5. Use _update override instead.")
        
        # Ownable without initialOwner
        if "is Ownable" in code or ", Ownable" in code:
            # Check if constructor properly initializes Ownable
            if not re.search(r'Ownable\s*\(\s*\w+\s*\)', code):
                errors.append("CRITICAL: Ownable in OZ v5 requires initialOwner parameter in constructor")
        
        # Check for old import paths
        old_security_path = re.search(r'@openzeppelin/contracts/security/', code)
        if old_security_path:
            errors.append("WARNING: OpenZeppelin v5 moved security contracts. Use @openzeppelin/contracts/utils/ instead")
        
        return errors
    
    def _check_constructors(self, code: str) -> List[str]:
        """Check constructor patterns"""
        errors = []
        
        # Find contract declaration
        contract_match = re.search(r'contract\s+(\w+)\s+is\s+([^{]+)\{', code)
        if not contract_match:
            return errors
        
        parents = [p.strip() for p in contract_match.group(2).split(',')]
        
        # Check if constructor exists
        if "constructor" not in code:
            if len(parents) > 0 and parents[0] != '':
                errors.append("WARNING: Contract has parent contracts but no constructor defined")
        else:
            # Check constructor initializes all parents that need it
            constructor_match = re.search(r'constructor[^{]*\{', code, re.DOTALL)
            if constructor_match:
                constructor_sig = constructor_match.group(0)
                
                # Check for required parent initializations
                if "ERC20" in parents and "ERC20(" not in constructor_sig:
                    errors.append("CRITICAL: ERC20 constructor must be initialized with name and symbol")
                
                if "ERC721" in parents and "ERC721(" not in constructor_sig:
                    errors.append("CRITICAL: ERC721 constructor must be initialized with name and symbol")
                
                if "Ownable" in parents and "Ownable(" not in constructor_sig:
                    errors.append("CRITICAL: Ownable constructor must be initialized with initialOwner")
        
        return errors
    
    def _check_access_control(self, code: str) -> List[str]:
        """Check access control patterns"""
        warnings = []
        
        # Check for custom onlyOwner modifier when Ownable is inherited
        if "is Ownable" in code or ", Ownable" in code:
            custom_owner = re.search(r'modifier\s+onlyOwner\s*\(', code)
            if custom_owner:
                warnings.append("WARNING: Custom onlyOwner modifier conflicts with Ownable. Use Ownable's onlyOwner instead.")
        
        # Check for role-based access without AccessControl
        if "ROLE" in code and "AccessControl" not in code:
            warnings.append("INFO: Role constants defined but AccessControl not inherited. Consider using AccessControl.")
        
        return warnings
    
    def _check_reentrancy(self, code: str) -> List[str]:
        """Check for potential reentrancy issues"""
        warnings = []
        
        # Check if contract handles ETH but doesn't use ReentrancyGuard
        if ("payable" in code or "transfer(" in code or "call{value" in code):
            if "ReentrancyGuard" not in code and "nonReentrant" not in code:
                warnings.append("WARNING: Contract handles ETH but doesn't use ReentrancyGuard. Consider adding it.")
        
        return warnings
    
    def _check_events(self, code: str) -> List[str]:
        """Check event usage patterns"""
        warnings = []
        
        # Find all state-changing functions (non-view, non-pure)
        functions = re.finditer(
            r'function\s+(\w+)\s*\([^)]*\)\s+(\w+\s+)*(?!view|pure)(\w+\s+)*\{',
            code
        )
        
        for func in functions:
            func_name = func.group(1)
            # Extract function body (simplified - assumes single level braces)
            start = func.end()
            brace_count = 1
            end = start
            for i, char in enumerate(code[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i
                        break
            
            func_body = code[start:end]
            
            # Check if function modifies state but doesn't emit event
            modifies_state = any(op in func_body for op in ['=', '++', '--', 'delete', 'push', 'pop'])
            has_event = 'emit' in func_body
            
            if modifies_state and not has_event and func_name not in ['constructor', 'receive', 'fallback']:
                warnings.append(f"INFO: Function '{func_name}' modifies state but doesn't emit event. Consider adding one.")
        
        return warnings

def validate_generated_code(solidity_code: str, debug: bool = False) -> Dict:
    """
    Validate generated Solidity code
    Returns dict with validation results
    """
    validator = SolidityValidator(debug=debug)
    is_valid, errors, warnings = validator.validate(solidity_code)
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings)
    }