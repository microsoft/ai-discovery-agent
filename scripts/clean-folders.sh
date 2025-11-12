#!/bin/sh

# This script cleans up temporary folders commonly found in Python projects.

temp_folders=(".pytest_cache" ".ruff_cache" "*.egg-info" "dist" "__pycache__" ".files" ".build" ".venv")

for folder in "${temp_folders[@]}"; do
    find . -type d -name "$folder" -exec rm -rf {} +
done

temp_files=("*.pyc" "*.pyo" "*~" ".*.swp" "*.sarif" "copyright-header-check.*" "bicep_results.xml")

for file in "${temp_files[@]}"; do
    find . -type f -name "$file" -exec rm -f {} +
done

echo "Cleanup complete."
