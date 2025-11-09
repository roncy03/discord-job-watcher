from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, HttpUrl, ValidationError


class SourceConfig(BaseModel):
    greenhouse: List[str] = Field(default_factory=list)
    lever: List[str] = Field(default_factory=list)


class Settings(BaseModel):
    discord_webhook_url: Optional[HttpUrl] = None
    discord_webhook_url_software: Optional[HttpUrl] = None
    discord_webhook_url_data: Optional[HttpUrl] = None
    sources: SourceConfig


def load_sources(path: Path) -> SourceConfig:
    data = yaml.safe_load(path.read_text()) or {}
    return SourceConfig(**data)


def _clean(url: str | None) -> str | None:
    if not url:
        return None
    stripped = url.strip()
    return stripped or None


def load_settings(config_path: Path) -> Settings:
    webhook = _clean(os.getenv("DISCORD_WEBHOOK_URL"))
    webhook_software = _clean(os.getenv("DISCORD_WEBHOOK_URL_SOFTWARE"))
    webhook_data = _clean(os.getenv("DISCORD_WEBHOOK_URL_DATA"))
    if not any([webhook, webhook_software, webhook_data]):
        raise RuntimeError(
            "At least one webhook env var must be set: "
            "DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_URL_SOFTWARE, or DISCORD_WEBHOOK_URL_DATA"
        )
    sources = load_sources(config_path)
    try:
        return Settings(
            discord_webhook_url=webhook,
            discord_webhook_url_software=webhook_software,
            discord_webhook_url_data=webhook_data,
            sources=sources,
        )
    except ValidationError as exc:
        raise RuntimeError(f"Invalid configuration: {exc}") from exc
