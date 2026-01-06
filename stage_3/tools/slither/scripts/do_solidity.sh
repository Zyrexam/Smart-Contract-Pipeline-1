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

# Initialize output file first (in case of early failure)
ensure_output

# Try Slither with minimal requirements and capture both stdout and stderr
# Redirect stderr to stdout so we can capture all errors
SLITHER_OUTPUT=$(slither "$FILENAME" \
  --json /output.json \
  --solc-disable-warnings \
  --skip-clean \
  --filter-paths "node_modules" 2>&1)
SLITHER_EXIT=$?

# Check if output file was created and is valid JSON
if [ ! -f /output.json ] || [ ! -s /output.json ]; then
    # File doesn't exist or is empty - create fallback
    ensure_output
elif ! python3 -c "import json; json.load(open('/output.json'))" 2>/dev/null; then
    # File exists but is not valid JSON - create fallback
    echo '{"success":false,"error":"Invalid JSON output from Slither","results":{"detectors":[]}}' > /output.json
fi

# Always exit 0 to not block pipeline
exit 0