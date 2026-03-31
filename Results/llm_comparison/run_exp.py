import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from run_pipeline import run_full_pipeline
from stage_2_v2.helpers_v2 import validate_generated_code
from stage_3 import run_stage3
from stage_3.models import Severity

load_dotenv()

DATASET_PATH = BASE_DIR / "dataset.json"
RESULTS_PATH = BASE_DIR / "llm_results.json"
OUTPUTS_DIR = BASE_DIR / "outputs"

STAGE3_TOOLS = ["slither", "mythril", "semgrep", "solhint"]
PIPELINE_STAGE3_OPTIONS = {
    "enable_stage3": True,
    "skip_auto_fix": True,
    "max_iterations": 1,
    "verbose": False,
}

DEFAULT_MODELS = ["pipeline", "gpt", "grok","codellama", "gemma", "mistral", "llama2"]
# DEFAULT_MODELS = ["codegemma"]




OLLAMA_MODELS = {
    "codegemma": "codegemma:2b",
    "codellama": "codellama:latest",
    "gemma": "gemma:2b",
    "mistral": "mistral:latest",
    "llama2": "llama2:latest",
}


def load_dataset():
    with open(DATASET_PATH, encoding="utf-8") as file:
        return json.load(file)


def parse_index_list(values: list[str] | None) -> list[int] | None:
    if not values:
        return None

    indexes = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                index = int(part)
            except ValueError as exc:
                raise ValueError(f"Invalid dataset index: {part}") from exc
            if index <= 0:
                raise ValueError(f"Dataset indexes must be 1-based positive integers, got: {index}")
            indexes.append(index)
    return indexes


def select_dataset_items(dataset: list[dict], limit: int | None, indexes: list[int] | None) -> list[dict]:
    if indexes:
        selected_items = []
        seen = set()

        for index in indexes:
            dataset_pos = index - 1
            if dataset_pos >= len(dataset):
                raise ValueError(
                    f"Dataset index {index} is out of range. Dataset contains {len(dataset)} items."
                )
            if index in seen:
                continue
            selected_items.append(dataset[dataset_pos])
            seen.add(index)

        return selected_items

    if limit:
        return dataset[:limit]

    return dataset


def ensure_dirs():
    OUTPUTS_DIR.mkdir(exist_ok=True)


