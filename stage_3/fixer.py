"""
Security Fixer
==============

LLM-based vulnerability fixer with Stage 2 metadata integration
"""

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .models import SecurityIssue

load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")) if os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") else None


class SecurityFixer:
    """LLM-based vulnerability fixer"""
    
    def __init__(self, model: str = "gpt-4o"):
        """Initialize fixer"""
        self.model = model
        self.client = _client
        if not self.client:
            print("  ⚠️  OpenAI API key not found. LLM fixes will be disabled.")
    
    def fix_issues(
        self,
        solidity_code: str,
        issues: List[SecurityIssue],
        contract_name: str,
        stage2_metadata: Optional[Dict] = None,
        iteration: int = 1
    ) -> str:
        """Generate fixed code using LLM"""
        if not issues:
            return solidity_code
        
        if not self.client:
            print(f"  ⚠️  Skipping LLM fix (no API key)")
            return solidity_code
        
        print(f"\n  🔧 Iteration {iteration}: Fixing {len(issues)} issues")
        
        metadata_context = self._build_metadata_context(stage2_metadata)
        issues_text = self._format_issues(issues)
        
        system_prompt = self._build_system_prompt(metadata_context)
        user_prompt = self._build_user_prompt(
            solidity_code, issues_text, contract_name, metadata_context
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            fixed_code = response.choices[0].message.content or ""
            fixed_code = self._clean_code(fixed_code)
            
            print(f"  ✓ Fixes generated")
            return fixed_code
        
        except Exception as e:
            print(f"  ✗ Fix failed: {e}")
            return solidity_code
    
    def _build_metadata_context(self, metadata: Optional[Dict]) -> str:
        """Build context from Stage 2 metadata"""
        if not metadata:
            return ""
        
        context_parts = []
        if metadata.get("base_standard"):
            context_parts.append(f"Base Standard: {metadata['base_standard']}")
        if metadata.get("category"):
            context_parts.append(f"Category: {metadata['category']}")
        if metadata.get("access_control"):
            context_parts.append(f"Access Control: {metadata['access_control']}")
        if metadata.get("security_features"):
            features = ", ".join(metadata["security_features"])
            context_parts.append(f"Security Features: {features}")
        if metadata.get("inheritance_chain"):
            chain = " -> ".join(metadata["inheritance_chain"])
            context_parts.append(f"Inheritance: {chain}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _format_issues(self, issues: List[SecurityIssue]) -> str:
        """Format issues for LLM prompt"""
        lines = []
        for i, issue in enumerate(issues, 1):
            line_info = f"Line {issue.line}" if issue.line else "Unknown location"
            if issue.line_end and issue.line_end != issue.line:
                line_info = f"Lines {issue.line}-{issue.line_end}"
            
            lines.append(
                f"{i}. [{issue.severity.value}] {issue.title}\n"
                f"   Tool: {issue.tool}\n"
                f"   Location: {line_info}\n"
                f"   Description: {issue.description}\n"
                f"   Recommendation: {issue.recommendation or 'Apply security best practices'}\n"
            )
        return "\n".join(lines)
    
    def _build_system_prompt(self, metadata_context: str) -> str:
        """Build system prompt"""
        base = """You are a Solidity security expert. Fix vulnerabilities while:
1. Preserving all functionality and public API
2. Maintaining OpenZeppelin v5 compatibility (^0.8.20)
3. Not introducing new bugs
4. Following the contract's existing architecture

COMMON FIXES:
- Reentrancy: Add ReentrancyGuard, use checks-effects-interactions
- Access Control: Add onlyOwner or AccessControl modifiers
- Unchecked Calls: Check return values, use SafeERC20
- Integer Issues: Use ^0.8.20 built-in checks
- tx.origin: Replace with msg.sender

Return ONLY the fixed Solidity code (no markdown, no explanations)."""
        
        if metadata_context:
            base += f"\n\nCONTRACT CONTEXT:\n{metadata_context}"
        
        return base
    
    def _build_user_prompt(
        self, code: str, issues_text: str, contract_name: str, metadata_context: str
    ) -> str:
        """Build user prompt"""
        prompt = f"Fix these security issues:\n\nCONTRACT: {contract_name}\n\n"
        if metadata_context:
            prompt += f"CONTEXT:\n{metadata_context}\n\n"
        prompt += f"CODE:\n{code}\n\nISSUES TO FIX:\n{issues_text}\n\nFix all CRITICAL and HIGH issues. Return complete fixed contract."
        return prompt
    
    def _clean_code(self, code: str) -> str:
        """Clean LLM output"""
        code = code.strip()
        if code.startswith("```solidity"):
            code = code[11:].strip()
        elif code.startswith("```"):
            code = code[3:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()
        
        if "// SPDX-License-Identifier" not in code:
            code = "// SPDX-License-Identifier: MIT\n" + code
        if "pragma solidity" not in code:
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("// SPDX"):
                    lines.insert(i + 1, "pragma solidity ^0.8.20;")
                    break
            code = '\n'.join(lines)
        
        return code

