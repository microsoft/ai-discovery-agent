#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Output files
JUNIT_OUTPUT="${PROJECT_ROOT}/copyright-header-check.xml"
JSON_OUTPUT="${PROJECT_ROOT}/copyright-header-check.json"

echo "Checking copyright headers in src/ directory..."
echo ""

# Arrays to store files with missing headers
declare -a missing_files=()
# Counter for total files checked
total_files=0

# Define file type patterns and their corresponding header patterns
# Format: "file_extension:file_pattern:header_pattern:description"
declare -A file_checks=(
  ["python"]="*.py:^# Copyright (c) Microsoft Corporation\.:Python"
  ["javascript"]="*.js:^// Copyright (c) Microsoft Corporation\.:JavaScript"
  ["typescript"]="*.ts:^// Copyright (c) Microsoft Corporation\.:TypeScript"
  ["jsx"]="*.jsx:^// Copyright (c) Microsoft Corporation\.:JSX"
  ["tsx"]="*.tsx:^// Copyright (c) Microsoft Corporation\.:TSX"
  ["html"]="*.html:<!-- Copyright (c) Microsoft Corporation\. -->:HTML"
  ["css"]="*.css:/\* Copyright (c) Microsoft Corporation\. \*/:CSS"
)

# Define the license header patterns for each comment style
declare -A license_patterns=(
  ["hash"]="^# Licensed under the MIT license\."
  ["slash"]="^// Licensed under the MIT license\."
  ["html"]="<!-- Licensed under the MIT license\. -->"
  ["css"]="/\* Licensed under the MIT license\. \*/"
)

# Map file types to license pattern types
declare -A file_license_map=(
  ["python"]="hash"
  ["javascript"]="slash"
  ["typescript"]="slash"
  ["jsx"]="slash"
  ["tsx"]="slash"
  ["html"]="html"
  ["css"]="css"
)

# Function to check files of a specific type
check_file_type() {
  local file_type=$1
  local file_pattern=$2
  local copyright_pattern=$3
  local description=$4
  local license_type=${file_license_map[$file_type]}
  local license_pattern=${license_patterns[$license_type]}

  # Find files in src directory, excluding specified directories
  local files=$(find "${PROJECT_ROOT}/src" \
    -path "*/.venv" -prune -o \
    -path "*/__pycache__" -prune -o \
    -path "*/.pytest_cache" -prune -o \
    -path "*/.ruff_cache" -prune -o \
    -path "*.egg-info" -prune -o \
    -type f -name "$file_pattern" -print 2>/dev/null)

  if [ -z "$files" ]; then
    return
  fi

  echo "Checking $description files..."
  for file in $files; do
    local relative_file="${file#${PROJECT_ROOT}/}"
    total_files=$((total_files + 1))

    # Check if file has both required headers
    if ! grep -q "$copyright_pattern" "$file" || \
       ! grep -q "$license_pattern" "$file"; then
      missing_files+=("$relative_file")
      echo -e "${RED}✗${NC} $relative_file - Missing copyright header"
    else
      echo -e "${GREEN}✓${NC} $relative_file"
    fi
  done
  echo ""
}

# Run checks for all defined file types
for file_type in "${!file_checks[@]}"; do
  IFS=':' read -r pattern copyright_pattern description <<< "${file_checks[$file_type]}"
  check_file_type "$file_type" "$pattern" "$copyright_pattern" "$description"
done

