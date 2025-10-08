$repo_name = gh repo view --json nameWithOwner -t '{{.nameWithOwner}}'
azd env set GITHUB_REPOSITORY "$repo_name"


uv pip compile src/pyproject.toml -o src/requirements.txt
