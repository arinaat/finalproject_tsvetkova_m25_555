from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_utc_iso() -> str:
    # Текущее время UTC в ISO-формате без микросекунд
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json_safe(path: Path, default: Any) -> Any:
    # Читает JSON : если файла нет — default; если JSON битый — ValueError
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Файл данных повреждён: {path}") from e
    except OSError as e:
        raise ValueError(f"Не удалось прочитать файл данных: {path}") from e


def atomic_write_json(path: Path, obj: Any) -> None:
    #  пишем во временный файл и переименовываем
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def load_rates_cache(path: Path) -> dict[str, Any]:
    # Загрузка кэша
    return read_json_safe(path, default={"pairs": {}, "last_refresh": None})


def save_rates_cache(path: Path, cache_obj: dict[str, Any]) -> None:
    # Сохранение кэша
    atomic_write_json(path, cache_obj)


def load_history(path: Path) -> list[dict[str, Any]]:
    # Загрузка истории exchange_rates.json
    return read_json_safe(path, default=[])


def append_history(path: Path, records: list[dict[str, Any]]) -> None:
    # Добавляет записи в историю
    if not records:
        return
    items = load_history(path)
    if not isinstance(items, list):
        items = []
    items.extend(records)
    atomic_write_json(path, items)


def make_history_record(
    from_currency: str,
    to_currency: str,
    rate: float,
    source: str,
    meta: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    # Формирует одну запись истории по ожидаемому формату
    ts = timestamp or now_utc_iso()
    return {
        "id": f"{from_currency}_{to_currency}_{ts}",
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": float(rate),
        "timestamp": ts,
        "source": source,
        "meta": meta or {},
    }
