# Stage 2 V2 - LLM-Powered Generalized Code Generation

## Overview

Stage 2 V2 uses **LLM-powered classification** instead of hardcoded keyword matching, making it truly generalized for ANY contract type without manual category engineering.

## Key Features

### 1. **LLM Classification** (`llm_classifier.py`)
- Uses GPT-4o to intelligently classify contract types
- Distinguishes between templates (ERC20, Governor) and custom contracts
- Provides confidence scores and reasoning
- No hardcoded keywords - scales to any domain

### 2. **Dynamic Profile Selection** (`profile_selector_v2.py`)
- Builds profiles based on LLM classification
- Sets `is_template` flag automatically
- Determines access control and security features intelligently

### 3. **Simplified Categories** (`categories_v2.py`)
- `ContractProfile` with `is_template` and `subtype` fields
- Works with both template and custom contracts
- Clean, simple structure

### 4. **Smart Coverage Mapping** (`coverage_mapper_v2.py`)
- Maps templates to OpenZeppelin patterns
- Maps custom contracts with semantic understanding
- Handles subtypes (election, certificate, etc.)

### 5. **Dynamic Prompts** (`updated_prompt_builder_v2.py`)
- Template contracts get OpenZeppelin v5 rules
- Custom contracts get custom contract guidance
- Includes automatic actions, data structure rules, etc.

### 6. **Profile-Aware Code Generation** (`code_generator_v2.py`)
- Template contracts: Apply constructor fixes
- Custom contracts: Skip fixes (protect custom logic)
- Uses `is_template` flag to decide

## File Structure

```
stage_2_v2/
├── __init__.py                    # Package exports
├── categories_v2.py               # Simplified categories
├── llm_classifier.py             # LLM classification
├── profile_selector_v2.py         # Dynamic profile selection
├── coverage_mapper_v2.py          # Coverage mapping
├── updated_prompt_builder_v2.py   # Dynamic prompt building
├── code_generator_v2.py           # Profile-aware code generation
├── generator_v2.py                # Main entry point
└── test_v2.py                     # Test runner
```

## Usage

### Basic Usage

```python
from stage_2_v2.generator_v2 import generate_solidity_v2
from stage_1.intent_extraction import extract_intent

user_input = "Create a tax token that charges 3% on every transfer..."

# Stage 1
spec = extract_intent(user_input)

# Stage 2 V2
result = generate_solidity_v2(user_input, spec, debug=True)

# Save results
with open("output.sol", "w") as f:
    f.write(result.solidity_code)
```

### Run Test File

```bash
cd stage_2_v2
python test_v2.py
```

Edit `USER_INPUT` in `test_v2.py` to test different inputs.

## How It Works

### Flow:

1. **LLM Classification**
   - Analyzes user input + JSON spec
   - Classifies as template (ERC20, Governor) or Custom
   - Provides subtype for custom contracts (election, certificate, etc.)

2. **Profile Building**
   - Creates `ContractProfile` with `is_template` flag
   - Determines access control, security features
   - Sets subtype for custom contracts

3. **Coverage Mapping**
   - Templates → OpenZeppelin patterns
   - Custom → Semantic domain patterns

4. **Prompt Building**
   - Templates → OpenZeppelin v5 rules
   - Custom → Custom contract guidance with automatic actions

5. **Code Generation**
   - Templates → Apply constructor fixes
   - Custom → Skip fixes, validate only

## Advantages Over V1

1. **No Hardcoding** - LLM handles classification
2. **Scales to Any Domain** - No need to add new categories manually
3. **Better Accuracy** - LLM understands context, not just keywords
4. **Protected Custom Logic** - Custom contracts aren't modified
5. **Generalized** - Works for any contract type

## Example Classifications

- "Create an ERC20 token" → `ERC20` (template)
- "Election system for club" → `Custom` (subtype: election)
- "Track luxury watch authenticity" → `Custom` (subtype: authentication)
- "DAO governance" → `Governor` (template)
- "Tax token with fees" → `ERC20` (template, with custom transfer logic)

## Integration

The v2 system is self-contained in `stage_2_v2/` folder and can be used independently or integrated into the main pipeline.

## Code Quality Improvements

### Fixed Issues in Generated Code

**1. Data Structure Separation (FIXED)**
- ✅ Now uses separate mappings:
  - `mapping(address => bool) hasVoted` - tracks if voter voted
  - `mapping(address => uint256) candidateVotes` - counts votes per candidate
- ❌ Previously: One `votes` mapping reused for both purposes (caused bugs)

