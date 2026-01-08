#!/bin/sh
# Production version with graceful failure handling

FILENAME="$1"
TIMEOUT="$2"
BIN="$3"

# Environment setup to prevent auto-downloads and solc-select issues
export PATH="/usr/local/bin:$PATH"
export SOLC_SELECT_DISABLED=1

# Disable solc-select completely - prevent it from trying to download or switch versions
export SOLC_SELECT_DISABLED=1
unset SOLC_VERSION

# Disable network access for solc downloads (use pre-installed versions only)
export SOLC_SELECT_DISABLED=1
export SLITHER_DISABLE_SOLC_DOWNLOAD=1

# Try to find solc in common locations
# The SmartBugs base image should have solc available
if command -v solc >/dev/null 2>&1; then
    SOLC_PATH=$(command -v solc)
    export PATH="$(dirname "$SOLC_PATH"):$PATH"
    echo "Found solc at: $SOLC_PATH" >&2
else
    # Try common locations
    for path in /usr/bin/solc /usr/local/bin/solc /root/.solcx/bin/solc; do
        if [ -f "$path" ]; then
            export PATH="$(dirname "$path"):$PATH"
            echo "Found solc at: $path" >&2
            break
        fi
    done
fi

# Function to ensure output exists with proper format
ensure_output() {
    if [ ! -f /output.json ] || [ ! -s /output.json ]; then
        # Create valid empty result JSON
        echo '{"success":false,"error":"Slither execution failed","results":{"detectors":[]}}' > /output.json
    fi
}

# CRITICAL FIX: Do NOT initialize fallback JSON before running Slither
# This was overwriting Slither's actual output. We only create fallback if Slither fails.
# Slither will create /output.json itself, so we don't need to pre-create it.

# Run Slither and silence stdout/stderr completely
# Slither writes JSON to /output.json, but also prints human-readable text to stdout
# We ONLY want the JSON file, so we redirect stdout/stderr to /dev/null
slither "$FILENAME" \
  --json /output.json \
  --solc-disable-warnings \
  --skip-clean \
  --filter-paths "node_modules" \
  > /dev/null 2>&1
SLITHER_EXIT=$?

# Debug: Log exit code only (not the text output which we've silenced)
echo "Slither exit code: $SLITHER_EXIT" >&2

# Check if output file was created and is valid JSON
# IMPORTANT: We check for file existence and validity, but we do NOT overwrite
# Slither's output even if success=false, because detectors may still be present
if [ ! -f /output.json ] || [ ! -s /output.json ]; then
    # File doesn't exist or is empty - create fallback ONLY in this case
    echo "Output file missing or empty, creating fallback" >&2
    ensure_output
elif ! python3 -c "import json; json.load(open('/output.json'))" 2>/dev/null; then
    # File exists but is not valid JSON - create fallback ONLY if invalid JSON
    echo "Output file is not valid JSON, creating fallback" >&2
    echo '{"success":false,"error":"Invalid JSON output from Slither","results":{"detectors":[]}}' > /output.json
else
    # File is valid JSON - validate structure for debugging
    # NOTE: We do NOT overwrite even if success=false, because detectors may exist
    # The parser will handle success=false correctly by still parsing detectors
    echo "Output file is valid JSON" >&2
    # Check structure and count detectors for debugging
    if python3 -c "import json; d=json.load(open('/output.json')); detectors=d.get('results', {}).get('detectors', []); print(f'Detectors found: {len(detectors)}')" 2>&1; then
        echo "Output file structure validated" >&2
    fi
fi

# Always exit 0 to not block pipeline
exit 0