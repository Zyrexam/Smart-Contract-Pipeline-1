# solidity_code_generator/constructor_resolver.py

import re
from typing import Dict, List

"""
ConstructorResolver — OpenZeppelin v5 Compatible
===============================================

This resolver fixes the most common LLM mistakes:
- Missing ERC20/ERC721 constructor arguments
- Missing Ownable(msg.sender) (OZ v5)
- Wrong inheritance ordering (Ownable must be last)
- Illegal onlyOwner override removal
- Creating a constructor if not present
- Removing LLM-generated duplicate initializer lists
- NOT initializing base classes that have no constructor
"""

# Parents that *must NOT* appear in initializer list
SKIP_INITIALIZER = {
    "AccessControl",
    "ReentrancyGuard",
    "Pausable",
    "ERC721Burnable",
    "ERC20Burnable",
    "ERC721Enumerable",
    "ERC721URIStorage",
}

# Parents that *require* constructor args in OZ v5
OZ_CONSTRUCTORS = {
    "Ownable": ["msg.sender"],                # OZ v5 requires initialOwner
    "ERC20": ["name", "symbol"],
    "ERC20Capped": ["cap"],
    "ERC721": ["name", "symbol"],
    "ERC1155": ["uri_"],
    "Governor": ["name_"],
    "GovernorSettings": [
        "initial_voting_delay",
        "initial_voting_period",
        "initial_proposal_threshold"
    ],
    "GovernorVotesQuorumFraction": ["quorumPercent"],
}


class ConstructorResolver:

    def __init__(self, debug: bool = False):
        self.debug = debug

    # -------------------------------------------------------------
    # Extract inheritance parents robustly
    # -------------------------------------------------------------
    def _extract_parents(self, code: str) -> List[str]:
        """
        Matches:
        contract X is A, B, C {
        """
        m = re.search(r"contract\s+\w+\s+is\s+([^{]+)\{", code, flags=re.DOTALL)
        if not m:
            return []

        raw_parents = m.group(1)
        parents = [p.strip().strip(",") for p in raw_parents.split(",")]
        parents = [p for p in parents if p]

        return parents

    # -------------------------------------------------------------
    # Build constructor args from JSON spec
    # -------------------------------------------------------------
    def _build_args_for_parent(self, parent: str, json_spec: Dict) -> List[str]:
        if parent == "ERC20":
            name = json_spec.get("token_name", json_spec.get("name", "Token"))
            symbol = json_spec.get("token_symbol", json_spec.get("symbol", "TKN"))
            return [f'"{name}"', f'"{symbol}"']

        if parent == "ERC721":
            name = json_spec.get("nft_name", json_spec.get("name", "NFT"))
            symbol = json_spec.get("nft_symbol", json_spec.get("symbol", "NFT"))
            return [f'"{name}"', f'"{symbol}"']

        if parent == "Ownable":
            return ["msg.sender"]

        if parent == "ERC20Capped":
            cap = json_spec.get("cap") or json_spec.get("token_cap") or json_spec.get("cap_value")
            return [str(cap)] if cap else []

        # fallback: no args
        return []

    # -------------------------------------------------------------
    # Build initializer list string
    # -------------------------------------------------------------
    def _build_initializer_string(self, parents: List[str], json_spec: Dict) -> str:
        initializers = []

        for p in parents:
            # skip parents that have no constructors
            if p in SKIP_INITIALIZER:
                continue

            args = self._build_args_for_parent(p, json_spec)

            # if parent appears in OZ_CONSTRUCTORS but args missing → skip
            # or insert empty parentheses (not recommended)
            if args:
                initializers.append(f"{p}({', '.join(args)})")
            else:
                # only include empty constructor if the parent really has an empty constructor
                if p in OZ_CONSTRUCTORS and len(OZ_CONSTRUCTORS[p]) == 0:
                    initializers.append(f"{p}()")

        return " ".join(initializers)

    # -------------------------------------------------------------
    # Remove any initializer list already inside constructor
    # -------------------------------------------------------------
    def _strip_existing_initializer(self, code: str) -> str:
        """
        Removes everything between constructor(...) and '{'
        Example:
        constructor() ERC20("X","Y") Ownable(msg.sender) {
        becomes:
        constructor() {
        """
        return re.sub(
            r"(constructor\s*\([^)]*\))\s*([^{]*)\{",
            r"\1 {",
            code,
            flags=re.MULTILINE | re.DOTALL
        )

    # -------------------------------------------------------------
    # Insert or replace constructor with correct initializer list
    # -------------------------------------------------------------
    def _insert_or_replace_constructor(self, code: str, initializer: str) -> str:
        # normalize initializer: e.g. "ERC20(...) Ownable(msg.sender)"
        initializer = initializer.strip()

        # Try replacing existing constructor
        pattern = re.compile(
            r"(constructor\s*\([^)]*\))\s*(.*?)\{",
            flags=re.MULTILINE | re.DOTALL
        )
        m = pattern.search(code)

        if m:
            prefix = m.group(1)
            new_ctor = f"{prefix} {initializer} {{"
            return code[:m.start()] + new_ctor + code[m.end():]

        # No constructor -> insert after contract header
        m2 = re.search(r"(contract\s+\w+\s+is\s+[^{]+\{)", code)
        if m2:
            insert_pos = m2.end()
            ctor = (
                f"\n\n    constructor() {initializer} {{\n"
                f"        // auto-generated constructor\n"
                f"    }}\n\n"
            )
            return code[:insert_pos] + ctor + code[insert_pos:]

        return code

    # -------------------------------------------------------------
    # Ensure Ownable is last for inheritance linearization
    # -------------------------------------------------------------
    def _fix_inheritance_order(self, code: str, parents: List[str]) -> str:
        if "Ownable" not in parents:
            return code

        new_order = [p for p in parents if p != "Ownable"] + ["Ownable"]

        return re.sub(
            r"(contract\s+\w+\s+is\s+)([^{]+)\{",
            lambda m: m.group(1) + ", ".join(new_order) + " {",
            code,
            flags=re.DOTALL
        )

    # -------------------------------------------------------------
    # Remove illegal onlyOwner override (OZ v5 forbids user override)
    # -------------------------------------------------------------
    def _remove_illegal_onlyowner_override(self, code: str) -> str:
        # remove explicit user-defined modifier
        code = re.sub(
            r"modifier\s+onlyOwner\s*\([^)]*\)?\s*\{[^}]*\}",
            "// removed illegal onlyOwner override",
            code,
            flags=re.DOTALL
        )
        code = re.sub(
            r"modifier\s+onlyOwner\s*\{[^}]*\}",
            "// removed illegal onlyOwner override",
            code,
            flags=re.DOTALL
        )
        return code

    # -------------------------------------------------------------
    # MAIN PROCESSOR
    # -------------------------------------------------------------
    def process(self, code: str, json_spec: Dict) -> str:

        parents = self._extract_parents(code)
        if self.debug:
            print("[Resolver] Parents:", parents)

        # Step 1: fix inheritance ordering
        code = self._fix_inheritance_order(code, parents)
        # re-extract after modifications
        parents = self._extract_parents(code)

        # Step 2: build initializer list
        initializer = self._build_initializer_string(parents, json_spec)
        if self.debug:
            print("[Resolver] Initializer:", initializer)

        # Step 3: strip any initializer the model may have generated
        code = self._strip_existing_initializer(code)

        # Step 4: insert/replace constructor
        code = self._insert_or_replace_constructor(code, initializer)

        # Step 5: remove illegal onlyOwner overrides
        code = self._remove_illegal_onlyowner_override(code)

        return code
