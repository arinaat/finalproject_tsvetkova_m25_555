# Бизнес-логика

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from valutatrade_hub.core.utils import (
    load_rates,
    normalize_currency_code,
    save_rates,
)

CACHE_TTL_SECONDS = 300  # 5 минут


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        dt = datetime.fromisoformat(str(value))
        # Если строка без таймзоны — считаем, что это UTC
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except ValueError:
        return None


def _is_fresh(last_refresh: Any, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    dt = _parse_iso_dt(last_refresh)
    if dt is None:
        return False
    return _now_utc() - dt <= timedelta(seconds=ttl_seconds)


def _refresh_rates_stub() -> dict[str, Any]:
    now = _now_utc().replace(microsecond=0).isoformat()

    # Условные курсы относительно USD
    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "RUB": 98.38,
        "BTC": 0.00001685,
        "ETH": 0.000268,
    }

    return {"source": "LocalStub", "last_refresh": now, "base": "USD", "rates": rates}


def ensure_rates_fresh() -> dict[str, Any]:
    #Возвращает актуальные курсы. Если кэш устарел — обновляет и сохраняет
    cache = load_rates()
    if not _is_fresh(cache.get("last_refresh")) or "rates" not in cache:
        cache = _refresh_rates_stub()
        save_rates(cache)
    return cache


def get_rate(from_currency: str, to_currency: str) -> dict[str, Any]:
    #Возвращает курс и (источник/время обновления).
    frm = normalize_currency_code(from_currency)
    to = normalize_currency_code(to_currency)

    data = ensure_rates_fresh()
    base = normalize_currency_code(data.get("base", "USD"))
    rates: dict[str, float] = data.get("rates", {})

    if frm == to:
        rate = 1.0
    else:
        if base not in rates:
            rates[base] = 1.0

        if frm not in rates or to not in rates:
            raise ValueError("Курс для указанной валюты недоступен.")

        def to_usd(x: str) -> float:
            if x == base:
                return 1.0
            return 1.0 / float(rates[x])

        def from_usd(x: str) -> float:
            if x == base:
                return 1.0
            return float(rates[x])

        rate = to_usd(frm) * from_usd(to)

    return {
        "from": frm,
        "to": to,
        "rate": float(rate),
        "source": data.get("source"),
        "last_refresh": data.get("last_refresh"),
        "base": base,
    }
