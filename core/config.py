"""
Config Service - Manages application settings via JSON file
"""
import json
import os
from pathlib import Path


class ConfigService:
    CONFIG_FILE = "nima_clothes_config.json"

    DEFAULT_CONFIG = {
        "db_connection_string": "sqlite:///nima_clothes.db",
        "app_language": "fa",
        "theme": "light"
    }

    def __init__(self):
        self.config_path = Path(self.CONFIG_FILE)
        self._config = self._load()

    def _load(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return self.DEFAULT_CONFIG.copy()

    def save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @property
    def db_connection_string(self) -> str:
        return self._config.get("db_connection_string", self.DEFAULT_CONFIG["db_connection_string"])

    @db_connection_string.setter
    def db_connection_string(self, value: str):
        self._config["db_connection_string"] = value.strip()
        self.save()

    def get_all(self) -> dict:
        return self._config.copy()