repo_name=$(gh repo view --json nameWithOwner -t "{{.nameWithOwner}}")
azd env set GITHUB_REPOSITORY "$repo_name"

cd src
uv pip compile pyproject.toml --no-deps -o requirements.txt
