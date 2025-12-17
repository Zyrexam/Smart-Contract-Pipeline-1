#!/bin/sh
# Semgrep with simplified, working rules

FILENAME="$1"
TIMEOUT="$2"
BIN="$3"

# Create simple, working rules
RULES_FILE="/tmp/semgrep-rules-$$.yaml"
cat > "$RULES_FILE" <<'EOF'
rules:
  - id: tx-origin-usage
    pattern: tx.origin
    message: "Avoid using tx.origin for authorization - use msg.sender instead"
    severity: ERROR
    languages: [solidity]

  - id: reentrancy-pattern
    pattern: |
      $X.call{value: $V}(...)
    message: "Potential reentrancy - ensure state changes happen before external calls"
    severity: WARNING
    languages: [solidity]

  - id: unchecked-send
    pattern: $ADDR.send($VALUE)
    message: "Unchecked send - always check return value"
    severity: WARNING
    languages: [solidity]

  - id: unchecked-transfer
    pattern: $ADDR.transfer($VALUE)
    message: "Transfer can fail - consider using call with checks"
    severity: INFO
    languages: [solidity]

  - id: delegatecall-usage
    pattern: $ADDR.delegatecall(...)
    message: "Delegatecall is dangerous - ensure target is trusted"
    severity: WARNING
    languages: [solidity]

  - id: selfdestruct-usage
    pattern: selfdestruct(...)
    message: "Selfdestruct is dangerous and deprecated"
    severity: WARNING
    languages: [solidity]
EOF

# Run semgrep
semgrep \
  --config "$RULES_FILE" \
  --timeout ${TIMEOUT:-120} \
  --json \
  --disable-version-check \
  "$FILENAME" 2>&1

EXIT_CODE=$?
rm -f "$RULES_FILE"
exit $EXIT_CODE