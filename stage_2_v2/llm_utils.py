"""
LLM Utilities - Robust JSON parsing, client wrapper, and error handling
"""

import json
import re
from typing import Dict, Optional, Any
from openai import OpenAI
import time


def safe_parse_json(text: str, debug: bool = False) -> Dict:
    """
    Safely parse JSON from LLM output, handling markdown fences and extra text.
    
    Args:
        text: Raw text from LLM (may contain markdown, extra text, etc.)
        debug: Enable debug output
    
    Returns:
        Parsed JSON dictionary
    
    Raises:
        ValueError: If no valid JSON found
        json.JSONDecodeError: If JSON is malformed
    """
    if not text:
        raise ValueError("Empty text provided")
    
    # Strip markdown code fences
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    
    if text.endswith("```"):
        text = text[:-3].strip()
    
    # Find first JSON object
    start = text.find("{")
    end = text.rfind("}")
    
    if start == -1 or end == -1 or start >= end:
        if debug:
            print(f"No JSON object found in text: {text[:200]}...")
        raise ValueError("No JSON object found in model output")
    
    json_chunk = text[start:end+1]
    
    # Try to parse
    try:
        return json.loads(json_chunk)
    except json.JSONDecodeError as e:
        # Attempt minor fixes: remove trailing commas, fix quotes
        try:
            # Remove trailing commas before } or ]
            fixed = re.sub(r',(\s*[}\]])', r'\1', json_chunk)
            return json.loads(fixed)
        except json.JSONDecodeError:
            if debug:
                print(f"JSON parse error: {e}")
                print(f"Attempted to parse: {json_chunk[:200]}...")
            raise ValueError(f"Invalid JSON format: {e}")


def call_chat_completion(
    client: OpenAI,
    model: str,
    messages: list,
    timeout: int = 60,
    max_retries: int = 2,
    debug: bool = False,
    **kwargs
) -> Any:
    """
    Resilient wrapper for OpenAI chat completion with timeout and retry logic.
    
    Args:
        client: OpenAI client instance
        model: Model name (e.g., "gpt-4o")
        messages: Chat messages
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        debug: Enable debug output
        **kwargs: Additional arguments for chat.completions.create
    
    Returns:
        Chat completion response
    
    Raises:
        RuntimeError: If all retries fail
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # Try with response_format if provided
            if 'response_format' in kwargs:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        timeout=timeout,
                        **kwargs
                    )
                    return response
                except TypeError:
                    # Fallback: remove response_format if not supported
                    if debug:
                        print(f"Warning: response_format not supported, retrying without it")
                    kwargs_no_format = {k: v for k, v in kwargs.items() if k != 'response_format'}
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        timeout=timeout,
                        **kwargs_no_format
                    )
                    return response
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    timeout=timeout,
                    **kwargs
                )
                return response
                
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                if debug:
                    print(f"LLM call failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                if debug:
                    print(f"All retry attempts failed")
                raise RuntimeError(f"LLM call failed after {max_retries + 1} attempts: {last_error}")
    
    raise RuntimeError(f"LLM call failed: {last_error}")


def validate_classification_schema(result: Dict, debug: bool = False) -> Dict:
    """
    Validate and normalize classification result with JSON Schema-like checks.
    
    Args:
        result: Classification result dictionary
        debug: Enable debug output
    
    Returns:
        Validated and normalized result
    """
    # Required fields
    required_fields = ["contract_type", "confidence", "is_template"]
    
    for field in required_fields:
        if field not in result:
            if debug:
                print(f"Warning: Missing required field '{field}', using default")
            if field == "contract_type":
                result[field] = "Custom"
            elif field == "confidence":
                result[field] = 0.5
            elif field == "is_template":
                result[field] = False
    
    # Validate types
    if not isinstance(result.get("contract_type"), str):
        if debug:
            print(f"Warning: contract_type is not string, defaulting to 'Custom'")
        result["contract_type"] = "Custom"
    
    if not isinstance(result.get("confidence"), (int, float)):
        if debug:
            print(f"Warning: confidence is not number, defaulting to 0.5")
        result["confidence"] = 0.5
    else:
        # Clamp confidence to [0, 1]
        result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
    
    if not isinstance(result.get("is_template"), bool):
        # Infer from contract_type if possible
        template_types = {"ERC20", "ERC721", "ERC1155", "Governor", "Staking", "Vault", "Marketplace", "Auction"}
        result["is_template"] = result.get("contract_type") in template_types
        if debug:
            print(f"Warning: is_template is not boolean, inferred as {result['is_template']}")
    
    # Optional fields with defaults
    if "subtype" not in result:
        result["subtype"] = None
    
    if "reasoning" not in result:
        result["reasoning"] = "Classification completed"
    
    if "recommended_approach" not in result:
        result["recommended_approach"] = "template" if result["is_template"] else "custom"
    
    return result


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (4 chars ≈ 1 token for English).
    
    Args:
        text: Text to estimate
    
    Returns:
        Estimated token count
    """
    return len(text) // 4


def truncate_spec_for_prompt(json_spec: Dict, max_chars: int = 2000) -> Dict:
    """
    Truncate or summarize large JSON spec to fit within token limits.
    
    Args:
        json_spec: Full JSON specification
        max_chars: Maximum characters to keep
    
    Returns:
        Truncated/summarized spec
    """
    import json as json_module
    
    spec_str = json_module.dumps(json_spec, indent=2)
    
    if len(spec_str) <= max_chars:
        return json_spec
    
    # Create summary version
    summary = {
        "contract_name": json_spec.get("contract_name", "Contract"),
        "contract_type": json_spec.get("contract_type", "contract"),
        "description": json_spec.get("description", "")[:500],  # Truncate description
    }
    
    # Keep function/state variable names but truncate descriptions
    if "functions" in json_spec:
        summary["functions"] = []
        for func in json_spec.get("functions", [])[:20]:  # Limit to 20 functions
            summary["functions"].append({
                "name": func.get("name", ""),
                "visibility": func.get("visibility", "public"),
                "description": (func.get("description", "") or "")[:100]  # Truncate
            })
    
    if "state_variables" in json_spec:
        summary["state_variables"] = []
        for var in json_spec.get("state_variables", [])[:20]:  # Limit to 20 vars
            summary["state_variables"].append({
                "name": var.get("name", ""),
                "type": var.get("type", "uint256"),
                "visibility": var.get("visibility", "private")
            })
    
    if "events" in json_spec:
        summary["events"] = json_spec.get("events", [])[:10]  # Limit to 10 events
    
    if "roles" in json_spec:
        summary["roles"] = json_spec.get("roles", [])[:10]  # Limit to 10 roles
    
    return summary
