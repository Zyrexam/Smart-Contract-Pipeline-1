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
Your job is to read a natural language description of a smart contract
and output a structured JSON object that describes it.

Schema format:
{
  "contract_name": "string",
  "contract_type": "string",
  "description": "string",
  "state_variables": [
    {"name": "string", "type": "string", "visibility": "public|private", "initial_value": "any"}
  ],
  "roles": [
    {"name": "string", "permissions": ["string"]}
  ],
  "functions": [
    {
      "name": "string",
      "visibility": "public|private|internal|external",
      "inputs": [{"name": "string", "type": "string"}],
      "outputs": [{"name": "string", "type": "string"}],
      "restricted_to": "string (role)",
      "description": "string"
    }
  ],
  "events": [
    {"name": "string", "parameters": [{"name": "string", "type": "string"}]}
  ],
  "modifiers": [
    {"name": "string", "condition": "string", "description": "string"}
  ]
}

Rules:
- Always output valid JSON only.
- Leave missing fields empty or as empty arrays.
- Infer reasonable types for Solidity (uint256, address, string, bool, etc.)
- Be specific and complete in your extraction.
"""


def extract_intent(user_input: str) -> dict:
    """
    Extract structured intent from natural language contract description.
    
    Args:
        user_input: Natural language description of the smart contract
    
    Returns:
        dict: Structured JSON specification of the contract
    
    Raises:
        RuntimeError: If the model returns no content
        json.JSONDecodeError: If the output cannot be parsed as JSON
    """
    
    prompt = f"{SCHEMA_PROMPT}\n\nUser input:\n{user_input}"
    
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
    
    # Parse and return JSON
    return json.loads(output_text)


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