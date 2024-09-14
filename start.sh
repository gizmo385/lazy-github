#!/usr/bin/env bash

uv sync --quiet --frozen
.venv/bin/python -m lazy_github -- "$@"
