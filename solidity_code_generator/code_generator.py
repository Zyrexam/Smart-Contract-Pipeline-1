"""Low-level Solidity code generation using the OpenAI API.

This module is intentionally small: it just sends the prompts, receives
Solidity code, and runs the post-processing / repair helpers.
"""

from __future__ import annotations

import os
from typing import Tuple

from dotenv import load_dotenv
from openai import OpenAI

from .repair import strip_markdown_fences, ensure_headers, repair_with_model_if_needed

load_dotenv()

_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
if not _API_KEY:
    raise RuntimeError(
        "OpenAI API key not found. Set OPENAI_API_KEY or API_KEY in your environment/.env."
    )

_client = OpenAI(api_key=_API_KEY)


def generate_solidity_code(system_prompt: str, user_prompt: str) -> str:
    """Call the model and return cleaned + repaired Solidity source code."""

    response = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    solidity_code = response.choices[0].message.content
    if not solidity_code:
        raise RuntimeError("No content returned from model in Stage 2")

    # First-pass cleanup
    solidity_code = strip_markdown_fences(solidity_code)
    solidity_code = ensure_headers(solidity_code)

    # Second-pass repair
    solidity_code = repair_with_model_if_needed(_client, solidity_code)

    return solidity_code
