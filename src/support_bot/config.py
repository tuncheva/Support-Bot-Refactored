"""Configuration and repo-relative path helpers."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """Return the repository root based on this file location.

    Assumes this file lives at `src/support_bot/config.py`.
    """

    return Path(__file__).resolve().parents[2]


def default_products_path() -> Path:
    return repo_root() / "data" / "products.json"


def products_path() -> Path:
    """Return products.json path.

    Precedence:
    1) `PRODUCTS_PATH` env var
    2) `./data/products.json` repo-relative default
    """

    raw = os.getenv("PRODUCTS_PATH")
    if raw:
        return Path(raw).expanduser().resolve()
    return default_products_path()
