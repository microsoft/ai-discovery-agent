#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Script to generate NOTICE file for OSS compliance.

This script reads the pyproject.toml file and generates a NOTICE file
that lists all third-party dependencies used in the project, following
OSS notice requirements as per:
- https://fosslight.org/hub-guide-en/tips/2_project/4_oss_notice/#types-of-oss-notices
- https://www.apache.org/licenses/LICENSE-2.0.html#redistribution
"""

import argparse
import re
import subprocess  # nosec B404
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any


def load_pyproject_toml(pyproject_path: Path) -> dict[str, Any]:
    """
    Load and parse pyproject.toml file.

    Args:
        pyproject_path: Path to pyproject.toml file

    Returns:
        Parsed TOML data as dictionary

    Raises:
        FileNotFoundError: If pyproject.toml file is not found
        Exception: If TOML parsing fails
    """
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


def extract_dependencies(pyproject_data: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Extract runtime and development dependencies from pyproject.toml.

    Args:
        pyproject_data: Parsed pyproject.toml data

    Returns:
        Tuple of (runtime_dependencies, dev_dependencies)
    """
    runtime_deps = []
    dev_deps = []

    # Extract runtime dependencies
    if "project" in pyproject_data and "dependencies" in pyproject_data["project"]:
        runtime_deps = pyproject_data["project"]["dependencies"]

    # Extract development dependencies from dependency-groups
    if "dependency-groups" in pyproject_data:
        dep_groups = pyproject_data["dependency-groups"]
        for _group_name, deps in dep_groups.items():
            dev_deps.extend(deps)

    # Also check for project.dependency-groups (alternative format)
    if "project" in pyproject_data and "dependency-groups" in pyproject_data["project"]:
        dep_groups = pyproject_data["project"]["dependency-groups"]
        for _group_name, deps in dep_groups.items():
            dev_deps.extend(deps)

    return runtime_deps, dev_deps


def normalize_package_name(dep_spec: str) -> str:
    """
    Extract package name from dependency specification.

    Args:
        dep_spec: Dependency specification (e.g., "requests>=2.25.0")

    Returns:
        Normalized package name
    """
    # Remove version constraints and extras
    package_name = re.split(r"[<>=!;[\]]", dep_spec)[0].strip()
    # Normalize package name (replace _ with -, convert to lowercase)
    return package_name.lower().replace("_", "-")


def get_package_info(package_name: str) -> dict[str, str] | None:
    """
    Get package information using pip show command.

    Args:
        package_name: Name of the package

    Returns:
        Dictionary with package information or None if not found
    """
    try:
        # Use 'uv run pip' to ensure pip is run in the correct environment.

        result = subprocess.run(  # nosec B603, B607
            ["uv", "run", "pip", "show", package_name],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,  # Add timeout for security
        )

        info = {}
        for line in result.stdout.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                info[key.strip()] = value.strip()

        return info
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return None


