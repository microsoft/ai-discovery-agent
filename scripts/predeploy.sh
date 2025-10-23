#!/bin/bash

cd src
# App service relies on the requirements file
uv pip compile pyproject.toml -o requirements.txt
