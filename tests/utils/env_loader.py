from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists() or not path.is_file():
        return values

    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_test_env(search_roots: Iterable[Path] | None = None) -> dict[str, str]:
    if search_roots is None:
        search_roots = [Path.cwd(), Path(__file__).resolve().parents[2]]

    merged: dict[str, str] = {}
    names = ('.env', '.env.test', '.env.dev')
    for root in search_roots:
        for name in names:
            merged.update(_parse_env_file(root / name))

    for key, value in os.environ.items():
        merged[key] = value
    return merged


def get_env(name: str, default: str | None = None) -> str | None:
    return load_test_env().get(name, default)
