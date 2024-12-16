#!/usr/bin/env bash

uv sync
.venv/bin/ruff check --select I --fix
.venv/bin/pyright
