# City Brain

Operational decision-maker layer for TSYP14.

## Quickstart
    cp .env.example .env
    docker compose up --build

## Local dev
    python -m venv .venv
    .venv\Scripts\activate
    pip install -e ".[dev]"
    pytest
