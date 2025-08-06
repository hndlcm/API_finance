#!/bin/bash

if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # sudo ln -s /root/.local/bin/uv /usr/local/bin/uv
else
    echo "uv already installed, skipping installation."
fi

uv sync --locked  --no-dev

if [ ! -f .env ]; then
    cp .env.example .env
fi
