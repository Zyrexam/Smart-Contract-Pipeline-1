from openai import OpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError(
        "OpenAI API key not found. Set `OPENAI_API_KEY` in a .env file or in your environment."
    )

client = OpenAI(api_key=API_KEY)

# Schema prompt for intent extraction
SCHEMA_PROMPT = """
You are a smart contract intent extractor.
Read a natural language smart contract request and return a compact JSON specification.

The output is used by later pipeline stages, so keep it simple, accurate, and implementation-oriented.
Do not invent unnecessary details.

Schema format:
{
  "contract_name": "string",
  "contract_type": "string",
  "description": "string",
  "name": "string",
  "symbol": "string",
  "roles": [
    {"name": "string", "permissions": ["string"]}
  ],
  "state_variables": [
    {"name": "string", "type": "string", "visibility": "public|private|internal"}
  ],
  "functions": [
    {
      "name": "string",
      "visibility": "public|private|internal|external",
      "inputs": [{"name": "string", "type": "string"}],
      "outputs": [{"name": "string", "type": "string"}],
      "restricted_to": "string",
      "description": "string"
    }
  ],
  "events": [
    {"name": "string", "parameters": [{"name": "string", "type": "string"}]}
  ]
}

Rules:
- Always output valid JSON only.
- Keep only fields that are directly useful for code generation.
- Use empty arrays for missing list fields.
- Use empty strings for unknown scalar fields.
- Infer reasonable Solidity types only when the request clearly suggests them.
- Preserve all important requirements from the prompt, including any "Conditions:" section.
- Prefer 3-8 important functions rather than a long speculative list.
- Do not create modifiers field or extra nested design details.
- If the request is for a token or NFT, fill "name" and "symbol" when they are clearly implied; otherwise leave them empty.
"""


def _normalize_spec(spec: dict, original_input: str) -> dict:
    normalized = {
        "contract_name": spec.get("contract_name") or "GeneratedContract",
        "contract_type": spec.get("contract_type") or "custom_contract",
        "description": spec.get("description") or original_input.strip(),
        "name": spec.get("name") or "",
        "symbol": spec.get("symbol") or "",
        "roles": spec.get("roles") or [],
        "state_variables": spec.get("state_variables") or [],
        "functions": spec.get("functions") or [],
        "events": spec.get("events") or [],
    }

    cleaned_roles = []
    for role in normalized["roles"]:
        if not isinstance(role, dict):
            continue
        cleaned_roles.append(
            {
                "name": role.get("name", ""),
                "permissions": role.get("permissions") or [],
            }
        )
    normalized["roles"] = cleaned_roles

    cleaned_state_vars = []
    for var in normalized["state_variables"]:
        if not isinstance(var, dict):
            continue
        cleaned_state_vars.append(
            {
                "name": var.get("name", ""),
                "type": var.get("type", ""),
                "visibility": var.get("visibility", "") or "private",
            }
        )
    normalized["state_variables"] = cleaned_state_vars

    cleaned_functions = []
    for func in normalized["functions"]:
        if not isinstance(func, dict):
            continue
        cleaned_functions.append(
            {
                "name": func.get("name", ""),
                "visibility": func.get("visibility", "") or "public",
                "inputs": func.get("inputs") or [],
                "outputs": func.get("outputs") or [],
                "restricted_to": func.get("restricted_to", "") or "",
                "description": func.get("description", "") or "",
            }
        )
    normalized["functions"] = cleaned_functions

    cleaned_events = []
    for event in normalized["events"]:
        if not isinstance(event, dict):
            continue
        cleaned_events.append(
            {
                "name": event.get("name", ""),
                "parameters": event.get("parameters") or [],
            }
        )
    normalized["events"] = cleaned_events

    contract_type = normalized["contract_type"].lower()
    description = normalized["description"].lower()

    if not normalized["name"]:
        if "erc20" in contract_type or "token" in contract_type or "token" in description:
            normalized["name"] = normalized["contract_name"]
    if not normalized["symbol"]:
        if "erc20" in contract_type or "token" in contract_type or "token" in description:
            normalized["symbol"] = "TKN"
        elif "erc721" in contract_type or "nft" in contract_type or "nft" in description:
            normalized["symbol"] = "NFT"

    return normalized


def parse_generalized_input(user_input: str) -> str:
    """
    Parse generalized input that may contain description and conditions.
    
    Handles inputs in the format:
    - "Description text"
    - Conditions: Additional requirements...
    
    Args:
        user_input: Raw input string that may contain description and conditions
    
    Returns:
        str: Formatted input combining description and conditions
    """
    # Remove leading/trailing whitespace
    user_input = user_input.strip()
    
    # Check if input contains "Conditions:" marker
    if "Conditions:" in user_input or "conditions:" in user_input:
        # Split by "Conditions:" (case-insensitive)
        parts = user_input.split("Conditions:", 1)
        if len(parts) == 1:
            parts = user_input.split("conditions:", 1)
        
        if len(parts) == 2:
            description = parts[0].strip()
            conditions = parts[1].strip()
            
            # Remove quotes from description if present
            description = description.strip('"').strip("'").strip()
            
            # Format for better LLM understanding
            formatted = f"""Main Description:
{description}

Additional Conditions and Requirements:
{conditions}

Please extract the complete specification incorporating both the main description and all conditions."""
            return formatted
    
    # If no conditions marker, return as-is (but clean up quotes)
    cleaned = user_input.strip('"').strip("'").strip()
    return cleaned


def extract_intent(user_input: str) -> dict:
    """
    Extract structured intent from natural language contract description.
    
    Supports generalized inputs with both description and conditions.
    
    Args:
        user_input: Natural language description of the smart contract
                   (may include main description and "Conditions:" section)
    
    Returns:
        dict: Structured JSON specification of the contract
    
    Raises:
        RuntimeError: If the model returns no content
        json.JSONDecodeError: If the output cannot be parsed as JSON
    """
    # Parse generalized input format
    formatted_input = parse_generalized_input(user_input)
    
    prompt = f"{SCHEMA_PROMPT}\n\nUser input:\n{formatted_input}"
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    
    output_text = response.choices[0].message.content
    
    if output_text is None:
        raise RuntimeError("No content returned by the model in Stage 1")
    
    # Clean markdown code blocks if present
    if output_text.startswith("```json"):
        output_text = output_text.replace("```json", "").replace("```", "").strip()
    elif output_text.startswith("```"):
        output_text = output_text.replace("```", "").strip()
    
    # Parse and normalize JSON
    return _normalize_spec(json.loads(output_text), user_input)


if __name__ == "__main__":
    # Simple test when run directly
    test_input = """
    A token contract that locks transferred tokens for 30 days before they become spendable.
    """
    
    print("Testing Stage 1: Intent Extraction")
    print("=" * 60)
    print(f"Input: {test_input.strip()}")
    print()
    
    try:
        result = extract_intent(test_input)
        print("Output:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
