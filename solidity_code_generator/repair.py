"""Post-processing and self-repair utilities for generated Solidity code.

This module is responsible for turning a raw model completion into a
clean, compilable Solidity source file by:
- stripping Markdown fences
- ensuring SPDX + pragma headers
- optionally running a second-pass "repair" completion that acts like a
  strict compiler/formatter and fixes syntax/import/inheritance issues.
"""

from __future__ import annotations

from typing import Any

from openai import OpenAI


def strip_markdown_fences(solidity_code: str) -> str:
    """Remove common Markdown code fences from the model output."""
    code = solidity_code.strip()
    if code.startswith("```solidity"):
        code = code[len("```solidity") :]
    if code.startswith("```"):
        code = code[len("```") :]
    if code.endswith("```"):
        code = code[: -len("```")]
    return code.strip()


def ensure_headers(solidity_code: str) -> str:
    """Ensure SPDX license and pragma solidity header are present once."""
    code = solidity_code.strip()

    # Normalize line endings
    code = code.replace("\r\n", "\n").replace("\r", "\n")

    has_spdx = "SPDX-License-Identifier" in code
    has_pragma = "pragma solidity" in code

    header_lines = []
    if not has_spdx:
        header_lines.append("// SPDX-License-Identifier: MIT")
    if not has_pragma:
        header_lines.append("pragma solidity ^0.8.20;")

    if header_lines:
        code = "\n".join(header_lines) + "\n" + code

    return code.strip()


def repair_with_model_if_needed(client: OpenAI, solidity_code: str) -> str:
    """Second-pass repair using the model as a strict compiler/formatter.

    The goal is to fix obvious syntax / import / inheritance ordering
    issues without changing the high-level design.
    """

    system = (
        "You are a strict Solidity compiler and formatter. "
        "Given a Solidity contract, you MUST return a version that compiles "
        "under Solidity ^0.8.20 without any syntax errors. Do not redesign "
        "the contract, only fix syntax/ordering/import/inheritance issues. "
        "Output ONLY the fixed Solidity code, with no Markdown fences and no "
        "explanations."
    )

    user = (
        "Here is a Solidity contract that may contain syntax errors. "
        "Return a fixed version that compiles under Solidity ^0.8.20, "
        "preserving the same structure and intent as much as possible.\n\n"
        + solidity_code
    )

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
    )

    fixed = resp.choices[0].message.content or ""
    fixed = strip_markdown_fences(fixed)
    fixed = ensure_headers(fixed)
    return fixed