def strip_code_fences(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```solidity"):
        text = text[len("```solidity"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def extract_solidity_code(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    block_match = re.search(r"```(?:solidity)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if block_match:
        text = block_match.group(1).strip()

    start_indexes = []
    for marker in ["// SPDX-License-Identifier", "pragma solidity", "contract "]:
        idx = text.find(marker)
        if idx != -1:
            start_indexes.append(idx)
    if start_indexes:
        text = text[min(start_indexes):]

    last_brace = text.rfind("}")
    if last_brace != -1:
        text = text[: last_brace + 1]

    return text.strip()


def is_probably_valid_solidity(code: str) -> tuple[bool, list[str]]:
    reasons = []
    if "pragma solidity" not in code:
        reasons.append("missing pragma solidity")
    if "contract " not in code:
        reasons.append("missing contract declaration")
    if count_functions(code) == 0:
        reasons.append("no functions detected")
    return len(reasons) == 0, reasons


def count_non_empty_lines(code: str) -> int:
    return sum(1 for line in code.splitlines() if line.strip())


def count_functions(code: str) -> int:
    return len(re.findall(r"\bfunction\s+\w+\s*\(", code))


def summarize_analysis(analysis_result):
    if not analysis_result:
        return {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
            "total": 0,
        }

    return {
        "critical": len(analysis_result.get_by_severity(Severity.CRITICAL)),
        "high": len(analysis_result.get_by_severity(Severity.HIGH)),
        "medium": len(analysis_result.get_by_severity(Severity.MEDIUM)),
        "low": len(analysis_result.get_by_severity(Severity.LOW)),
        "info": len(analysis_result.get_by_severity(Severity.INFO)),
        "total": len(analysis_result.issues),
    }


def build_common_metrics(code: str):
    validation = validate_generated_code(code, debug=False)
    return {
        "loc": count_non_empty_lines(code),
        "function_count": count_functions(code),
        "validation_success": validation["is_valid"],
        "validation_errors": validation["errors"],
        "validation_warnings": validation["warnings"],
        "compilation_success": None,
    }


def build_generation_prompt(user_prompt: str) -> str:
    return f"""Generate a complete Solidity smart contract for the following request.

User request:
{user_prompt}

Rules:
- Return only Solidity code
- Include SPDX license identifier
- Include pragma solidity ^0.8.20;
- Produce one complete contract file
- Do not include markdown fences
"""


EXAMPLE_CONTRACT = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SimpleStorage {
    uint256 private storedValue;

    function set(uint256 _value) public {
        storedValue = _value;
    }

    function get() public view returns (uint256) {
        return storedValue;
    }
}
"""


def build_local_generation_prompt(user_prompt: str) -> str:
    return f"""Write a Solidity smart contract for: {user_prompt}

IMPORTANT: Output ONLY valid Solidity code. No explanations. No markdown.

Start your response EXACTLY like this example:
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

Example contract format:
{EXAMPLE_CONTRACT}

Now write the contract for: {user_prompt}"""


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def call_openai_compatible(model_name: str, api_key: str, model: str, base_url: str | None, prompt: str) -> str:
    if not api_key:
        raise RuntimeError(f"{model_name} API key not found")

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    client = OpenAI(**client_kwargs)
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You are an expert Solidity developer. Return only Solidity code.",
            },
            {
                "role": "user",
                "content": build_generation_prompt(prompt),
            },
        ],
    )
    return extract_solidity_code(strip_code_fences(response.choices[0].message.content or ""))


def call_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    if not api_key:
        raise RuntimeError("Groq API key not found")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You are an expert Solidity developer. Return only Solidity code.",
            },
            {
                "role": "user",
                "content": build_generation_prompt(prompt),
            },
        ],
    )
    return extract_solidity_code(strip_code_fences(response.choices[0].message.content or ""))


def call_ollama(model: str, prompt: str) -> str:
    url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You write Solidity contracts. Reply with code only.",
            },
            {
                "role": "user",
                "content": build_local_generation_prompt(prompt),
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 1200,
        },
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Ollama API error: {exc.code} {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama is not reachable at {url}: {exc}") from exc

    message = data.get("message", {})
    text = message.get("content", "")
    if not text:
        raise RuntimeError(f"Ollama returned no code for model {model}")
    return extract_solidity_code(strip_code_fences(text))


def generate_contract(model_name: str, prompt: str) -> str:
    if model_name == "gpt":
        return call_openai_compatible(
            model_name="GPT",
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            prompt=prompt,
        )

    if model_name == "grok":
        return call_groq(prompt)

    if model_name in OLLAMA_MODELS:
        return call_ollama(OLLAMA_MODELS[model_name], prompt)

    raise ValueError(f"Unsupported model: {model_name}")


def run_stage3_for_code(code: str, task_name: str, output_dir: Path):
    contract_path = output_dir / "generated.sol"
    report_path = output_dir / "stage3_report.json"

    save_text(contract_path, code)

    stage3_result = run_stage3(
        solidity_code=code,
        contract_name=task_name.replace(" ", ""),
        stage2_metadata=None,
        max_iterations=1,
        tools=STAGE3_TOOLS,
        skip_auto_fix=True,
    )

    save_json(report_path, stage3_result.to_dict())
    return contract_path, report_path, stage3_result


def run_pipeline_item(item):
    start = time.perf_counter()
    prompt = item["prompt"]

    try:
        result = run_full_pipeline(prompt, PIPELINE_STAGE3_OPTIONS)
        runtime = time.perf_counter() - start

        if not result:
            return {
                "id": item["id"],
                "task_name": item["task_name"],
                "category": item["category"],
                "prompt": prompt,
                "method": "pipeline",
                "status": "failed",
                "runtime_seconds": runtime,
            }

        code = result["stage2_result"].solidity_code
        analysis_result = result["stage3_result"].initial_analysis if result["stage3_result"] else None

        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "prompt": prompt,
            "method": "pipeline",
            "provider_model": "pipeline",
            "status": "success",
            "runtime_seconds": runtime,
            "output_dir": result["output_dir"],
            "contract_name": result["spec"].get("contract_name"),
            "severity": summarize_analysis(analysis_result),
            **build_common_metrics(code),
        }
    except Exception as exc:
        runtime = time.perf_counter() - start
        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "prompt": prompt,
            "method": "pipeline",
            "provider_model": "pipeline",
            "status": "error",
            "runtime_seconds": runtime,
            "error": str(exc),
        }


def run_direct_model_item(model_name: str, item):
    start = time.perf_counter()
    prompt = item["prompt"]
    output_dir = OUTPUTS_DIR / model_name / item["id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        code = generate_contract(model_name, prompt)
        contract_path = output_dir / "generated.sol"
        save_text(contract_path, code)
        is_valid_code, invalid_reasons = is_probably_valid_solidity(code)
        validation = validate_generated_code(code, debug=False)

        if model_name in OLLAMA_MODELS:
            configured_model = OLLAMA_MODELS[model_name]
        elif model_name == "gpt":
            configured_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        elif model_name == "grok":
            configured_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        else:
            configured_model = model_name

        if not is_valid_code:
            runtime = time.perf_counter() - start
            return {
                "id": item["id"],
                "task_name": item["task_name"],
                "category": item["category"],
                "prompt": prompt,
                "method": "direct_llm",
                "provider": model_name,
                "provider_model": configured_model,
                "status": "invalid_generation",
                "runtime_seconds": runtime,
                "output_dir": str(output_dir),
                "contract_path": str(contract_path),
                "invalid_reasons": invalid_reasons,
                "severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0,
                    "total": 0,
                },
                "loc": count_non_empty_lines(code),
                "function_count": count_functions(code),
                "validation_success": validation["is_valid"],
                "validation_errors": validation["errors"],
                "validation_warnings": validation["warnings"],
                "compilation_success": None,
            }

        contract_path, report_path, stage3_result = run_stage3_for_code(code, item["task_name"], output_dir)
        runtime = time.perf_counter() - start

        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "prompt": prompt,
            "method": "direct_llm",
            "provider": model_name,
            "provider_model": configured_model,
            "status": "success",
            "runtime_seconds": runtime,
            "output_dir": str(output_dir),
            "contract_path": str(contract_path),
            "analysis_report_path": str(report_path),
            "severity": summarize_analysis(stage3_result.initial_analysis),
            **build_common_metrics(code),
        }
    except Exception as exc:
        runtime = time.perf_counter() - start
        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "prompt": prompt,
            "method": "direct_llm",
            "provider": model_name,
            "provider_model": model_name,
            "status": "error",
            "runtime_seconds": runtime,
            "error": str(exc),
        }


def run_experiment(models: list[str], limit: int | None, indexes: list[int] | None):
    ensure_dirs()
    dataset = load_dataset()
    dataset = select_dataset_items(dataset, limit=limit, indexes=indexes)

    all_results = []

    for item in dataset:
        print(f"\nRunning task: {item['task_name']}")
        for model_name in models:
            print(f"  -> {model_name}")
            if model_name == "pipeline":
                all_results.append(run_pipeline_item(item))
            else:
                all_results.append(run_direct_model_item(model_name, item))

    save_json(RESULTS_PATH, all_results)
    print(f"\nSaved results to: {RESULTS_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Result 5 runner: pipeline vs local LLMs and Grok")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=DEFAULT_MODELS,
        default=DEFAULT_MODELS,
        help="Select which models to run",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Run only the first N dataset entries",
    )
    parser.add_argument(
        "--indexes",
        "--indices",
        dest="indexes",
        nargs="+",
        help="Run only specific dataset entries using 1-based indexes, e.g. --indexes 8 9 or --indexes 2,8,15",
    )
    args = parser.parse_args()

    try:
        selected_indexes = parse_index_list(args.indexes)
    except ValueError as exc:
        parser.error(str(exc))

    if args.limit is not None and selected_indexes:
        parser.error("Use either --limit or --indexes/--indices, not both.")

    run_experiment(models=args.models, limit=args.limit, indexes=selected_indexes)


if __name__ == "__main__":
    main()
