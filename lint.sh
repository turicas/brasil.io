#!/bin/bash

set -ev

if [[ $1 == "--check" ]]; then
	opts="--check"
	isort_opts="--check-only"
else
	opts=""
	isort_opts=""
fi

cd /app
autoflake $opts --in-place --recursive --remove-unused-variables --remove-all-unused-imports --exclude docker/,.git/,.local .
isort $isort_opts --skip .local --skip migrations --skip wsgi --skip asgi --line-length 120 --multi-line VERTICAL_HANGING_INDENT --trailing-comma .
black $opts --exclude '(.local/|docker/|migrations/|config/settings\.py|manage\.py|\.direnv|\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|venv|\.svn|\.ipynb_checkpoints|_build|buck-out|build|dist|__pypackages__)' -l 120 .
flake8 --config setup.cfg
