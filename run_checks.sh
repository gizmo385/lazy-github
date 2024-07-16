#!/usr/bin/env bash

source ./venv/bin/activate
uv run --extra=checks pyright
uv run --extra=checks ruff check