def generate_notice_content(
    project_name: str,
    project_version: str,
    runtime_deps: list[str],
    dev_deps: list[str],
    include_dev: bool = True,
) -> str:
    """
    Generate the content for the NOTICE file.

    Args:
        project_name: Name of the project
        project_version: Version of the project
        runtime_deps: List of runtime dependencies
        dev_deps: List of development dependencies
        include_dev: Whether to include development dependencies

    Returns:
        Generated NOTICE file content
    """

    notice_content = f"""NOTICE

{project_name} version {project_version}
Copyright (c) Microsoft Corporation.

This product includes software developed by Microsoft Corporation and third-party libraries.

================================================================================

THIRD-PARTY SOFTWARE NOTICES AND INFORMATION

This product incorporates components from the projects listed below. The original
copyright notices and the licenses under which Microsoft received such components
are set forth below. Microsoft reserves all rights not expressly granted herein,
whether by implication, estoppel or otherwise.

================================================================================

"""

    # Process runtime dependencies
    if runtime_deps:
        notice_content += "RUNTIME DEPENDENCIES:\n\n"

        for dep in sorted(runtime_deps):
            package_name = normalize_package_name(dep)
            package_info = get_package_info(package_name)

            if package_info:
                name = package_info.get("Name", package_name)
                version = package_info.get("Version", "unknown")
                homepage = package_info.get("Home-page", "").strip() or "N/A"
                license_info = package_info.get("License", "").strip() or "N/A"
                author = package_info.get("Author", "").strip() or "N/A"

                notice_content += f"* {name} {version}\n"
                notice_content += f"  Homepage: {homepage}\n"
                notice_content += f"  License: {license_info}\n"
                notice_content += f"  Author: {author}\n"
                notice_content += f"  Dependency specification: {dep}\n\n"
            else:
                notice_content += f"* {package_name}\n"
                notice_content += f"  Dependency specification: {dep}\n"
                notice_content += "  Note: Package information not available\n\n"

    # Process development dependencies if requested
    if include_dev and dev_deps:
        notice_content += "DEVELOPMENT DEPENDENCIES:\n\n"

        for dep in sorted(dev_deps):
            package_name = normalize_package_name(dep)
            package_info = get_package_info(package_name)

            if package_info:
                name = package_info.get("Name", package_name)
                version = package_info.get("Version", "unknown")
                homepage = package_info.get("Home-page", "").strip() or "N/A"
                license_info = package_info.get("License", "").strip() or "N/A"
                author = package_info.get("Author", "").strip() or "N/A"

                notice_content += f"* {name} {version}\n"
                notice_content += f"  Homepage: {homepage}\n"
                notice_content += f"  License: {license_info}\n"
                notice_content += f"  Author: {author}\n"
                notice_content += f"  Dependency specification: {dep}\n\n"
            else:
                notice_content += f"* {package_name}\n"
                notice_content += f"  Dependency specification: {dep}\n"
                notice_content += "  Note: Package information not available\n\n"

    notice_content += f"""================================================================================

This NOTICE file was generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

For more information about open source licenses, visit:
- https://opensource.org/licenses/
- https://fosslight.org/hub-guide-en/tips/2_project/4_oss_notice/

For questions about this NOTICE file, please contact Microsoft Corporation.
"""

    return notice_content


def main() -> int:
    """
    Main function to generate NOTICE file.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Generate NOTICE file for OSS compliance"
    )
    parser.add_argument(
        "--pyproject-path",
        type=Path,
        default=Path("src/pyproject.toml"),
        help="Path to pyproject.toml file (default: src/pyproject.toml)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("NOTICE"),
        help="Output path for NOTICE file (default: NOTICE)",
    )
    parser.add_argument(
        "--no-dev",
        action="store_true",
        help="Exclude development dependencies from NOTICE file (dev deps included by default)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    try:
        # Load pyproject.toml
        if args.verbose:
            print(f"Loading pyproject.toml from {args.pyproject_path}")

        pyproject_data = load_pyproject_toml(args.pyproject_path)

        # Extract project information
        project_info = pyproject_data.get("project", {})
        project_name = project_info.get("name", "Unknown Project")
        project_version = project_info.get("version", "Unknown Version")

        if args.verbose:
            print(f"Project: {project_name} v{project_version}")

        # Extract dependencies
        runtime_deps, dev_deps = extract_dependencies(pyproject_data)

        if args.verbose:
            print(f"Found {len(runtime_deps)} runtime dependencies")
            print(f"Found {len(dev_deps)} development dependencies")

        # Generate NOTICE content
        if args.verbose:
            print("Generating NOTICE content...")

        notice_content = generate_notice_content(
            project_name, project_version, runtime_deps, dev_deps, not args.no_dev
        )

        # Write NOTICE file with cleaned content (remove trailing whitespace)
        cleaned_content = "\n".join(
            line.rstrip() for line in notice_content.splitlines()
        )
        # Ensure file ends with exactly one newline
        if not cleaned_content.endswith("\n"):
            cleaned_content += "\n"

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

        print(f"NOTICE file generated successfully: {args.output}")
        return 0

    except Exception as e:
        print(f"Error generating NOTICE file: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
