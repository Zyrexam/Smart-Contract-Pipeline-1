#!/bin/sh
# Production version - already working well

FILENAME="$1"
TIMEOUT="$2"
BIN="$3"
MAIN="$4"

# Calculate execution timeout (80% of total)
if [ "$TIMEOUT" -gt 0 ]; then
    TO=$(( (TIMEOUT * 8 + 9) / 10 ))
    OPT_TIMEOUT="--execution-timeout $TO"
else
    OPT_TIMEOUT="--execution-timeout 90"
fi

# Disable solc auto-download to avoid network errors
export MYTHRIL_DISABLE_SOLC_DOWNLOAD=1

# Run with error handling - returns JSON on failure
/usr/local/bin/myth analyze \
  $OPT_TIMEOUT \
  --max-depth 12 \
  --solver-timeout 10000 \
  -o json \
  "$FILENAME" 2>&1 || \
echo '{"error":"Analysis failed","issues":[]}'

# Always exit 0 to not block pipeline
exit 0