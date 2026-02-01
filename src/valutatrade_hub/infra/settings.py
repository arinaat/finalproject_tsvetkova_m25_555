#Singleton SettingsLoader

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    # Пути к данным
    data_dir: Path
    users_json: Path
    portfolios_json: Path
    rates_json: Path
    session_json: Path

    # Кеш курсов
    rates_ttl_seconds: int

    # Базовая валюта по умолчанию
    default_base_currency: str

    # Логи
    logs_dir: Path
    actions_log: Path
    log_level: str


class SettingsLoader:
    #загружает и кеширует настройки

    _instance: "SettingsLoader | None" = None

    def __new__(cls) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = None
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        #Получить значение настройки по ключу
        s = self.load()
        return getattr(s, key, default)

    def load(self) -> Settings:
        #Загрузить настройки, дальше отдаём кеш
        if self._settings is not None:
            return self._settings

        root = Path(".").resolve()
        data_dir = root / "data"
        logs_dir = root / "logs"

        settings = Settings(
            data_dir=data_dir,
            users_json=data_dir / "users.json",
            portfolios_json=data_dir / "portfolios.json",
            rates_json=data_dir / "rates.json",
            session_json=data_dir / "session.json",
            rates_ttl_seconds=300,
            default_base_currency="USD",
            logs_dir=logs_dir,
            actions_log=logs_dir / "actions.log",
            log_level="INFO",
        )
        self._settings = settings
        return settings

    def reload(self) -> Settings:
        # Сброс кеша и повторная загрузка
        self._settings = None
        return self.load()
