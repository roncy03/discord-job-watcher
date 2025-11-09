from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, HttpUrl, ValidationError


class WorkdaySource(BaseModel):
    tenant: str
    site: str
    host: str
    limit: int = Field(default=50, ge=1, le=200)
    search_text: str = ""


class SourceConfig(BaseModel):
    greenhouse: List[str] = Field(default_factory=list)
    lever: List[str] = Field(default_factory=list)
    workday: List[WorkdaySource] = Field(default_factory=list)


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


def load_webhook_defaults(path: Path) -> dict[str, Optional[str]]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return {
        "general": _clean(data.get("general")),
        "software": _clean(data.get("software")),
        "data": _clean(data.get("data")),
    }


def load_settings(config_path: Path, webhook_config: Path | None = None) -> Settings:
    webhook = _clean(os.getenv("DISCORD_WEBHOOK_URL"))
    webhook_software = _clean(os.getenv("DISCORD_WEBHOOK_URL_SOFTWARE"))
    webhook_data = _clean(os.getenv("DISCORD_WEBHOOK_URL_DATA"))
    if webhook_config is None:
        webhook_config = Path("config/webhooks.yaml")
    defaults = load_webhook_defaults(webhook_config)
    webhook = webhook or defaults.get("general")
    webhook_software = webhook_software or defaults.get("software")
    webhook_data = webhook_data or defaults.get("data")
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
