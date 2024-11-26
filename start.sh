#!/usr/bin/env bash

uv sync --quiet --frozen
TERM=xterm-256color .venv/bin/python -m lazy_github -- "$@"
