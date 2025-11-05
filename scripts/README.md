# NOTICE File Generation Scripts

This directory contains scripts to generate OSS-compliant NOTICE files for the AI Discovery Agent project.

## Overview

The NOTICE file generation follows OSS best practices as outlined in:
- [FOSSLight Guide - OSS Notice Types](https://fosslight.org/hub-guide-en/tips/2_project/4_oss_notice/#types-of-oss-notices)
- [Apache License 2.0 - Redistribution Requirements](https://www.apache.org/licenses/LICENSE-2.0.html#redistribution)

## Files

### `generate-notice.py`
A Python script that parses `pyproject.toml` and generates a comprehensive NOTICE file listing all third-party dependencies.

**Features:**
- Extracts runtime and development dependencies from `pyproject.toml`
- Attempts to gather package information using `pip show`
- Supports both PEP 621 and legacy dependency group formats
- Generates formatted NOTICE file with proper OSS attribution

**Usage:**
```bash
python3 scripts/generate-notice.py [OPTIONS]
```

**Options:**
- `--pyproject-path PATH`: Path to pyproject.toml (default: `src/pyproject.toml`)
- `--output PATH`: Output path for NOTICE file (default: `NOTICE`)
- `--include-dev`: Include development dependencies
- `--verbose`: Enable verbose output

### `generate-notice.sh`
A shell wrapper script that provides a convenient interface and handles the Python environment automatically.

**Features:**
- Automatically detects and uses `uv` if available
- Fallback to system Python if `uv` is not available
- User-friendly command-line interface
- Input validation and error handling

**Usage:**
```bash
./scripts/generate-notice.sh [OPTIONS]
```

**Options:**
- `-p, --pyproject-path PATH`: Path to pyproject.toml
- `-o, --output PATH`: Output path for NOTICE file
- `-d, --include-dev`: Include development dependencies
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help message

## Examples

### Basic Usage
Generate a NOTICE file with runtime dependencies only:
```bash
./scripts/generate-notice.sh
```

### Include Development Dependencies
Generate a NOTICE file including development/build dependencies:
```bash
./scripts/generate-notice.sh --include-dev
```

### Custom Paths
Generate a NOTICE file with custom input and output paths:
```bash
./scripts/generate-notice.sh \
  --pyproject-path custom/pyproject.toml \
  --output THIRD_PARTY_NOTICES.txt \
  --verbose
```

### Using Python Script Directly
If you prefer to use the Python script directly:
```bash
cd src
uv run python ../scripts/generate-notice.py --include-dev --verbose
```

## NOTICE File Format

The generated NOTICE file includes:

1. **Header Section**: Project name, version, and copyright
2. **Third-Party Software Notices**: Legal disclaimer
3. **Runtime Dependencies**: All dependencies required for operation
4. **Development Dependencies**: Build/test dependencies (if `--include-dev` is used)
5. **Footer**: Generation timestamp and additional information

For each dependency, the script attempts to include:
- Package name and version
- Homepage URL
- License information
- Author information
- Original dependency specification

## Requirements

### Python Dependencies
The script requires Python 3.11+ and attempts to use these packages if available:
- `tomllib` (Python 3.11+) or `tomli` (fallback)
- Standard library modules: `argparse`, `subprocess`, `pathlib`, `datetime`

### System Requirements
- Python 3.11 or later
- `pip` command available in PATH (for package information gathering)
- `uv` (optional, but recommended for this project)

## Security Considerations

The script includes several security measures:
- Uses `subprocess` with timeout limits
- Validates file paths before processing
- Uses full paths for external commands when possible
- Includes appropriate `nosec` comments for security scanners

## Integration with Build Process

You can integrate NOTICE file generation into your build process by adding it to:

### GitHub Actions
```yaml
- name: Generate NOTICE file
  run: ./scripts/generate-notice.sh --include-dev
```

### Pre-commit Hook
Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: generate-notice
      name: Generate NOTICE file
      entry: ./scripts/generate-notice.sh
      language: system
      files: ^src/pyproject\.toml$
      pass_filenames: false
```

### VS Code Task
Add to `.vscode/tasks.json`:
```json
{
  "label": "Generate NOTICE",
  "type": "shell",
  "command": "./scripts/generate-notice.sh",
  "args": ["--verbose"],
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always"
  }
}
```

## Troubleshooting

### Package Information Not Available
If the script shows "Package information not available" for dependencies:
1. Ensure the packages are installed in your current environment
2. Try installing the project dependencies: `uv sync` or `pip install -e .`
3. Verify `pip show <package-name>` works manually

### Permission Errors
If you get permission errors:
```bash
chmod +x scripts/generate-notice.sh
chmod +x scripts/generate-notice.py
```

### Python Version Issues
If you get import errors related to `tomllib`:
- Ensure you're using Python 3.11+
- Install `tomli` as a fallback: `pip install tomli`

## License Compliance Notes

This script helps generate NOTICE files but does not constitute legal advice. For OSS compliance:

1. **Review Generated Content**: Always review the generated NOTICE file
2. **Verify License Information**: Confirm license details for critical dependencies
3. **Update Regularly**: Regenerate NOTICE files when dependencies change
4. **Legal Review**: Consider legal review for commercial distributions

## Contributing

When modifying these scripts:
1. Follow the project's Python code style guidelines
2. Update this README if adding new features
3. Test with various dependency configurations
4. Ensure security best practices are maintained