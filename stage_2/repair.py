# solidity_code_generator/repair.py
from openai import OpenAI
import re

def strip_markdown_fences(solidity_code: str) -> str:
    code = solidity_code.strip()
    if code.startswith("```solidity"):
        code = code[len("```solidity"):]
    if code.startswith("```"):
        code = code[len("```"):]
    if code.endswith("```"):
        code = code[:-len("```")]
    return code.strip()

def ensure_headers(solidity_code: str) -> str:
    code = solidity_code.strip()
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    has_spdx = "SPDX-License-Identifier" in code
    has_pragma = "pragma solidity" in code
    header_lines = []
    if not has_spdx:
        header_lines.append("// SPDX-License-Identifier: MIT")
    if not has_pragma:
        header_lines.append("pragma solidity ^0.8.20;")
    if header_lines:
        code = "\n".join(header_lines) + "\n\n" + code
    return code.strip() + "\n"

def detect_openzeppelin_version_issues(solidity_code: str) -> list:
    """Detect common OpenZeppelin v5 migration issues"""
    issues = []
    
    # Check for deprecated hooks
    if "_beforeTokenTransfer" in solidity_code or "_afterTokenTransfer" in solidity_code:
        issues.append("deprecated_hooks")
    
    # Check for Ownable without initialOwner
    if "Ownable" in solidity_code and "constructor" in solidity_code:
        # Check if constructor doesn't pass initialOwner to Ownable
        if "Ownable(" not in solidity_code and "is Ownable" in solidity_code:
            issues.append("ownable_constructor")
    
    # Check for safeTransferFrom without data parameter in ERC721
    if "ERC721" in solidity_code and "safeTransferFrom" in solidity_code:
        issues.append("check_erc721_compatibility")
    
    return issues

def apply_openzeppelin_v5_fixes(solidity_code: str) -> str:
    """Apply automatic fixes for OpenZeppelin v5 compatibility"""
    code = solidity_code
    
    # Fix 1: Replace _beforeTokenTransfer with _update
    if "_beforeTokenTransfer" in code or "_afterTokenTransfer" in code:
        # This is complex - let model handle it
        return code
    
    # Fix 2: Add msg.sender to Ownable constructor calls
    # Pattern: Ownable() -> Ownable(msg.sender)
    code = re.sub(
        r'\bOwnable\(\s*\)',
        'Ownable(msg.sender)',
        code
    )
    
    # Fix 3: Ensure Ownable constructor has initialOwner parameter
    # Look for: constructor(...) Ownable(...)
    # This is complex, better handled by model
    
    return code

def repair_with_model_if_needed(client: OpenAI, solidity_code: str) -> str:
    """Enhanced repair with OpenZeppelin v5 awareness"""
    
    # Detect issues first
    issues = detect_openzeppelin_version_issues(solidity_code)
    
    if not issues:
        # No detected issues, do basic repair
        return basic_model_repair(client, solidity_code)
    
    # Build issue-specific prompt
    issue_descriptions = {
        "deprecated_hooks": "The code uses deprecated _beforeTokenTransfer or _afterTokenTransfer hooks. In OpenZeppelin v5, these must be replaced with the _update function override.",
        "ownable_constructor": "The Ownable contract in OpenZeppelin v5 requires an initialOwner parameter in its constructor.",
        "check_erc721_compatibility": "Verify ERC721 compatibility with OpenZeppelin v5."
    }
    
    issues_text = "\n".join([f"- {issue_descriptions.get(issue, issue)}" for issue in issues])
    
    system = """You are an expert Solidity compiler and OpenZeppelin v5 migration specialist.

CRITICAL REQUIREMENTS:
1. Output ONLY valid Solidity code that compiles under ^0.8.20
2. Use OpenZeppelin v5 patterns:
   - Replace _beforeTokenTransfer/_afterTokenTransfer with _update override
   - Ownable requires initialOwner parameter in constructor
   - Use AccessControl for role-based permissions
   - Custom errors instead of require strings
3. Fix ONLY syntax/import/inheritance/constructor issues
4. Do NOT redesign contract logic
5. Preserve all custom functions and business logic
6. Output ONLY Solidity code, no explanations"""

    user = f"""Fix the following OpenZeppelin v5 compatibility issues in this Solidity contract:

DETECTED ISSUES:
{issues_text}

SOLIDITY CODE:
{solidity_code}

Return the corrected version that compiles under Solidity ^0.8.20 with OpenZeppelin v5."""

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.0,
    )
    
    fixed = resp.choices[0].message.content or ""
    fixed = strip_markdown_fences(fixed)
    fixed = ensure_headers(fixed)
    
    return fixed

def basic_model_repair(client: OpenAI, solidity_code: str) -> str:
    """Basic repair without specific issue targeting"""
    system = (
        "You are a strict Solidity compiler and formatter. Given a Solidity contract, "
        "return a version that compiles under Solidity ^0.8.20 with OpenZeppelin v5. "
        "Fix ONLY syntax/import/inheritance/constructor issues. "
        "Do not redesign logic. Output ONLY Solidity code."
    )
    user = "Here is a Solidity contract that may contain syntax issues. Return a fixed version that compiles under ^0.8.20:\n\n" + solidity_code
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.0,
    )
    
    fixed = resp.choices[0].message.content or ""
    fixed = strip_markdown_fences(fixed)
    fixed = ensure_headers(fixed)
    
    return fixed