from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from valutatrade_hub.parser_service.api_clients import (
    ApiRequestError,
    BaseApiClient,
    FetchResult,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import (
    append_history,
    make_history_record,
    now_utc_iso,
    save_rates_cache,
)

logger = logging.getLogger("parser_service")


def _utc_now() -> str:
    # Время старта/финиша обновления в ISO UTC
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RatesUpdater:
    # Координатор обновления курсов: опрос источников + запись кэша и истории

    def __init__(self, config: ParserConfig, clients: list[BaseApiClient]) -> None:
        self.config = config
        self.clients = clients

    def run_update(self, source: str | None = None) -> dict[str, Any]:
        # Обновляет кэш rates.json и пишет историю в exchange_rates.json

        started_at = _utc_now()
        logger.info("Старт обновления курсов...")

        combined_pairs: dict[str, dict[str, Any]] = {}
        history_records: list[dict[str, Any]] = []
        errors: list[str] = []

        for client in self.clients:
            if source:
                s = source.strip().lower()
                if s == "coingecko" and client.source_name != "CoinGecko":
                    continue
                if s == "exchangerate" and client.source_name != "ExchangeRate-API":
                    continue

            try:
                result: FetchResult = client.fetch_rates()
                logger.info(
                    "Источник '%s': получено курсов: %s",
                    result.source,
                    len(result.pairs_usd_per_unit),
                )
            except ApiRequestError as e:
                msg = f"Источник '{client.source_name}': ошибка запроса: {e}"
                logger.error(msg)
                errors.append(msg)
                continue

            updated_at = now_utc_iso()
            for pair, rate in result.pairs_usd_per_unit.items():
                # В кэше храним последнее значение по паре
                combined_pairs[pair] = {
                    "rate": float(rate),
                    "updated_at": updated_at,
                    "source": result.source,
                }

                # В историю пишем все полученные значения
                from_ccy, to_ccy = pair.split("_", 1)
                history_records.append(
                    make_history_record(
                        from_currency=from_ccy,
                        to_currency=to_ccy,
                        rate=float(rate),
                        source=result.source,
                        meta=result.meta,
                        timestamp=updated_at,
                    )
                )

        last_refresh = now_utc_iso()
        cache_obj = {"pairs": combined_pairs, "last_refresh": last_refresh}

        # Даже если один источник упал — сохраним то, что собрали
        save_rates_cache(self.config.rates_file, cache_obj)
        append_history(self.config.history_file, history_records)

        logger.info(
            "Кэш записан: %s пар(ы) -> %s", len(combined_pairs), self.config.rates_file
        )
        if errors:
            logger.info("Обновление завершено с ошибками: %s", len(errors))
        else:
            logger.info("Обновление завершено успешно")

        return {
            "started_at": started_at,
            "last_refresh": last_refresh,
            "updated_pairs": len(combined_pairs),
            "history_records": len(history_records),
            "errors": errors,
        }
