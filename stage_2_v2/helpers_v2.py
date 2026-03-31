import re
from typing import Dict, List, Tuple


def strip_markdown_fences(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```solidity"):
        text = text[len("```solidity"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def ensure_headers(code: str) -> str:
    code = (code or "").strip()
    if "SPDX-License-Identifier" not in code:
        code = "// SPDX-License-Identifier: MIT\n" + code
    if "pragma solidity" not in code:
        lines = code.splitlines()
        insert_at = 1 if lines and "SPDX-License-Identifier" in lines[0] else 0
        lines.insert(insert_at, "pragma solidity ^0.8.20;")
        code = "\n".join(lines)
    return code


def repair_with_model_if_needed(_client, code: str) -> str:
    return code


class ConstructorResolver:
    def __init__(self, debug: bool = False):
        self.debug = debug

    def _extract_parents(self, code: str) -> List[str]:
        match = re.search(r"contract\s+\w+\s+is\s+([^{]+)\{", code, flags=re.DOTALL)
        if not match:
            return []
        return [parent.strip().strip(",") for parent in match.group(1).split(",") if parent.strip()]

    def _build_initializer_string(self, parents: List[str], spec: Dict) -> str:
        initializers = []
        if "ERC20" in parents:
            initializers.append(f'ERC20("{spec.get("token_name", spec.get("name", "Token"))}", "{spec.get("token_symbol", spec.get("symbol", "TKN"))}")')
        if "ERC721" in parents or any(parent in {"ERC721Enumerable", "ERC721URIStorage"} for parent in parents):
            initializers.append(f'ERC721("{spec.get("nft_name", spec.get("name", "NFT"))}", "{spec.get("nft_symbol", spec.get("symbol", "NFT"))}")')
        if "Ownable" in parents:
            initializers.append("Ownable(msg.sender)")
        return " ".join(dict.fromkeys(initializers))

    def _strip_existing_initializer(self, code: str) -> str:
        return re.sub(r"(constructor\s*\([^)]*\))\s*([^{]*)\{", r"\1 {", code, flags=re.MULTILINE | re.DOTALL)

    def _insert_or_replace_constructor(self, code: str, initializer: str) -> str:
        if not initializer:
            return code

        constructor_pattern = re.compile(r"(constructor\s*\([^)]*\))\s*(.*?)\{", flags=re.MULTILINE | re.DOTALL)
        match = constructor_pattern.search(code)
        if match:
            replacement = f"{match.group(1)} {initializer} {{"
            return code[:match.start()] + replacement + code[match.end():]

        contract_match = re.search(r"(contract\s+\w+\s+is\s+[^{]+\{)", code)
        if not contract_match:
            return code

        constructor_code = f"\n\n    constructor() {initializer} {{\n    }}\n"
        return code[:contract_match.end()] + constructor_code + code[contract_match.end():]

    def process(self, code: str, spec: Dict) -> str:
        parents = self._extract_parents(code)
        if not parents:
            return code
        code = self._strip_existing_initializer(code)
        initializer = self._build_initializer_string(parents, spec)
        return self._insert_or_replace_constructor(code, initializer)


class SolidityValidator:
    def __init__(self, debug: bool = False):
        self.debug = debug

    def validate(self, solidity_code: str) -> Tuple[bool, List[str], List[str]]:
        errors: List[str] = []
        warnings: List[str] = []

        if "SPDX-License-Identifier" not in solidity_code:
            errors.append("Missing SPDX license identifier")
        if "pragma solidity" not in solidity_code:
            errors.append("Missing pragma statement")
        if "_beforeTokenTransfer" in solidity_code or "_afterTokenTransfer" in solidity_code:
            errors.append("CRITICAL: OpenZeppelin v5 deprecated token transfer hooks are still used")
        if ("is Ownable" in solidity_code or ", Ownable" in solidity_code) and "Ownable(" not in solidity_code:
            errors.append("CRITICAL: Ownable constructor must be initialized with initialOwner")
        if "@openzeppelin/contracts/security/" in solidity_code:
            warnings.append("WARNING: OpenZeppelin v5 moved security contracts to utils/")
        if ("payable" in solidity_code or "transfer(" in solidity_code or "call{value" in solidity_code) and "ReentrancyGuard" not in solidity_code:
            warnings.append("WARNING: Contract handles ETH but doesn't use ReentrancyGuard. Consider adding it.")

        return len(errors) == 0, errors, warnings


def validate_generated_code(solidity_code: str, debug: bool = False) -> Dict:
    validator = SolidityValidator(debug=debug)
    is_valid, errors, warnings = validator.validate(solidity_code)
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def validate_semantics(solidity_code: str, spec: Dict, debug: bool = False) -> Dict:
    errors: List[str] = []
    warnings: List[str] = []

    required_functions = [f.get("name", "") for f in spec.get("functions", []) if f.get("name")]
    missing = [name for name in required_functions if f"function {name}" not in solidity_code]
    if missing:
        errors.append(f"Missing specified functions: {', '.join(missing[:5])}")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def repair_semantic_issues(_client, solidity_code: str, _errors: List[str], _spec: Dict, debug: bool = False) -> str:
    return solidity_code
