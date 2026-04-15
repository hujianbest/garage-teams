#!/bin/bash

# Garage OS Structure Verification Script
# Checks that all .garage/ directories and files exist with valid formats

set -e

BASE_DIR=".garage"
ERRORS=0

echo "🔍 Verifying Garage OS structure..."
echo ""

# Function to check if a directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo "✅ Directory exists: $1"
        return 0
    else
        echo "❌ Directory missing: $1"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check if a file exists
check_file() {
    if [ -f "$1" ]; then
        echo "✅ File exists: $1"
        return 0
    else
        echo "❌ File missing: $1"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to validate JSON file
validate_json() {
    if command -v python3 &> /dev/null; then
        if python3 -m json.tool "$1" > /dev/null 2>&1; then
            echo "✅ JSON valid: $1"
            return 0
        else
            echo "❌ JSON invalid: $1"
            ERRORS=$((ERRORS + 1))
            return 1
        fi
    else
        echo "⚠️  Python3 not found, skipping JSON validation for: $1"
        return 0
    fi
}

# Function to validate YAML file
validate_yaml() {
    if command -v python3 &> /dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('$1'))" 2>/dev/null; then
            echo "✅ YAML valid: $1"
            return 0
        else
            echo "❌ YAML invalid: $1"
            ERRORS=$((ERRORS + 1))
            return 1
        fi
    else
        echo "⚠️  Python3 or PyYAML not found, skipping YAML validation for: $1"
        return 0
    fi
}

echo "📁 Checking directories..."
check_dir "$BASE_DIR"
check_dir "$BASE_DIR/sessions"
check_dir "$BASE_DIR/sessions/active"
check_dir "$BASE_DIR/sessions/archived"
check_dir "$BASE_DIR/knowledge"
check_dir "$BASE_DIR/knowledge/decisions"
check_dir "$BASE_DIR/knowledge/patterns"
check_dir "$BASE_DIR/knowledge/solutions"
check_dir "$BASE_DIR/knowledge/.metadata"
check_dir "$BASE_DIR/experience"
check_dir "$BASE_DIR/experience/records"
check_dir "$BASE_DIR/experience/patterns"
check_dir "$BASE_DIR/config"
check_dir "$BASE_DIR/config/tools"
check_dir "$BASE_DIR/contracts"

echo ""
echo "📄 Checking .gitkeep files..."
check_file "$BASE_DIR/sessions/active/.gitkeep"
check_file "$BASE_DIR/sessions/archived/.gitkeep"

echo ""
echo "⚙️  Checking config files..."
check_file "$BASE_DIR/config/platform.json"
validate_json "$BASE_DIR/config/platform.json"

check_file "$BASE_DIR/config/host-adapter.json"
validate_json "$BASE_DIR/config/host-adapter.json"

check_file "$BASE_DIR/config/tools/registered-tools.yaml"
validate_yaml "$BASE_DIR/config/tools/registered-tools.yaml"

echo ""
echo "📚 Checking knowledge files..."
check_file "$BASE_DIR/knowledge/.metadata/index.json"
validate_json "$BASE_DIR/knowledge/.metadata/index.json"

echo ""
echo "📋 Checking contract files..."
CONTRACTS=(
    "host-adapter-interface.yaml"
    "session-manager-interface.yaml"
    "skill-executor-interface.yaml"
    "state-machine-interface.yaml"
    "error-handler-interface.yaml"
    "knowledge-store-interface.yaml"
    "tool-registry-interface.yaml"
    "version-manager-interface.yaml"
)

for contract in "${CONTRACTS[@]}"; do
    check_file "$BASE_DIR/contracts/$contract"
    validate_yaml "$BASE_DIR/contracts/$contract"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed! Garage OS structure is valid."
    exit 0
else
    echo "❌ Found $ERRORS error(s). Please fix the issues above."
    exit 1
fi
