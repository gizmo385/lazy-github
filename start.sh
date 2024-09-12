#!/usr/bin/env bash

uv sync --quiet
.venv/bin/python -m lazy_github -- "$@"