# Function to generate junit.xml output
generate_junit_xml() {
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S")
  local passed=$((total_files - ${#missing_files[@]}))
  local failed=${#missing_files[@]}

  # Calculate execution time (approximate)
  local time="0.0"

  # Create junit.xml file
  cat > "$JUNIT_OUTPUT" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Copyright Header Check" tests="${total_files}" failures="${failed}" errors="0" time="${time}" timestamp="${timestamp}">
  <testsuite name="Copyright Headers" tests="${total_files}" failures="${failed}" errors="0" skipped="0" time="${time}">
EOF

  # Add test cases for files with correct headers
  for file_type in "${!file_checks[@]}"; do
    IFS=':' read -r pattern copyright_pattern description <<< "${file_checks[$file_type]}"
    local files=$(find "${PROJECT_ROOT}/src" \
      -path "*/.venv" -prune -o \
      -path "*/__pycache__" -prune -o \
      -path "*/.pytest_cache" -prune -o \
      -path "*/.ruff_cache" -prune -o \
      -path "*.egg-info" -prune -o \
      -type f -name "$pattern" -print 2>/dev/null)

    for file in $files; do
      local relative_file="${file#${PROJECT_ROOT}/}"
      local is_missing=false

      # Check if this file is in the missing_files array
      for missing in "${missing_files[@]}"; do
        if [[ "$missing" == "$relative_file" ]]; then
          is_missing=true
          break
        fi
      done

      if $is_missing; then
        # Generate failure test case
        cat >> "$JUNIT_OUTPUT" << EOF
    <testcase name="${relative_file}" classname="CopyrightHeaderCheck" time="0.0">
      <failure message="Missing copyright header" type="CopyrightHeaderMissing">
File: ${relative_file}

Expected headers:
  Copyright: # Copyright (c) Microsoft Corporation. (or // or &lt;!-- or /* depending on file type)
  License: # Licensed under the MIT license. (or // or &lt;!-- or /* depending on file type)
      </failure>
    </testcase>
EOF
      else
        # Generate success test case
        cat >> "$JUNIT_OUTPUT" << EOF
    <testcase name="${relative_file}" classname="CopyrightHeaderCheck" time="0.0"/>
EOF
      fi
    done
  done

  # Close the XML structure
  cat >> "$JUNIT_OUTPUT" << EOF
  </testsuite>
</testsuites>
EOF

  echo "JUnit XML report generated: $JUNIT_OUTPUT"
}

# Function to generate JSON output
generate_json_output() {
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S")
  local passed=$((total_files - ${#missing_files[@]}))
  local failed=${#missing_files[@]}

  # Start JSON structure
  cat > "$JSON_OUTPUT" << EOF
{
  "timestamp": "${timestamp}",
  "summary": {
    "total_files": ${total_files},
    "passed": ${passed},
    "failed": ${failed}
  },
  "failed_files": [
EOF

  # Add failed files as JSON array
  local failed_files_json=""
  for file in "${missing_files[@]}"; do
    # Escape double quotes in file path if any
    local escaped_file="${file//\"/\\\"}"
    if [ -n "$failed_files_json" ]; then
      failed_files_json+=",\n"
    fi
    failed_files_json+="    {\"path\": \"${escaped_file}\", \"message\": \"Missing copyright header\"}"
  done

  # Output failed_files array
  if [ -n "$failed_files_json" ]; then
    echo -e "$failed_files_json" >> "$JSON_OUTPUT"
  fi

  ],
  "header_examples": {
    "python": {
      "extension": ".py",
      "syntax": "# ",
      "example": "# Copyright (c) Microsoft Corporation.\n# Licensed under the MIT license."
    },
    "javascript": {
      "extension": ".js, .ts, .jsx, .tsx",
      "syntax": "// ",
      "example": "// Copyright (c) Microsoft Corporation.\n// Licensed under the MIT license."
    },
    "html": {
      "extension": ".html",
      "syntax": "<!-- -->",
      "example": "<!-- Copyright (c) Microsoft Corporation. -->\n<!-- Licensed under the MIT license. -->"
    },
    "css": {
      "extension": ".css",
      "syntax": "/* */",
      "example": "/* Copyright (c) Microsoft Corporation. */\n/* Licensed under the MIT license. */"
    }
  }
}
EOF

  echo "JSON report generated: $JSON_OUTPUT"
}

# Generate reports
generate_junit_xml
generate_json_output

echo "================================================"

# Report results
if [ ${#missing_files[@]} -eq 0 ]; then
  echo -e "${GREEN}✓ All files have the required copyright headers!${NC}"
  exit 0
else
  echo -e "${RED}✗ Found ${#missing_files[@]} file(s) missing copyright headers:${NC}"
  echo ""
  for file in "${missing_files[@]}"; do
    echo "  - $file"
  done
  echo ""
  echo "Required headers:"
  echo "  Python:        # Copyright (c) Microsoft Corporation."
  echo "                 # Licensed under the MIT license."
  echo "  JS/TS/JSX/TSX: // Copyright (c) Microsoft Corporation."
  echo "                 // Licensed under the MIT license."
  echo "  HTML:          <!-- Copyright (c) Microsoft Corporation. -->"
  echo "                 <!-- Licensed under the MIT license. -->"
  echo "  CSS:           /* Copyright (c) Microsoft Corporation. */"
  echo "                 /* Licensed under the MIT license. */"
  exit 1
fi
