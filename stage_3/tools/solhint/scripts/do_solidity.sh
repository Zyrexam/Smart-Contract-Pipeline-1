#!/bin/sh
# Production version - security-focused configuration

FILENAME="$1"
BIN="$2"

# Create security-focused config (filter out noise)
cat > /sb/.solhint.json <<'EOF'
{
  "extends": "solhint:recommended",
  "rules": {
    "avoid-tx-origin": "error",
    "check-send-result": "error",
    "avoid-low-level-calls": "warn",
    "avoid-call-value": "warn",
    "compiler-version": ["warn", "^0.8.0"],
    "func-visibility": ["warn", {"ignoreConstructors": true}],
    "state-visibility": "warn",
    "no-unused-vars": "warn",
    "no-empty-blocks": "warn",
    "use-natspec": "off",
    "import-path-check": "off"
  }
}
EOF

# Run with unix format (easier to parse)
cd /sb && solhint "$FILENAME" 2>&1

exit $?
