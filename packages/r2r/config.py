from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - py<3.11
    import tomli as tomllib

from pydantic import BaseModel


class R2RConfig(BaseModel):
    base_url: str = "http://localhost:7272"
    api_key: str | None = None


def load_config(path: str | None = None) -> R2RConfig:
    env_path = os.getenv("R2R_CONFIG_PATH") or "infra/r2r.toml"
    file_path = Path(path or env_path)
    data: dict[str, Any] = {}
    if file_path.exists():
        with file_path.open("rb") as f:
            data.update(tomllib.load(f))
    env_base = os.getenv("R2R_BASE_URL")
    env_key = os.getenv("R2R_API_KEY")
    if env_base:
        data["base_url"] = env_base
    if env_key:
        data["api_key"] = env_key
    return R2RConfig(**data)


__all__ = ["R2RConfig", "load_config"]
