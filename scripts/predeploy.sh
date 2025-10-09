repo_name=$(gh repo view --json nameWithOwner -t "{{.nameWithOwner}}")
azd env set GITHUB_REPOSITORY "$repo_name"

cd src
# App service relies on the requirements file
uv pip compile pyproject.toml -o requirements.txt
