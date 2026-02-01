from __future__ import annotations

from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater


def build_updater() -> RatesUpdater:
    # собирает конфиг и клиентов, возвращает готовый RatesUpdater
    config = ParserConfig.from_env()
    clients = [CoinGeckoClient(config), ExchangeRateApiClient(config)]
    return RatesUpdater(config=config, clients=clients)
