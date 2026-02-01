from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import requests

from valutatrade_hub.parser_service.config import ParserConfig


class ApiRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchResult:
    pairs_usd_per_unit: dict[str, float]
    source: str
    meta: dict[str, Any]


class BaseApiClient(ABC):
    def __init__(self, config: ParserConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def fetch_rates(self) -> FetchResult: ...


class CoinGeckoClient(BaseApiClient):
    @property
    def source_name(self) -> str:
        return "CoinGecko"

    def fetch_rates(self) -> FetchResult:
        # CoinGecko дает цену в USD за 1 монету -> это наш стандарт "USD per unit"
        ids = []
        for c in self.config.crypto_currencies:
            coin_id = self.config.crypto_id_map.get(c)
            if coin_id:
                ids.append(coin_id)

        if not ids:
            return FetchResult(
                pairs_usd_per_unit={},
                source=self.source_name,
                meta={"note": "no crypto ids"},
            )

        params = {"ids": ",".join(ids), "vs_currencies": "usd"}

        t0 = perf_counter()
        try:
            resp = requests.get(
                self.config.coingecko_url,
                params=params,
                timeout=self.config.request_timeout,
            )
        except requests.exceptions.Timeout as e:
            raise ApiRequestError("CoinGecko: timeout") from e
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko: network error: {e}") from e
        dt_ms = int((perf_counter() - t0) * 1000)

        if resp.status_code == 429:
            raise ApiRequestError("CoinGecko: 429 Too Many Requests (лимит запросов)")
        if resp.status_code >= 400:
            raise ApiRequestError(f"CoinGecko: HTTP {resp.status_code}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiRequestError("CoinGecko: invalid JSON") from e

        # data: {"bitcoin": {"usd": 59337.21}, ...}
        out: dict[str, float] = {}
        inv_map = {v: k for k, v in self.config.crypto_id_map.items()}
        for coin_id, obj in data.items():
            ticker = inv_map.get(coin_id)
            if not ticker:
                continue
            usd_val = obj.get("usd")
            if isinstance(usd_val, (int, float)) and usd_val > 0:
                out[f"{ticker}_USD"] = float(usd_val)

        return FetchResult(
            pairs_usd_per_unit=out,
            source=self.source_name,
            meta={
                "status_code": resp.status_code,
                "request_ms": dt_ms,
                "count": len(out),
            },
        )


class ExchangeRateApiClient(BaseApiClient):
    @property
    def source_name(self) -> str:
        return "ExchangeRate-API"

    def fetch_rates(self) -> FetchResult:
        key = self.config.exchangerate_api_key
        if not key:
            raise ApiRequestError(
                "ExchangeRate-API: отсутствует EXCHANGERATE_API_KEY в env"
            )

        url = (
    f"{self.config.exchangerate_url}/{key}/latest/"
    f"{self.config.base_fiat_currency}"
)


        t0 = perf_counter()
        try:
            resp = requests.get(url, timeout=self.config.request_timeout)
        except requests.exceptions.Timeout as e:
            raise ApiRequestError("ExchangeRate-API: timeout") from e
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API: network error: {e}") from e
        dt_ms = int((perf_counter() - t0) * 1000)

        if resp.status_code == 401:
            raise ApiRequestError(
                "ExchangeRate-API: 401 Unauthorized (неверный API-ключ)"
            )
        if resp.status_code == 429:
            raise ApiRequestError(
                "ExchangeRate-API: 429 Too Many Requests (лимит запросов)"
            )
        if resp.status_code >= 400:
            raise ApiRequestError(f"ExchangeRate-API: HTTP {resp.status_code}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiRequestError("ExchangeRate-API: invalid JSON") from e

        # ожидаем: {"result":"success","base_code":"USD","time_last_update_utc":"..."}
# и "rates": {...}

        if data.get("result") != "success":
            err_type = data.get("error-type")
            raise ApiRequestError(f"ExchangeRate-API: result != success ({err_type})")

        rates = data.get("rates", {}) or data.get("conversion_rates", {})
        if not isinstance(rates, dict):
            raise ApiRequestError("ExchangeRate-API: invalid rates format")

        out: dict[str, float] = {}
        for ccy in self.config.fiat_currencies:
            v = rates.get(ccy)
            if isinstance(v, (int, float)) and v > 0:
                out[f"{ccy}_USD"] = 1.0 / float(v)

        return FetchResult(
            pairs_usd_per_unit=out,
            source=self.source_name,
            meta={
                "status_code": resp.status_code,
                "request_ms": dt_ms,
                "time_last_update_utc": data.get("time_last_update_utc"),
                "count": len(out),
            },
        )
