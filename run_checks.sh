#!/usr/bin/env bash

uv sync
.venv/bin/ruff check
.venv/bin/pyright
