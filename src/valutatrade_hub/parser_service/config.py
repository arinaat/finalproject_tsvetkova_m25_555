from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from valutatrade_hub.core.utils import data_file


@dataclass(frozen=True)
class ParserConfig:
    # Конфиг сервиса парсинга: ключи, URL, валюты, пути к файлам, таймауты

    # Ключ API
    exchangerate_api_key: str | None

    # URL внешних сервисов
    coingecko_url: str
    exchangerate_url: str  # базовый префикс, ключ вставим в клиенте

    # Валюты
    base_fiat_currency: str
    fiat_currencies: tuple[str, ...]
    crypto_currencies: tuple[str, ...]
    crypto_id_map: dict[str, str]

    # Файлы хранения
    rates_file: Path
    history_file: Path

    # Сеть
    request_timeout: int

    @classmethod
    def from_env(cls) -> "ParserConfig":
        """Собирает конфиг из переменных окружения и дефолтов."""
        exchangerate_api_key = os.getenv("EXCHANGERATE_API_KEY")

        # Наборы валют для отслеживания
        fiat = ("EUR", "GBP", "RUB")
        crypto = ("BTC", "ETH", "SOL")

        crypto_id_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}

        return cls(
            exchangerate_api_key=exchangerate_api_key,
            coingecko_url="https://api.coingecko.com/api/v3/simple/price",
            exchangerate_url="https://v6.exchangerate-api.com/v6",
            base_fiat_currency="USD",
            fiat_currencies=fiat,
            crypto_currencies=crypto,
            crypto_id_map=crypto_id_map,
            rates_file=data_file("rates.json"),
            history_file=data_file("exchange_rates.json"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "10")),
        )
