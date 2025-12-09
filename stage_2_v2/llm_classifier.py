
"""
LLM-Powered Contract Classification System

Instead of hardcoded regex/keyword matching, we use the LLM to intelligently
classify what type of smart contract the user wants to build.

This scales to ANY domain without manual category engineering.
"""

import os
import json
from typing import Dict, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from .llm_utils import safe_parse_json, call_chat_completion, validate_classification_schema

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("OpenAI API key not found")

client = OpenAI(api_key=API_KEY)

# Known template types where we have optimized patterns
TEMPLATE_TYPES = {
    "ERC20": "Standard fungible token (ERC20)",
    "ERC721": "Non-fungible token / NFT (ERC721)",
    "ERC1155": "Multi-token standard (ERC1155)",
    "Governor": "DAO governance with proposals and voting",
    "Staking": "Token staking with rewards",
    "Vault": "Asset vault / ERC4626",
    "Marketplace": "NFT marketplace with listings",
    "Auction": "Auction system with bidding",
    "Timelock": "Time-delayed execution",
    "MultiSig": "Multi-signature wallet",
}

CLASSIFICATION_PROMPT = """You are an expert smart contract architect. Your task is to classify what type of smart contract the user wants to build.

AVAILABLE TEMPLATE TYPES (use these if applicable):
- ERC20: Standard fungible token
- ERC721: Non-fungible token / NFT
- ERC1155: Multi-token standard
- Governor: DAO governance system with proposals/voting
- Staking: Token staking with rewards
- Vault: Asset vault (ERC4626)
- Marketplace: NFT marketplace
- Auction: Auction system
- Timelock: Time-delayed execution
- MultiSig: Multi-signature wallet

IMPORTANT DISTINCTIONS:
- "Governor" = Full DAO governance with proposals, voting power, quorum, execution
- "Election" = Simple community voting (candidates, one vote per person, winner declaration)
- These are DIFFERENT! An election is NOT a Governor.

CLASSIFICATION RULES:
1. Use a TEMPLATE TYPE if the contract closely matches a known standard
2. Use "Custom" for unique business logic that doesn't fit templates
3. Be specific: "Election" is Custom, not Governor
4. Consider the core functionality, not surface keywords

EXAMPLES:
- "Create an ERC20 token" → ERC20
- "Build a DAO with governance" → Governor  
- "Community election for club president" → Custom (election system)
- "Track product authenticity" → Custom (provenance tracking)
- "Manage digital certificates" → Custom (certificate registry)
- "NFT marketplace" → Marketplace
- "Staking rewards for token holders" → Staking

OUTPUT FORMAT (JSON only):
{
  "contract_type": "ERC20" | "ERC721" | "Governor" | "Custom",
  "subtype": "election" | "certificate" | "supply_chain" | null,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of classification",
  "is_template": true | false,
  "recommended_approach": "template" | "custom"
}

RULES:
- is_template=true ONLY for ERC20, ERC721, ERC1155, Governor, Staking, Vault, Marketplace, Auction
- is_template=false for everything else (elections, certificates, registries, etc.)
- subtype is ONLY used when contract_type="Custom" to help with generation
- confidence > 0.8 means high certainty
- confidence < 0.6 means uncertain, default to Custom

Be precise. Better to say "Custom" than force-fit into wrong template.
"""


