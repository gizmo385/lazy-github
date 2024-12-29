#!/usr/bin/env bash

uv sync
.venv/bin/ruff check --select I --fix
.venv/bin/ruff check --fix
.venv/bin/pyright
