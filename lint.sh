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

autoflake $opts \
	--in-place \
	--recursive \
	--remove-unused-variables \
	--remove-all-unused-imports \
	--exclude '*/migrations/*,*/__pycache__/*,./_build/*,./buck-out/*,./build/*,./collected-static/*,./data/*,./dist/*,./docker/*,./manage.py,./project/asgi.py,./project/wsgi.py,./venv/*,./*.csv,./*.pyc,./*.sh,./*.txt,./*.md,./*.log,./*.html' \
	.

isort $isort_opts \
	--skip .git/ \
	--skip .local/ \
	--skip collected-static/ \
	--skip data/ \
	--skip docker/ \
	--skip project/asgi.py \
	--skip project/wsgi.py \
	--skip-glob '*/migrations/*' \
	--line-length 120 \
	--multi-line VERTICAL_HANGING_INDENT \
	--trailing-comma \
	.

black $opts \
	--exclude '(/migrations/|\.direnv/|\.eggs/|\.git/|\.hg/|\.ipynb_checkpoints/|\.local/|\.mypy_cache/|\.nox/|\.svn/|\.tox/|\.venv/|__pycache__/|_build/|buck-out/|build/|collected-static/|data/|dist/|docker/|manage\.py|migrations/|project/asgi\.py|project/wsgi\.py|venv/)' \
	-l 120 \
	.

flake8 --config setup.cfg