class ContractClassifier:
    """LLM-powered contract classification"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.client = client
    
    def classify(self, user_input: str, json_spec: Optional[Dict] = None) -> Dict:
        """
        Classify the contract type using LLM intelligence.
        
        Args:
            user_input: Original natural language input
            json_spec: Optional JSON specification from Stage 1
        
        Returns:
            Classification result with type, confidence, and reasoning
        """
        
        # Build context from both user input and spec
        context = self._build_classification_context(user_input, json_spec)
        
        if self.debug:
            print("\n" + "="*80)
            print("CONTRACT CLASSIFICATION")
            print("="*80)
            print(f"Context length: {len(context)} chars")
        
        # Call LLM for classification with resilient wrapper
        try:
            response = call_chat_completion(
                client=self.client,
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": CLASSIFICATION_PROMPT},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,  # Low temperature for consistent classification
                response_format={"type": "json_object"},
                timeout=30,
                max_retries=2,
                debug=self.debug
            )
        except Exception as e:
            if self.debug:
                print(f"LLM call failed: {e}")
            raise RuntimeError(f"Failed to get classification from LLM: {e}")
        
        result_text = response.choices[0].message.content
        
        if not result_text:
            raise RuntimeError("No classification result from LLM")
        
        # Parse result with robust parser
        try:
            result = safe_parse_json(result_text, debug=self.debug)
        except (ValueError, json.JSONDecodeError) as e:
            if self.debug:
                print(f"Failed to parse JSON: {result_text[:200]}...")
                print(f"Error: {e}")
            # Retry with a parse-fix prompt
            try:
                result = self._retry_with_parse_prompt(context, result_text)
            except Exception as retry_error:
                if self.debug:
                    print(f"Retry also failed: {retry_error}")
                raise RuntimeError(f"Invalid JSON from classifier after retry: {e}")
        
        # Validate and normalize result with schema validation
        result = validate_classification_schema(result, debug=self.debug)
        result = self._validate_classification(result)
        
        if self.debug:
            print(f"\nClassification Result:")
            print(f"  Type: {result['contract_type']}")
            print(f"  Subtype: {result.get('subtype', 'N/A')}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Is Template: {result['is_template']}")
            print(f"  Approach: {result['recommended_approach']}")
            print(f"  Reasoning: {result['reasoning']}")
            print("="*80 + "\n")
        
        return result
    
    def _build_classification_context(self, user_input: str, json_spec: Optional[Dict]) -> str:
        """Build rich context for classification"""
        
        context_parts = [
            "USER REQUEST:",
            user_input,
            ""
        ]
        
        if json_spec:
            context_parts.extend([
                "EXTRACTED SPECIFICATION:",
                f"Contract Name: {json_spec.get('contract_name', 'N/A')}",
                f"Description: {json_spec.get('description', 'N/A')}",
                ""
            ])
            
            # Add function names if available
            functions = json_spec.get('functions', [])
            if functions:
                func_names = [f.get('name', '') for f in functions]
                context_parts.append(f"Functions: {', '.join(func_names)}")
                context_parts.append("")
            
            # Add state variables if available
            state_vars = json_spec.get('state_variables', [])
            if state_vars:
                var_names = [v.get('name', '') for v in state_vars]
                context_parts.append(f"State Variables: {', '.join(var_names)}")
                context_parts.append("")
            
            # Add roles if available
            roles = json_spec.get('roles', [])
            if roles:
                role_names = [r.get('name', '') for r in roles]
                context_parts.append(f"Roles: {', '.join(role_names)}")
                context_parts.append("")
        
        context_parts.append("Classify this contract:")
        
        return "\n".join(context_parts)
    
    def _validate_classification(self, result: Dict) -> Dict:
        """Validate and normalize classification result"""
        
        # Ensure required fields
        required_fields = ['contract_type', 'confidence', 'is_template', 'recommended_approach']
        for field in required_fields:
            if field not in result:
                # Set defaults
                if field == 'confidence':
                    result[field] = 0.5
                elif field == 'is_template':
                    result[field] = result['contract_type'] in TEMPLATE_TYPES
                elif field == 'recommended_approach':
                    result[field] = 'template' if result.get('is_template') else 'custom'
        
        # Validate confidence range
        result['confidence'] = max(0.0, min(1.0, result['confidence']))
        
        # Ensure is_template matches contract_type
        if result['contract_type'] not in TEMPLATE_TYPES and result['contract_type'] != 'Custom':
            # Unknown type, force to custom
            result['contract_type'] = 'Custom'
            result['is_template'] = False
            result['recommended_approach'] = 'custom'
        
        # Set subtype to None if not provided or empty
        if 'subtype' not in result or not result['subtype']:
            result['subtype'] = None
        
        # Add reasoning if missing
        if 'reasoning' not in result:
            result['reasoning'] = f"Classified as {result['contract_type']}"
        
        return result


def classify_contract(user_input: str, json_spec: Optional[Dict] = None, debug: bool = False) -> Dict:
    """
    Convenience function for contract classification.
    
    Args:
        user_input: Original user input
        json_spec: Optional JSON spec from Stage 1
        debug: Enable debug output
    
    Returns:
        Classification dict with type, confidence, reasoning
    """
    classifier = ContractClassifier(debug=debug)
    return classifier.classify(user_input, json_spec)


# Quick test
if __name__ == "__main__":
    test_inputs = [
        "Create an ERC20 token for my project",
        "Build a simple election system for a community club",
        "NFT marketplace with royalties",
        "Track luxury watch authenticity and ownership",
    ]
    
    print("Testing Contract Classifier")
    print("="*80)
    
    for inp in test_inputs:
        result = classify_contract(inp, debug=True)
        print(f"\nInput: {inp}")
        print(f"→ Type: {result['contract_type']}")
        print(f"→ Template: {result['is_template']}")
        print("-"*80)
