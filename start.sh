#!/usr/bin/env bash

uv venv --quiet
uv pip sync --quiet requirements.txt
.venv/bin/python -m lazy_github
