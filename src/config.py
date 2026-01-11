"""Configuration management for arxiv-zotero-obsidian."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ArxivConfig:
    """arXiv API configuration."""
    delay_seconds: float = 3.0
    default_max_results: int = 10
    download_dir: str = "./downloads"


@dataclass
class ZoteroConfig:
    """Zotero API configuration."""
    library_id: str = ""
    library_type: str = "user"
    api_key: str = ""
    default_collection: str = "arXiv Papers"


@dataclass
class ObsidianConfig:
    """Obsidian vault configuration."""
    vault_path: str = ""
    papers_folder: str = "Papers"


@dataclass
class Config:
    """Main configuration container."""
    arxiv: ArxivConfig = field(default_factory=ArxivConfig)
    zotero: ZoteroConfig = field(default_factory=ZoteroConfig)
    obsidian: ObsidianConfig = field(default_factory=ObsidianConfig)


def _resolve_env_vars(value: str) -> str:
    """Resolve environment variable references like ${VAR_NAME}."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.environ.get(env_var, "")
    return value


def _get_config_path() -> Path:
    """Get the configuration file path."""
    # Check environment variable first
    if env_path := os.environ.get("ARXIV_ZOTERO_CONFIG"):
        return Path(env_path)

    # Check common locations
    locations = [
        Path.cwd() / "config" / "config.json",
        Path.home() / ".config" / "arxiv-zotero-obsidian" / "config.json",
    ]

    for loc in locations:
        if loc.exists():
            return loc

    # Return default location (may not exist)
    return locations[0]


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from JSON file and environment variables.

    Args:
        config_path: Optional path to config file. If not provided,
                     searches in default locations.

    Returns:
        Config object with all settings loaded.
    """
    # Load .env file if it exists
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        _load_dotenv(env_file)

    # Determine config file path
    path = Path(config_path) if config_path else _get_config_path()

    config_data: dict = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            config_data = json.load(f)

    # Build config objects
    arxiv_data = config_data.get("arxiv", {})
    zotero_data = config_data.get("zotero", {})
    obsidian_data = config_data.get("obsidian", {})

    # Resolve environment variables in zotero config
    if "api_key" in zotero_data:
        zotero_data["api_key"] = _resolve_env_vars(zotero_data["api_key"])

    # Override with environment variables if set
    if env_key := os.environ.get("ZOTERO_API_KEY"):
        zotero_data["api_key"] = env_key

    if env_vault := os.environ.get("OBSIDIAN_VAULT_PATH"):
        obsidian_data["vault_path"] = env_vault

    return Config(
        arxiv=ArxivConfig(**arxiv_data) if arxiv_data else ArxivConfig(),
        zotero=ZoteroConfig(**zotero_data) if zotero_data else ZoteroConfig(),
        obsidian=ObsidianConfig(**obsidian_data) if obsidian_data else ObsidianConfig(),
    )


def _load_dotenv(path: Path) -> None:
    """Simple .env file loader."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value


def save_config(config: Config, config_path: Optional[str] = None) -> Path:
    """Save configuration to JSON file.

    Args:
        config: Config object to save.
        config_path: Optional path. If not provided, uses default location.

    Returns:
        Path where config was saved.
    """
    path = Path(config_path) if config_path else _get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "arxiv": {
            "delay_seconds": config.arxiv.delay_seconds,
            "default_max_results": config.arxiv.default_max_results,
            "download_dir": config.arxiv.download_dir,
        },
        "zotero": {
            "library_id": config.zotero.library_id,
            "library_type": config.zotero.library_type,
            "api_key": "${ZOTERO_API_KEY}",  # Don't save actual key
            "default_collection": config.zotero.default_collection,
        },
        "obsidian": {
            "vault_path": config.obsidian.vault_path,
            "papers_folder": config.obsidian.papers_folder,
        },
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path