**2. Automatic Tabulation (FIXED)**
- ✅ Check at START of `vote()` function (before main logic)
- ✅ Internal `_autoTabulate()` function
- ⚠️ Note: Manual `declareWinner()` still exists but automatic tabulation works

**3. Prompt Enhancements**
- Added explicit CORRECT vs WRONG examples in prompts
- Enhanced coverage mapper with specific requirements
- Fixed Python f-string syntax issues (escaped braces in Solidity examples)

## Generalized Input Support

### Format
```
"Main description text"

Conditions: Additional requirements and constraints...
```

### How It Works
1. **Stage 1** parses both description and conditions
2. **LLM Classifier** sees full context (original input + parsed spec)
3. **Dynamic Prompts** include all conditions in generation
4. **Code Generation** implements automatic actions correctly

### Example: Election System
- Input with "Conditions: automatically tabulates when period ends"
- Generated code checks at START of `vote()` function
- Uses separate mappings for voter status and vote counts
- Implements automatic tabulation logic

## Supported Generalized Input Types

The system handles all types of generalized inputs from `generalized_inputs.txt`:

### 1. **Election Systems**
- Voter registration and identity verification
- Single vote per verified identity
- Automatic tabulation when voting period ends
- Separate mappings for vote status and vote counts

### 2. **Certificate Verification**
- Educational institution certificate issuance
- Employer verification without contacting issuer
- Access control for institutions and employers
- Admin-only role management

### 3. **Supply Chain Tracking**
- IoT sensor data logging (temperature, location)
- Automatic alerts when conditions violated
- Conditional payment release upon delivery confirmation
- Oracle integration for sensor updates

### 4. **Royalty Distribution**
- Automatic micro-payment distribution
- Oracle integration for usage reporting
- Ownership share tracking (artist, producer, label)
- Pull payment pattern for recipients

### 5. **Authentication/Provenance**
- Immutable ownership history records
- Maintenance record tracking
- Transparent digital title transfer
- Unique ID and origin verification

### 6. **DAO/Governance**
- Token-based voting with automatic execution
- Per-proposal vote tracking
- Quorum and majority checks
- Automatic proposal execution when conditions met

### 7. **Registry Systems**
- Record registration and lookup
- Identity management
- Custom data structures per domain

## Robustness Improvements

### 1. **Robust JSON Parsing** (`llm_utils.py`)
- Safe JSON parser handles markdown fences, extra text, trailing commas
- Retry mechanism with parse-fix prompts if initial parse fails
- JSON Schema validation for classifier outputs

### 2. **Resilient LLM Client** (`llm_utils.py`)
- Wrapper with timeout and retry logic
- Handles `response_format` parameter gracefully (fallback if unsupported)
- Exponential backoff on failures
- Better error messages

### 3. **Fixes Tracking** (`categories_v2.py`, `code_generator_v2.py`)
- `fixes_applied` list tracks all repair attempts
- Records method, attempt number, description
- Included in metadata for auditability

### 4. **Prompt Size Management** (`llm_utils.py`, `updated_prompt_builder_v2.py`)
- Token estimation and size checks
- Automatic spec truncation for very large inputs
- Prevents token limit errors

### 5. **Platform Detection** (`platform_utils.py`)
- Detects Windows/Linux/macOS
- Provides tool availability checks
- Warnings for platform-incompatible tools (Semgrep, Mythril)

### 6. **Enhanced Error Handling**
- Better error messages with context
- Retry logic with different strategies
- Graceful degradation when tools unavailable

## Robustness & Production Features

### Error Handling & Resilience
- **Robust JSON Parsing**: Handles markdown fences, extra text, trailing commas
- **LLM Client Wrapper**: Timeout, retry logic, graceful fallbacks
- **Schema Validation**: Validates and normalizes classifier outputs
- **Retry Logic**: Parse-fix prompts if initial classification fails

### Observability & Debugging
- **Fixes Tracking**: Records all repair attempts in `fixes_applied` field
- **Debug Mode**: Detailed logging at each step
- **Token Estimation**: Warns about large prompts
- **Platform Detection**: Identifies available tools per platform

### Code Quality
- **Type Safety**: Proper type hints throughout
- **Error Messages**: Clear, actionable error messages
- **Modular Design**: Easy to test and extend

## Known Limitations

- Manual `declareWinner()` function still generated (but automatic tabulation also works)
- Some edge cases may need manual review
- Custom contracts skip constructor fixes (by design)
- Oracle integration requires external oracle contract setup
- Windows: Some security tools (Semgrep, Mythril) may not be available (use WSL/Docker)
